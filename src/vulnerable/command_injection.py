import os

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: OS Command Injection (CWE-78) via unsanitized shell input


def ping_host(hostname):
    return os.system("ping -c 1 " + hostname)  # user input passed directly to shell
