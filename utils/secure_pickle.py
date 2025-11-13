"""
Secure Pickle Module
Safe loading and saving of pickle files with security restrictions
"""

import pickle
import hmac
import hashlib
import logging
from pathlib import Path
from typing import Any, Set, Optional
import io

logger = logging.getLogger(__name__)


class RestrictedUnpickler(pickle.Unpickler):
    """
    Restricted unpickler that only allows specific safe classes

    This helps prevent arbitrary code execution from malicious pickle files
    """

    # Whitelist of allowed modules and classes
    SAFE_MODULES = {
        'numpy', 'numpy.core', 'numpy.core.multiarray', 'numpy.core.numeric',
        'pandas', 'pandas.core', 'pandas.core.frame', 'pandas.core.series',
        'sklearn', 'sklearn.ensemble', 'sklearn.svm', 'sklearn.cluster',
        'sklearn.preprocessing', 'sklearn.tree', 'sklearn.neighbors',
        'scipy', 'scipy.sparse',
        'models', 'models.unsupervised', 'models.supervised',
        'features', 'features.preprocessor',
        'builtins', '_codecs', 'collections',
    }

    # Additional safe builtin types
    SAFE_BUILTINS = {
        'list', 'dict', 'set', 'tuple', 'frozenset',
        'int', 'float', 'str', 'bool', 'bytes',
        'range', 'slice', 'complex', 'type', 'object'
    }

    def find_class(self, module: str, name: str):
        """
        Override find_class to restrict which classes can be unpickled

        Args:
            module: Module name
            name: Class name

        Returns:
            Class object if allowed

        Raises:
            pickle.UnpicklingError: If class is not in whitelist
        """
        # Check if module is in whitelist
        module_base = module.split('.')[0]

        if module == 'builtins' and name in self.SAFE_BUILTINS:
            return super().find_class(module, name)

        if module_base in self.SAFE_MODULES or module in self.SAFE_MODULES:
            return super().find_class(module, name)

        # Log and reject
        logger.warning(f"Rejected unpickling of class: {module}.{name}")
        raise pickle.UnpicklingError(
            f"Unsafe class detected: {module}.{name}. "
            "This may be a malicious pickle file."
        )


class SecurePickle:
    """Secure pickle operations with HMAC verification"""

    def __init__(self, secret_key: Optional[bytes] = None):
        """
        Initialize secure pickle handler

        Args:
            secret_key: Secret key for HMAC (if None, HMAC is disabled)
        """
        self.secret_key = secret_key
        self.use_hmac = secret_key is not None

        if self.use_hmac:
            logger.info("SecurePickle initialized with HMAC verification enabled")
        else:
            logger.info("SecurePickle initialized without HMAC verification")

    def _compute_hmac(self, data: bytes) -> bytes:
        """
        Compute HMAC for data

        Args:
            data: Data to compute HMAC for

        Returns:
            HMAC digest
        """
        if not self.secret_key:
            raise ValueError("HMAC key not set")

        return hmac.new(self.secret_key, data, hashlib.sha256).digest()

    def save(self, obj: Any, file_path: str, protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        """
        Securely save object to pickle file with optional HMAC

        Args:
            obj: Object to pickle
            file_path: Output file path
            protocol: Pickle protocol version
        """
        try:
            # Serialize object
            data = pickle.dumps(obj, protocol=protocol)

            # Write to file
            with open(file_path, 'wb') as f:
                if self.use_hmac:
                    # Write HMAC first, then data
                    mac = self._compute_hmac(data)
                    f.write(len(mac).to_bytes(4, 'big'))  # HMAC length
                    f.write(mac)  # HMAC
                    f.write(data)  # Pickled data
                else:
                    # Write data only
                    f.write(data)

            logger.info(f"Securely saved pickle to: {file_path}")

        except Exception as e:
            logger.error(f"Error saving pickle file: {e}")
            raise

    def load(self, file_path: str, restricted: bool = True) -> Any:
        """
        Securely load object from pickle file with optional HMAC verification

        Args:
            file_path: Input file path
            restricted: Use restricted unpickler (recommended)

        Returns:
            Unpickled object

        Raises:
            ValueError: If HMAC verification fails
            pickle.UnpicklingError: If restricted class detected
        """
        try:
            # Validate file exists
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Pickle file not found: {file_path}")

            # Check file size (basic sanity check)
            file_size = path.stat().st_size
            if file_size == 0:
                raise ValueError(f"Pickle file is empty: {file_path}")

            if file_size > 1024 * 1024 * 1024:  # 1GB limit
                logger.warning(f"Pickle file is very large ({file_size / (1024*1024):.1f} MB): {file_path}")

            # Read file
            with open(file_path, 'rb') as f:
                if self.use_hmac:
                    # Read and verify HMAC
                    mac_len_bytes = f.read(4)
                    if len(mac_len_bytes) != 4:
                        raise ValueError("Invalid pickle file format: missing HMAC length")

                    mac_len = int.from_bytes(mac_len_bytes, 'big')
                    stored_mac = f.read(mac_len)
                    data = f.read()

                    # Verify HMAC
                    computed_mac = self._compute_hmac(data)
                    if not hmac.compare_digest(stored_mac, computed_mac):
                        raise ValueError(
                            "HMAC verification failed! Pickle file may be corrupted or tampered with."
                        )

                    logger.info(f"HMAC verification passed for: {file_path}")
                else:
                    # Read all data
                    data = f.read()

            # Unpickle with restricted or standard unpickler
            if restricted:
                obj = RestrictedUnpickler(io.BytesIO(data)).load()
                logger.info(f"Securely loaded pickle from: {file_path} (restricted mode)")
            else:
                obj = pickle.loads(data)
                logger.info(f"Loaded pickle from: {file_path} (unrestricted mode)")

            return obj

        except pickle.UnpicklingError as e:
            logger.error(f"Unpickling error - possible malicious file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading pickle file: {e}")
            raise


# Convenience functions
def safe_load(file_path: str, secret_key: Optional[bytes] = None, restricted: bool = True) -> Any:
    """
    Safely load a pickle file with optional HMAC verification

    Args:
        file_path: Path to pickle file
        secret_key: Optional HMAC key for verification
        restricted: Use restricted unpickler (recommended: True)

    Returns:
        Unpickled object

    Example:
        >>> # Load with restricted unpickler (safe)
        >>> model = safe_load('model.pkl', restricted=True)

        >>> # Load with HMAC verification
        >>> model = safe_load('model.pkl', secret_key=b'my_secret', restricted=True)
    """
    sp = SecurePickle(secret_key=secret_key)
    return sp.load(file_path, restricted=restricted)


def safe_save(obj: Any, file_path: str, secret_key: Optional[bytes] = None) -> None:
    """
    Safely save an object to pickle file with optional HMAC

    Args:
        obj: Object to pickle
        file_path: Output file path
        secret_key: Optional HMAC key for signing

    Example:
        >>> # Save without HMAC
        >>> safe_save(model, 'model.pkl')

        >>> # Save with HMAC
        >>> safe_save(model, 'model.pkl', secret_key=b'my_secret')
    """
    sp = SecurePickle(secret_key=secret_key)
    sp.save(obj, file_path)


def add_allowed_module(module: str) -> None:
    """
    Add a module to the whitelist for restricted unpickler

    Args:
        module: Module name to add

    Example:
        >>> add_allowed_module('my_custom_module')
    """
    RestrictedUnpickler.SAFE_MODULES.add(module)
    logger.info(f"Added module to whitelist: {module}")


def get_allowed_modules() -> Set[str]:
    """
    Get the current whitelist of allowed modules

    Returns:
        Set of allowed module names
    """
    return RestrictedUnpickler.SAFE_MODULES.copy()
