import re
from typing import List

# Blocked commands that are too critical to run or always require confirmation
BLOCKED_SHELL_PATTERNS = [
    r"rm\s+-rf\s+/",                      # delete root
    r"rm\s+-rf\s+/\w+",                    # delete high-level directories
    r"dd\s+if=",                           # raw write
    r"mkfs",                               # format disk
    r"mv\s+.*?\s+/\w+",                    # move to system folder
    r"shutdown",
    r"reboot",
    r":\(\)\{\s*:\s*\|\s*:\s*&\s*\};:\s*" # fork bomb
]

# Medium risk shells that need confirmation if risk_policy is confirm_medium_high or higher
MEDIUM_SHELL_PATTERNS = [
    r"sudo\s+",                            # superuser
    r"apt-get\s+",                         # package management
    r"apt\s+",                             # package management
    r"dpkg\s+",                            # package management
    r"chmod\s+",                           # permission changes
    r"chown\s+",                           # ownership changes
    r"curl\s+.*?\|\s*bash",               # pipe to bash
    r"wget\s+.*?\|\s*bash",               # pipe to bash
    r"curl\s+.*?\|\s*sh",                 # pipe to sh
    r"wget\s+.*?\|\s*sh",                 # pipe to sh
    r"git\s+push\s+.*?-f",                 # force push
    r"git\s+push\s+.*?--force",            # force push
    r"rm\s+",                              # file deletions
    r"mv\s+"                               # moves
]

# UI keywords that suggest sensitive operations
SENSITIVE_UI_KEYWORDS = [
    "password", "passwort", "pin", "cvv", "credit card", "kreditkarte", 
    "bank", "paypal", "checkout", "buy", "kaufen", "order", "bestellen",
    "bezahlen", "payment", "einkaufswagen", "cart"
]

# Domain configurations
BLOCKED_DOMAINS = [
    r"amazon\.", r"ebay\.", r"paypal\.", r"stripe\.", r"bank", r"login", r"signin"
]
