import os

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: Path Traversal (CWE-22) via unsanitized filename

MEDIA_DIR = "static/mars_photos"


def load_photo(filename):
    path = os.path.join(MEDIA_DIR, filename)  # no validation, "../../etc/passwd" escapes MEDIA_DIR
    with open(path, "rb") as f:
        return f.read()
