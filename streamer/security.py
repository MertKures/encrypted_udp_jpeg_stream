import logging
from cryptography.fernet import Fernet, InvalidToken

class Encryptor:
    """
    A wrapper for the Fernet symmetric encryption scheme.
    
    Fernet is ideal here because it provides Authenticated Encryption (AEAD).
    This means it guarantees both the confidentiality (encryption) and the
    integrity/authenticity of the data. If a packet is corrupted or tampered with
    in transit, the decryption will fail. This directly satisfies the requirement
    to drop incorrect messages without needing a separate checksum.
    """
    def __init__(self, key: bytes):
        """
        Initializes the encryptor with a secret key.
        
        Args:
            key (bytes): A URL-safe base64-encoded 32-byte key.
        """
        self.fernet = Fernet(key)

    @classmethod
    def from_file(cls, key_path: str):
        """
        Loads the encryption key from a file and creates an Encryptor instance.
        """
        try:
            with open(key_path, "rb") as key_file:
                key = key_file.read()
            return cls(key)
        except FileNotFoundError:
            logging.error(f"Encryption key file not found at '{key_path}'.")
            logging.error("Generate a key with: `generate-stream-key`")
            raise

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts data."""
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes | None:
        """
        Decrypts a token.
        
        Returns:
            The original data, or None if the token is invalid (corrupted/tampered).
        """
        try:
            return self.fernet.decrypt(token)
        except InvalidToken:
            logging.warning("Received a corrupted or invalid data packet. Dropping it.")
            return None

def generate_key_and_save():
    """
    Generates a new Fernet key and saves it to 'secret.key'.
    This function is exposed as the `generate-stream-key` command-line script.
    """
    key = Fernet.generate_key()
    key_path = "secret.key"
    with open(key_path, "wb") as key_file:
        key_file.write(key)
    logging.info(f"New encryption key generated and saved to '{key_path}'.")
    print(f"Key saved to {key_path}. Share this file securely with the receiver.")


