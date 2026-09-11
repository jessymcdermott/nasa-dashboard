import io
import pickle

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: Insecure Deserialization (CWE-502) via untrusted pickle data


class _RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError("Deserialization of arbitrary classes is not allowed")


def load_cached_telemetry(raw_bytes):
    return _RestrictedUnpickler(io.BytesIO(raw_bytes)).load()
