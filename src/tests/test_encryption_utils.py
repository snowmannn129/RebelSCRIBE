#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the encryption_utils module.

This module contains tests for the encryption utilities:
- Data encryption/decryption
- Key management
- Secure storage
- Password hashing
- Secure deletion
"""

import os
import base64
import tempfile
import unittest
import shutil
from unittest.mock import patch, MagicMock

from src.utils.encryption_utils import (
    check_encryption_available, generate_key, derive_key_from_password,
    encrypt_data, decrypt_data, encrypt_file, decrypt_file,
    hash_password, verify_password, secure_delete_file,
    create_secure_temp_file, create_secure_temp_directory,
    cleanup_secure_temp_file, cleanup_secure_temp_directory,
    store_key_securely, load_key_securely,
    encrypt_config_value, decrypt_config_value
)


class TestEncryptionUtils(unittest.TestCase):
    """Tests for the encryption_utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Skip tests if encryption is not available
        if not check_encryption_available():
            self.skipTest("Encryption functionality is not available")
        
        # Generate a test key
        self.test_key = generate_key()
        
        # Create test files
        self.text_file = os.path.join(self.test_dir, "test.txt")
        with open(self.text_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        self.binary_file = os.path.join(self.test_dir, "test.bin")
        with open(self.binary_file, 'wb') as f:
            f.write(b"Binary content")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_check_encryption_available(self):
        """Test checking if encryption is available."""
        # This should return a boolean
        result = check_encryption_available()
        self.assertIsInstance(result, bool)
    
    def test_generate_key(self):
        """Test generating an encryption key."""
        # Generate a key
        key = generate_key()
        
        # Verify the key
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 44)  # Fernet keys are 44 bytes
        
        # Generate another key
        another_key = generate_key()
        
        # Verify the keys are different
        self.assertNotEqual(key, another_key)
    
    def test_derive_key_from_password(self):
        """Test deriving a key from a password."""
        # Derive a key
        password = "test_password"
        key, salt = derive_key_from_password(password)
        
        # Verify the key and salt
        self.assertIsInstance(key, bytes)
        self.assertIsInstance(salt, bytes)
        self.assertEqual(len(salt), 16)
        
        # Derive the key again with the same salt
        key2, salt2 = derive_key_from_password(password, salt)
        
        # Verify the keys are the same
        self.assertEqual(key, key2)
        self.assertEqual(salt, salt2)
        
        # Derive a key with a different password
        key3, _ = derive_key_from_password("different_password", salt)
        
        # Verify the keys are different
        self.assertNotEqual(key, key3)
    
    def test_encrypt_decrypt_data(self):
        """Test encrypting and decrypting data."""
        # Test with string data
        data = "Test data"
        encrypted = encrypt_data(data, self.test_key)
        
        # Verify the encrypted data
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, data.encode())
        
        # Decrypt the data
        decrypted = decrypt_data(encrypted, self.test_key)
        
        # Verify the decrypted data
        self.assertEqual(decrypted.decode(), data)
        
        # Test with bytes data
        data = b"Binary data"
        encrypted = encrypt_data(data, self.test_key)
        
        # Verify the encrypted data
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, data)
        
        # Decrypt the data
        decrypted = decrypt_data(encrypted, self.test_key)
        
        # Verify the decrypted data
        self.assertEqual(decrypted, data)
        
        # Test with invalid key
        with self.assertRaises(Exception):
            decrypt_data(encrypted, generate_key())
    
    def test_encrypt_decrypt_file(self):
        """Test encrypting and decrypting a file."""
        # Encrypt the text file
        encrypted_file = encrypt_file(self.text_file, self.test_key, os.path.join(self.test_dir, "encrypted.txt"))
        
        # Verify the encrypted file
        self.assertTrue(os.path.exists(encrypted_file))
        
        # Decrypt the file
        decrypted_file = decrypt_file(encrypted_file, self.test_key, os.path.join(self.test_dir, "decrypted.txt"))
        
        # Verify the decrypted file
        self.assertTrue(os.path.exists(decrypted_file))
        
        # Verify the content
        with open(decrypted_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "Test content")
        
        # Test with in-place encryption/decryption
        in_place_file = os.path.join(self.test_dir, "in_place.txt")
        with open(in_place_file, 'w', encoding='utf-8') as f:
            f.write("In-place test")
        
        # Encrypt in place
        encrypt_file(in_place_file, self.test_key)
        
        # Verify the file is encrypted
        with open(in_place_file, 'rb') as f:
            encrypted_content = f.read()
        self.assertNotEqual(encrypted_content, b"In-place test")
        
        # Decrypt in place
        decrypt_file(in_place_file, self.test_key)
        
        # Verify the file is decrypted
        with open(in_place_file, 'r', encoding='utf-8') as f:
            decrypted_content = f.read()
        self.assertEqual(decrypted_content, "In-place test")
        
        # Test with invalid key
        with self.assertRaises(Exception):
            decrypt_file(encrypted_file, generate_key())
        
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            encrypt_file(os.path.join(self.test_dir, "nonexistent.txt"), self.test_key)
    
    def test_hash_verify_password(self):
        """Test hashing and verifying a password."""
        # Hash a password
        password = "test_password"
        password_hash, salt = hash_password(password)
        
        # Verify the hash and salt
        self.assertIsInstance(password_hash, bytes)
        self.assertIsInstance(salt, bytes)
        
        # Verify the password
        self.assertTrue(verify_password(password, password_hash, salt))
        
        # Verify with incorrect password
        self.assertFalse(verify_password("wrong_password", password_hash, salt))
        
        # Hash with a specific salt
        specific_salt = os.urandom(16)
        password_hash2, salt2 = hash_password(password, specific_salt)
        
        # Verify the salt is the same
        self.assertEqual(salt2, specific_salt)
        
        # Verify the password
        self.assertTrue(verify_password(password, password_hash2, salt2))
    
    def test_secure_delete_file(self):
        """Test securely deleting a file."""
        # Create a file to delete
        file_to_delete = os.path.join(self.test_dir, "to_delete.txt")
        with open(file_to_delete, 'w', encoding='utf-8') as f:
            f.write("File to delete")
        
        # Verify the file exists
        self.assertTrue(os.path.exists(file_to_delete))
        
        # Securely delete the file
        result = secure_delete_file(file_to_delete)
        
        # Verify the result and file deletion
        self.assertTrue(result)
        self.assertFalse(os.path.exists(file_to_delete))
        
        # Test with non-existent file
        result = secure_delete_file(os.path.join(self.test_dir, "nonexistent.txt"))
        self.assertFalse(result)
    
    def test_create_cleanup_secure_temp_file(self):
        """Test creating and cleaning up a secure temporary file."""
        # Create a temporary file
        temp_file = create_secure_temp_file("Temp content")
        
        # Verify the file exists
        self.assertTrue(os.path.exists(temp_file))
        
        # Verify the content
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "Temp content")
        
        # Clean up the file
        result = cleanup_secure_temp_file(temp_file)
        
        # Verify the result and file deletion
        self.assertTrue(result)
        self.assertFalse(os.path.exists(temp_file))
        
        # Test with binary data
        temp_file = create_secure_temp_file(b"Binary content")
        
        # Verify the file exists
        self.assertTrue(os.path.exists(temp_file))
        
        # Verify the content
        with open(temp_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"Binary content")
        
        # Clean up the file
        cleanup_secure_temp_file(temp_file)
    
    def test_create_cleanup_secure_temp_directory(self):
        """Test creating and cleaning up a secure temporary directory."""
        # Create a temporary directory
        temp_dir = create_secure_temp_directory()
        
        # Verify the directory exists
        self.assertTrue(os.path.exists(temp_dir))
        self.assertTrue(os.path.isdir(temp_dir))
        
        # Create some files in the directory
        for i in range(3):
            file_path = os.path.join(temp_dir, f"file{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Content {i}")
        
        # Clean up the directory
        result = cleanup_secure_temp_directory(temp_dir)
        
        # Verify the result and directory deletion
        self.assertTrue(result)
        self.assertFalse(os.path.exists(temp_dir))
        
        # Test with non-existent directory
        result = cleanup_secure_temp_directory(os.path.join(self.test_dir, "nonexistent"))
        self.assertFalse(result)
    
    def test_store_load_key_securely(self):
        """Test storing and loading a key securely."""
        # Create a key file
        key_file = os.path.join(self.test_dir, "key.dat")
        
        # Store the key
        password = "test_password"
        result = store_key_securely(self.test_key, key_file, password)
        
        # Verify the result and file creation
        self.assertTrue(result)
        self.assertTrue(os.path.exists(key_file))
        
        # Load the key
        loaded_key = load_key_securely(key_file, password)
        
        # Verify the loaded key
        self.assertEqual(loaded_key, self.test_key)
        
        # Test with incorrect password
        loaded_key = load_key_securely(key_file, "wrong_password")
        self.assertIsNone(loaded_key)
        
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            load_key_securely(os.path.join(self.test_dir, "nonexistent.dat"), password)
    
    def test_encrypt_decrypt_config_value(self):
        """Test encrypting and decrypting a configuration value."""
        # Encrypt a value
        value = "sensitive_value"
        encrypted = encrypt_config_value(value, self.test_key)
        
        # Verify the encrypted value
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, value)
        
        # Decrypt the value
        decrypted = decrypt_config_value(encrypted, self.test_key)
        
        # Verify the decrypted value
        self.assertEqual(decrypted, value)
        
        # Test with invalid key
        with self.assertRaises(Exception):
            decrypt_config_value(encrypted, generate_key())


if __name__ == '__main__':
    unittest.main()
