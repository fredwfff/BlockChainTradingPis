# The Validator class handles the validation of transactions within the blockchain system.
# It ensures that each transaction is legitimate before it is added to a block. Specifically, 
# it checks three main aspects: the validity of the transaction signature, the sender's 
# balance, and whether the transaction has already been processed (double-spending check).

# Key functionalities:
# 1. **validate_transaction**: The main method that validates a transaction by calling
#    other methods to verify the signature, check the balance, and ensure no double-spending.
# 2. **verify_signature**: Verifies the authenticity of the transaction by checking that the 
#    transaction signature matches the sender's public key. This ensures that the transaction 
#    was signed by the rightful owner of the funds.
# 3. **check_balance**: Ensures that the sender has sufficient balance to cover the transaction.
# 4. **is_double_spending**: Checks whether the transaction has already been processed, 
#    preventing double-spending.

# Blockchain signatures:
# - **Who signs**: The sender of the transaction signs it using their private key. This provides proof 
#   that the transaction is authorised by the wallet owner.
# - **Who validates**: Validators (usually network participants or nodes) validate the transaction by 
#   checking the signature against the sender's public key, verifying the sender's balance, and ensuring 
#   that the transaction hasn't been processed previously.

import json

class Validator:
    def __init__(self, blockchain, logger, security):
        self.blockchain = blockchain
        self.logger = logger
        self.security = security

    def validate_transaction(self, transaction):
        if not self.verify_signature(transaction):
            self.logger.log_event("Invalid signature", "ERROR")
            return False, "Invalid signature"
        if not self.check_balance(transaction):
            self.logger.log_event("Insufficient balance", "ERROR")
            return False, "Insufficient balance"
        if self.is_double_spending(transaction):
            self.logger.log_event("Double spending detected", "ERROR")
            return False, "Double spending detected"
        return True, ""

    def verify_signature(self, transaction):
        sender_public_key_pem = transaction['sender_public_key']
        signature = transaction['signature']
        transaction_data = transaction.copy()
        transaction_data.pop('signature', None)
        transaction_string = self.security.transaction_to_string(transaction_data)
        return self.security.verify_signature(transaction_string, signature, sender_public_key_pem)

    def check_balance(self, transaction):
        sender_public_key = transaction['sender_public_key']
        amount = transaction.get('amount', 0)
        balance = self.blockchain.get_balance(sender_public_key)
        return balance >= amount

    def is_double_spending(self, transaction):
        transaction_id = transaction['transaction_id']
        if self.blockchain.is_transaction_processed(transaction_id):
            return True
        return False
