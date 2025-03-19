#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encryption utilities for RebelSCRIBE.

This module provides functions for data encryption, key management,
secure storage, password hashing, and secure deletion.
"""

import os
import base64
import hashlib
import secrets
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union

# Try to import cryptography libraries, but provide fallbacks if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Logger setup
import logging
logger = logging.getLogger(__name__)


def check_encryption_available() -> bool:
    """
    Check if encryption functionality is available.
    
    Returns:
        bool: True if encryption is available, False otherwise.
    """
    return CRYPTOGRAPHY_AVAILABLE


def generate_key() -> bytes:
    """
    Generate a new encryption key.
    
    Returns:
        bytes: A new encryption key.
    
    Raises:
        RuntimeError: If encryption is not available.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    return Fernet.generate_key()


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Derive an encryption key from a password.
    
    Args:
        password (str): The password to derive the key from.
        salt (bytes, optional): The salt to use for key derivation. If None, a new salt is generated.
    
    Returns:
        Tuple[bytes, bytes]: A tuple containing the derived key and the salt used.
    
    Raises:
        RuntimeError: If encryption is not available.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_data(data: Union[str, bytes], key: bytes) -> bytes:
    """
    Encrypt data using the provided key.
    
    Args:
        data (Union[str, bytes]): The data to encrypt.
        key (bytes): The encryption key.
    
    Returns:
        bytes: The encrypted data.
    
    Raises:
        RuntimeError: If encryption is not available.
        TypeError: If data is not a string or bytes.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise TypeError("Data must be a string or bytes.")
    
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt data using the provided key.
    
    Args:
        encrypted_data (bytes): The encrypted data.
        key (bytes): The encryption key.
    
    Returns:
        bytes: The decrypted data.
    
    Raises:
        RuntimeError: If encryption is not available.
        ValueError: If the key is invalid or the data is corrupted.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    f = Fernet(key)
    return f.decrypt(encrypted_data)


def encrypt_file(file_path: str, key: bytes, output_path: Optional[str] = None) -> str:
    """
    Encrypt a file using the provided key.
    
    Args:
        file_path (str): The path to the file to encrypt.
        key (bytes): The encryption key.
        output_path (str, optional): The path to save the encrypted file. If None, the original file is replaced.
    
    Returns:
        str: The path to the encrypted file.
    
    Raises:
        RuntimeError: If encryption is not available.
        FileNotFoundError: If the file does not exist.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # If no output path is provided, use a temporary file and replace the original
    if output_path is None:
        output_path = file_path + ".encrypted"
        replace_original = True
    else:
        replace_original = False
    
    try:
        # Read the file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Encrypt the data
        encrypted_data = encrypt_data(data, key)
        
        # Write the encrypted data
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Replace the original file if requested
        if replace_original:
            os.replace(output_path, file_path)
            return file_path
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error encrypting file {file_path}: {str(e)}")
        # Clean up the output file if it was created
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def decrypt_file(file_path: str, key: bytes, output_path: Optional[str] = None) -> str:
    """
    Decrypt a file using the provided key.
    
    Args:
        file_path (str): The path to the encrypted file.
        key (bytes): The encryption key.
        output_path (str, optional): The path to save the decrypted file. If None, the original file is replaced.
    
    Returns:
        str: The path to the decrypted file.
    
    Raises:
        RuntimeError: If encryption is not available.
        FileNotFoundError: If the file does not exist.
        ValueError: If the key is invalid or the file is corrupted.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # If no output path is provided, use a temporary file and replace the original
    if output_path is None:
        output_path = file_path + ".decrypted"
        replace_original = True
    else:
        replace_original = False
    
    try:
        # Read the encrypted file
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt the data
        decrypted_data = decrypt_data(encrypted_data, key)
        
        # Write the decrypted data
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        # Replace the original file if requested
        if replace_original:
            os.replace(output_path, file_path)
            return file_path
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error decrypting file {file_path}: {str(e)}")
        # Clean up the output file if it was created
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hash a password using PBKDF2 with SHA-256.
    
    Args:
        password (str): The password to hash.
        salt (bytes, optional): The salt to use for hashing. If None, a new salt is generated.
    
    Returns:
        Tuple[bytes, bytes]: A tuple containing the password hash and the salt used.
    """
    if salt is None:
        salt = os.urandom(16)
    
    # Use PBKDF2 with SHA-256 for password hashing
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,  # Number of iterations
        dklen=32  # Length of the derived key
    )
    
    return key, salt


def verify_password(password: str, password_hash: bytes, salt: bytes) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password (str): The password to verify.
        password_hash (bytes): The hash to verify against.
        salt (bytes): The salt used for hashing.
    
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    # Hash the provided password with the same salt
    key, _ = hash_password(password, salt)
    
    # Compare the hashes using a constant-time comparison
    return secrets.compare_digest(key, password_hash)


def secure_delete_file(file_path: str, passes: int = 3) -> bool:
    """
    Securely delete a file by overwriting it multiple times before deletion.
    
    Args:
        file_path (str): The path to the file to delete.
        passes (int, optional): The number of overwrite passes to perform. Defaults to 3.
    
    Returns:
        bool: True if the file was successfully deleted, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for secure deletion: {file_path}")
        return False
    
    try:
        # Get the file size
        file_size = os.path.getsize(file_path)
        
        # Open the file for writing
        with open(file_path, 'wb') as f:
            # Perform multiple overwrite passes
            for _ in range(passes):
                # Seek to the beginning of the file
                f.seek(0)
                
                # Write random data
                f.write(os.urandom(file_size))
                
                # Flush to ensure data is written
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(file_path)
        return True
    
    except Exception as e:
        logger.error(f"Error securely deleting file {file_path}: {str(e)}")
        return False


def create_secure_temp_file(data: Union[str, bytes] = None) -> str:
    """
    Create a secure temporary file.
    
    Args:
        data (Union[str, bytes], optional): Data to write to the file. If None, an empty file is created.
    
    Returns:
        str: The path to the temporary file.
    """
    # Create a temporary file
    fd, path = tempfile.mkstemp(prefix="rebelscribe_", suffix=".tmp")
    
    try:
        # Write data if provided
        if data is not None:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
        else:
            # Close the file descriptor if no data is provided
            os.close(fd)
        
        return path
    
    except Exception as e:
        # Clean up on error
        os.close(fd)
        if os.path.exists(path):
            os.remove(path)
        logger.error(f"Error creating secure temporary file: {str(e)}")
        raise


def create_secure_temp_directory() -> str:
    """
    Create a secure temporary directory.
    
    Returns:
        str: The path to the temporary directory.
    """
    # Create a temporary directory
    path = tempfile.mkdtemp(prefix="rebelscribe_")
    return path


def cleanup_secure_temp_file(file_path: str) -> bool:
    """
    Securely clean up a temporary file.
    
    Args:
        file_path (str): The path to the temporary file.
    
    Returns:
        bool: True if the file was successfully cleaned up, False otherwise.
    """
    return secure_delete_file(file_path)


def cleanup_secure_temp_directory(directory_path: str) -> bool:
    """
    Securely clean up a temporary directory.
    
    Args:
        directory_path (str): The path to the temporary directory.
    
    Returns:
        bool: True if the directory was successfully cleaned up, False otherwise.
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        logger.warning(f"Directory not found for secure cleanup: {directory_path}")
        return False
    
    try:
        # Securely delete all files in the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                secure_delete_file(file_path)
        
        # Remove the directory
        shutil.rmtree(directory_path)
        return True
    
    except Exception as e:
        logger.error(f"Error securely cleaning up directory {directory_path}: {str(e)}")
        return False


def store_key_securely(key: bytes, key_file: str, password: str) -> bool:
    """
    Store an encryption key securely.
    
    Args:
        key (bytes): The encryption key to store.
        key_file (str): The path to the file where the key will be stored.
        password (str): The password to protect the key.
    
    Returns:
        bool: True if the key was successfully stored, False otherwise.
    
    Raises:
        RuntimeError: If encryption is not available.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    try:
        # Derive a key from the password
        derived_key, salt = derive_key_from_password(password)
        
        # Encrypt the key
        encrypted_key = encrypt_data(key, derived_key)
        
        # Create the key file directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(key_file)), exist_ok=True)
        
        # Write the salt and encrypted key to the file
        with open(key_file, 'wb') as f:
            f.write(salt)
            f.write(encrypted_key)
        
        return True
    
    except Exception as e:
        logger.error(f"Error storing key securely: {str(e)}")
        return False


def load_key_securely(key_file: str, password: str) -> Optional[bytes]:
    """
    Load an encryption key securely.
    
    Args:
        key_file (str): The path to the file where the key is stored.
        password (str): The password protecting the key.
    
    Returns:
        Optional[bytes]: The encryption key, or None if the key could not be loaded.
    
    Raises:
        RuntimeError: If encryption is not available.
        FileNotFoundError: If the key file does not exist.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"Key file not found: {key_file}")
    
    try:
        # Read the salt and encrypted key from the file
        with open(key_file, 'rb') as f:
            salt = f.read(16)
            encrypted_key = f.read()
        
        # Derive the key from the password
        derived_key, _ = derive_key_from_password(password, salt)
        
        # Decrypt the key
        key = decrypt_data(encrypted_key, derived_key)
        
        return key
    
    except Exception as e:
        logger.error(f"Error loading key securely: {str(e)}")
        return None


def encrypt_config_value(value: str, key: bytes) -> str:
    """
    Encrypt a configuration value.
    
    Args:
        value (str): The value to encrypt.
        key (bytes): The encryption key.
    
    Returns:
        str: The encrypted value as a base64-encoded string.
    
    Raises:
        RuntimeError: If encryption is not available.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    # Encrypt the value
    encrypted_data = encrypt_data(value, key)
    
    # Encode as base64 for storage in config files
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_config_value(encrypted_value: str, key: bytes) -> str:
    """
    Decrypt a configuration value.
    
    Args:
        encrypted_value (str): The encrypted value as a base64-encoded string.
        key (bytes): The encryption key.
    
    Returns:
        str: The decrypted value.
    
    Raises:
        RuntimeError: If encryption is not available.
        ValueError: If the key is invalid or the value is corrupted.
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("Encryption functionality is not available. Please install cryptography package.")
    
    # Decode from base64
    encrypted_data = base64.b64decode(encrypted_value)
    
    # Decrypt the value
    decrypted_data = decrypt_data(encrypted_data, key)
    
    # Convert to string
    return decrypted_data.decode('utf-8')
