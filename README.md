# RedaForce

> **A browser-driven authentication testing framework for Dahua web interfaces, built at age 15 after discovering the limitations of traditional tools such as Hydra during home laboratory security research.**

## Overview

RedaForce is a Python-based authentication testing framework that automates login attempts against Dahua web interfaces through a real Firefox browser using Selenium.

The project was created after discovering that conventional password auditing tools, such as Hydra, were ineffective against Dahua's JavaScript-driven authentication interface. Instead of relying on raw HTTP requests, RedaForce interacts with the login page exactly as a real user would, making it compatible with the interface variants encountered during testing.

The current release (v9.2) is the result of several months of experimentation and five major iterations.

---

# Why I Built RedaForce

At the age of 15, I was building a home cybersecurity laboratory to better understand wireless and network security.

While studying common penetration testing workflows, I discovered that Hydra could not reliably authenticate against Dahua's JavaScript-based login interface. Although it worked well against traditional web forms, it was not suitable for the DVR interfaces I was researching.

Rather than modifying an existing project, I decided to design my own solution from scratch.

What began as a simple automation script gradually evolved into RedaForce—a browser-driven authentication framework capable of adapting to multiple Dahua login interface variants while providing a streamlined workflow for authorized laboratory assessments.

The project became much more than writing Python code. It involved reverse engineering login behavior, studying different firmware interfaces, improving reliability across versions, and refining the user experience through multiple complete rewrites.

---

# Features

* Browser-driven authentication using Selenium and Firefox
* Automatic detection of multiple Dahua login interface variants
* Interactive command-line interface
* Username input as:

  * default (`admin`)
  * single username
  * space-separated usernames
  * UTF-8 text file
* Password input as:

  * single password
  * space-separated passwords
  * UTF-8 wordlist
* Automatic path autocompletion for wordlists on Linux
* Progress statistics
* ETA estimation
* Automatic result logging
* Automatic browser recovery
* Automatic MAC address renewal between batches of attempts for uninterrupted laboratory testing
* Clean terminal interface with colored output

---

# Laboratory Workflow

RedaForce was designed to fit into a complete laboratory security assessment workflow.

Typical workflow:

1. Connect to an authorized laboratory network.
2. Discover hosts using Nmap.
3. Identify Dahua devices exposing the web interface.
4. Verify the login page.
5. Launch RedaForce against the detected target.
6. Evaluate authentication strength.
7. Improve security based on the assessment findings.

This workflow reflects how the tool was designed and tested during home laboratory research.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/REDA-MAH/RedaForce.git
cd RedaForce
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Ensure the following are available:

* Python 3
* Firefox
* GeckoDriver
* Selenium
* macchanger
* NetworkManager (`nmcli`)

The project is currently intended for Kali Linux and similar Linux distributions. Some functionality (such as MAC renewal and terminal path completion) depends on Linux-specific utilities.

---

# Usage

Run:

```bash
python3 redaforce.py
```

The program will request:

* Target IP address
* Username(s)
* Password(s)

Usernames may be:

* press Enter to use `admin`
* a single username
* multiple usernames separated by spaces
* a UTF-8 text file

Passwords may be:

* a single password
* multiple passwords separated by spaces
* a UTF-8 wordlist

---

# Compatibility

RedaForce has been tested against Dahua DVR web interfaces encountered during laboratory research.

During development, two primary login interface variants were identified. The application automatically detects the interface and selects the appropriate interaction logic.

Compatibility with additional firmware versions has not yet been extensively evaluated.

---

# Case Study

After completing RedaForce, I had the opportunity to use it during an authorized security assessment requested by the principal of a local school.

The objective was to evaluate the security of the school's network and surveillance infrastructure. During the assessment, I identified weak authentication protecting the surveillance system and demonstrated the associated risk within the authorized testing scope.

Based on the findings, I recommended replacing the weak credentials with a significantly stronger password and separating the surveillance system from the general wireless network through improved network segmentation.

These recommendations were implemented, improving the overall security posture of the school's surveillance infrastructure.

Seeing software that I had built from scratch contribute to a real security improvement was one of the most rewarding parts of this project.

---

# Roadmap

## Completed

* Browser-driven authentication
* Adaptive interface detection
* Interactive CLI
* Automatic MAC renewal
* Progress tracking
* ETA calculation
* Result logging

## Planned

* Automatic Nmap integration
* Automatic Dahua device discovery
* Support for additional router web interfaces (Orange, IAM, TP-Link, and others)
* Configuration file support
* Improved modular architecture
* Docker support
* Expanded device compatibility

---

# Limitations

Current limitations include:

* Linux-focused implementation
* Firefox/GeckoDriver dependency
* Designed specifically around Dahua authentication workflows
* Tested primarily on DVR interfaces
* Not intended for high-speed parallel password auditing

---

# Screenshots

Screenshots are available in the `screenshots/` directory. (not available yet)

---

# Disclaimer

RedaForce is intended solely for authorized security testing, defensive research, laboratory experimentation, and educational purposes.

Always obtain permission before testing systems or networks that you do not own or explicitly administer.

---

# Author

**REDA-MAH**

This project represents my exploration of browser automation, network security, reverse engineering of web authentication workflows, and Python software engineering. It was developed as a personal research project while I was 15 years old and continues to evolve as I expand its capabilities.
