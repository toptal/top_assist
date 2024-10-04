from cryptography.fernet import Fernet


class Cypher:
    """Base class for encrypting and decrypting values using Fernet symmetric encryption."""

    def __init__(self, secret_key: str) -> None:
        """Initialize the Cypher with a secret key.

        Args:
            secret_key: The secret key to use for encryption and decryption in base64 format (32 bytes, 44 characters).
        """
        self.fernet = Fernet(secret_key.encode())

    def encrypt(self, original_value: str) -> str:
        encrypted_token = self.fernet.encrypt(original_value.encode())
        return encrypted_token.decode()

    def decrypt(self, encrypted_value: str) -> str:
        decrypted_token = self.fernet.decrypt(encrypted_value.encode())
        return decrypted_token.decode()
