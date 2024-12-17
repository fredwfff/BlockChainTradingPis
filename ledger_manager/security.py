"""
The `security.py` file implements cryptographic functions to ensure data integrity, 
authentication, and security in the Ledger Manager. It generates and manages public 
and private key pairs, signs data, and verifies signatures.

Key Concepts:
1. **Public and Private Keys**:
    - A **private key** is used to sign data (e.g., transactions or blocks), proving its authenticity.
    - A **public key** can be shared and is used to verify that the data was signed by the corresponding private key.
2. **Usage in Blockchain**:
    - Transactions are signed using the sender's private key. 
    - Validators use the sender's public key to verify the transaction's signature, ensuring the sender's identity and data integrity.
3. **Signature**: A cryptographic fingerprint generated from the data and the private key. Any change to the data invalidates the signature.

Functions:
- **sign_data**: Signs a given string of data using the private key.
- **verify_signature**: Verifies a signature against the data and the signer's public key.
- **generate_transaction_id**: Generates a unique identifier for transactions.
"""
import ssl
import os
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

class Security:
    def __init__(self):
        self.private_key_path = 'private_key.pem'
        self.public_key_path = 'public_key.pem'
        self.private_key = None
        self.public_key = None
        self.ensure_keys_exist()
        self.load_keys()

    def ensure_keys_exist(self):
        if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
            self.generate_key_pair()

    def generate_key_pair(self):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        with open(self.private_key_path, 'wb') as f:
            f.write(private_key)
        with open(self.public_key_path, 'wb') as f:
            f.write(public_key)

    def load_keys(self):
        with open(self.private_key_path, 'rb') as f:
            self.private_key = RSA.import_key(f.read())
        with open(self.public_key_path, 'rb') as f:
            self.public_key = RSA.import_key(f.read())

    def sign_data(self, data):
        h = SHA256.new(data.encode('utf-8'))
        signature = pkcs1_15.new(self.private_key).sign(h)
        return signature.hex()

    def verify_signature(self, data, signature_hex, public_key_pem):
        public_key = RSA.import_key(public_key_pem)
        signature = bytes.fromhex(signature_hex)
        h = SHA256.new(data.encode('utf-8'))
        try:
            pkcs1_15.new(public_key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False

    def get_public_key_pem(self):
        return self.public_key.export_key().decode('utf-8')

    def generate_transaction_id(self):
        return os.urandom(16).hex()

    def transaction_to_string(self, transaction):
        transaction_string = json.dumps(transaction, sort_keys=True)
        return transaction_string

    def configure_ssl_context(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        return ssl_context
