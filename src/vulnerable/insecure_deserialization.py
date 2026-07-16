import pickle

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: Insecure Deserialization (CWE-502) via untrusted pickle data


def load_cached_telemetry(raw_bytes):
    return pickle.loads(raw_bytes)  # deserializes untrusted data, allows arbitrary code execution
