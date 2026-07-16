import hashlib

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: Use of a Broken Cryptographic Algorithm (CWE-327) for password storage


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is not suitable for password hashing
