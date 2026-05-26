# -*- coding: utf-8 -*-
"""
Cryptography research module: RSA, elliptic curve, hashes, post-quantum experiments.
Lightweight; uses standard library + optional cryptography package.
"""
import hashlib
from typing import Optional, Tuple

# RSA and ECC require cryptography or similar; we use stdlib for basic experiments
# and optional crypto for real RSA/ECC.


def hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_sha256_int(data: bytes) -> int:
    return int(hashlib.sha256(data).hexdigest(), 16)


def _ensure_crypto() -> bool:
    try:
        import cryptography
        return True
    except ImportError:
        return False


def rsa_generate_keypair(bits: int = 2048) -> Optional[Tuple[str, str]]:
    """Generate RSA key pair (PEM). Returns (public_pem, private_pem) or None if crypto not installed."""
    if not _ensure_crypto():
        return None
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        key = rsa.generate_private_key(public_exponent=65537, key_size=bits, backend=default_backend())
        priv_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        return (pub_pem, priv_pem)
    except Exception:
        return None


def rsa_encrypt(public_pem: str, plaintext: bytes) -> Optional[bytes]:
    """RSA encrypt with public key. For larger data use hybrid encryption in production."""
    if not _ensure_crypto():
        return None
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        pub = serialization.load_pem_public_key(public_pem.encode(), backend=default_backend())
        return pub.encrypt(plaintext, padding.PKCS1v15())
    except Exception:
        return None


def rsa_decrypt(private_pem: str, ciphertext: bytes) -> Optional[bytes]:
    if not _ensure_crypto():
        return None
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        priv = serialization.load_pem_private_key(private_pem.encode(), password=None, backend=default_backend())
        return priv.decrypt(ciphertext, padding.PKCS1v15())
    except Exception:
        return None


def ecc_generate_keypair() -> Optional[Tuple[str, str]]:
    """Generate ECDSA P-256 key pair. Returns (public_pem, private_pem) or None."""
    if not _ensure_crypto():
        return None
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        priv_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        return (pub_pem, priv_pem)
    except Exception:
        return None


def ecc_sign(private_key_pem: str, message: bytes) -> Optional[bytes]:
    """ECDSA sign message. Requires cryptography."""
    if not _ensure_crypto():
        return None
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend
        priv = serialization.load_pem_private_key(private_key_pem.encode(), password=None, backend=default_backend())
        sig = priv.sign(message, ec.ECDSA(ec.SHA256()))
        return sig
    except Exception:
        return None


def ecc_verify(public_key_pem: str, message: bytes, signature: bytes) -> bool:
    if not _ensure_crypto():
        return False
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend
        pub = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
        pub.verify(signature, message, ec.ECDSA(ec.SHA256()))
        return True
    except Exception:
        return False


def post_quantum_hash_based(message: bytes) -> str:
    """Hash-based commitment (experimental post-quantum safe building block)."""
    try:
        h = hashlib.sha3_256(message).hexdigest()
    except AttributeError:
        h = hashlib.sha256(message).hexdigest()
    return h


class CryptoEngine:
    """
    Cryptography research engine: RSA, ECC, hashes, experiments.
    """

    def __init__(self) -> None:
        self._crypto_available = _ensure_crypto()

    @property
    def has_cryptography(self) -> bool:
        return self._crypto_available

    def sha256(self, data: bytes) -> str:
        return hash_sha256(data)

    def rsa_keypair(self, bits: int = 2048) -> Optional[Tuple[str, str]]:
        return rsa_generate_keypair(bits)

    def rsa_encrypt(self, public_pem: str, plaintext: bytes) -> Optional[bytes]:
        return rsa_encrypt(public_pem, plaintext)

    def rsa_decrypt(self, private_pem: str, ciphertext: bytes) -> Optional[bytes]:
        return rsa_decrypt(private_pem, ciphertext)

    def ecc_sign(self, private_pem: str, message: bytes) -> Optional[bytes]:
        return ecc_sign(private_pem, message)

    def ecc_keypair(self) -> Optional[Tuple[str, str]]:
        return ecc_generate_keypair()

    def ecc_verify(self, public_pem: str, message: bytes, signature: bytes) -> bool:
        return ecc_verify(public_pem, message, signature)

    def hash_based_commitment(self, message: bytes) -> str:
        return post_quantum_hash_based(message)
