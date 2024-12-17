"""
security.py

This module manages cryptographic security operations for the trading node, including key pair generation, signing, and verification of data. 
It is integral to ensuring the authenticity and integrity of transactions.

Core Features:
1. **Public and Private Keys**: 
   - A private key is used to sign data (e.g., transactions), ensuring it originates from a verified user.
   - A public key is shared with others to verify the signature's authenticity.

2. **Blockchain Role**: 
   - Transactions on a blockchain require signatures to prove ownership and prevent tampering. The private key signs the data, while the public key validates the signature.

Key Methods:
- `generate_keys()`: Generates a new RSA key pair if none exists.
- `sign_data()`: Signs transaction data using the private key.
- `verify_signature()`: Verifies that the transaction signature matches the provided public key.
- `generate_transaction_id()`: Creates a unique identifier for transactions.
- `transaction_to_string()`: Converts transaction data into a consistent string format for signing.

This module ensures all cryptographic operations adhere to blockchain security standards, preventing malicious activity.
"""

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import os
import json

class Security:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.load_keys()

    def load_keys(self):
        if os.path.exists('private_key.pem') and os.path.exists('public_key.pem'):
            with open('private_key.pem', 'rb') as f:
                self.private_key = RSA.import_key(f.read())
            with open('public_key.pem', 'rb') as f:
                self.public_key = RSA.import_key(f.read())
        else:
            self.generate_keys()

    def generate_keys(self):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        with open('private_key.pem', 'wb') as f:
            f.write(private_key)
        with open('public_key.pem', 'wb') as f:
            f.write(public_key)
        self.private_key = RSA.import_key(private_key)
        self.public_key = RSA.import_key(public_key)

    def sign_data(self, data):
        h = SHA256.new(data.encode('utf-8'))
        signature = pkcs1_15.new(self.private_key).sign(h)
        return signature.hex()

    def verify_signature(self, data, signature, public_key_pem):
        public_key = RSA.import_key(public_key_pem)
        h = SHA256.new(data.encode('utf-8'))
        try:
            pkcs1_15.new(public_key).verify(h, bytes.fromhex(signature))
            return True
        except (ValueError, TypeError):
            return False

    def get_public_key_pem(self):
        return self.public_key.export_key().decode('utf-8')

    def generate_transaction_id(self):
        return os.urandom(16).hex()

    def transaction_to_string(self, transaction):
        """
        Converts a transaction dictionary to a string in a consistent order for signing.
        """
        # Ensure the dictionary is sorted to maintain consistency
        transaction_string = json.dumps(transaction, sort_keys=True)
        return transaction_string