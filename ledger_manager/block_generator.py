# The BlockGenerator class is responsible for creating new blocks in the blockchain.
# It gathers transactions from the transaction pool, calculates the Merkle root for the 
# transactions, signs the block for integrity, and generates a unique hash for the block header.

# Key functionalities:
# 1. **create_block**: Retrieves transactions from the pool, executes any associated smart contracts, 
#    computes the Merkle root, and bundles them into a new block with metadata.
# 2. **calculate_merkle_root**: Recursively hashes pairs of transaction hashes to create a single hash 
#    representing the entire block’s transactions. This ensures the data integrity of transactions.
# 3. **hash_transaction**: Creates a SHA256 hash of an individual transaction for inclusion in the Merkle tree.
# 4. **hash_pair**: Combines two transaction hashes and hashes them again to advance the Merkle root computation.
# 5. **generate_block_hash**: Generates a unique SHA256 hash for the block header based on its contents.

# What is a Merkle root?
# A Merkle root is a single hash that summarises all the transactions in a block. It is built by 
# repeatedly hashing pairs of transaction hashes until only one hash remains. This makes the 
# blockchain tamper-evident because any modification to a transaction changes the Merkle root.

import json
import time
import hashlib

class BlockGenerator:
    def __init__(self, transaction_pool, blockchain, consensus, logger, smart_contract_executor):
        self.transaction_pool = transaction_pool
        self.blockchain = blockchain
        self.consensus = consensus
        self.logger = logger
        self.smart_contract_executor = smart_contract_executor
        self.MAX_TRANSACTIONS_PER_BLOCK = 100

    def create_block(self):
        transactions = self.transaction_pool.get_transactions(self.MAX_TRANSACTIONS_PER_BLOCK)
        if not transactions:
            self.logger.log_event("No transactions to include in the block", "INFO")
            return None

        previous_block = self.blockchain.get_latest_block()
        previous_hash = previous_block['header']['block_hash'] if previous_block else '0' * 64

        block_body = {
            'transactions': [],
            'smart_contract_results': []
        }

        for transaction in transactions:
            contract_result = self.smart_contract_executor.execute_contract(transaction)
            if contract_result is not None:
                block_body['smart_contract_results'].append({
                    'transaction_id': transaction['transaction_id'],
                    'result': contract_result
                })
            block_body['transactions'].append(transaction)

        merkle_root = self.calculate_merkle_root(block_body['transactions'])

        block_header = {
            'previous_hash': previous_hash,
            'timestamp': int(time.time()),
            'nonce': 0,
            'merkle_root': merkle_root,
            'block_hash': '',
            'ledger_manager_signature': ''
        }

        block_header['block_hash'] = self.generate_block_hash(block_header)

        block = {
            'header': block_header,
            'body': block_body
        }

        block = self.consensus.sign_block(block)

        self.logger.log_event(f"Block created with hash: {block_header['block_hash']}", "INFO")
        return block

    def calculate_merkle_root(self, transactions):
        transaction_hashes = [self.hash_transaction(tx) for tx in transactions]
        if not transaction_hashes:
            return ''
        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])
            transaction_hashes = [
                self.hash_pair(transaction_hashes[i], transaction_hashes[i + 1])
                for i in range(0, len(transaction_hashes), 2)
            ]
        return transaction_hashes[0]

    def hash_transaction(self, transaction):
        transaction_string = json.dumps(transaction, sort_keys=True)
        return hashlib.sha256(transaction_string.encode('utf-8')).hexdigest()

    def hash_pair(self, hash1, hash2):
        return hashlib.sha256((hash1 + hash2).encode('utf-8')).hexdigest()

    def generate_block_hash(self, block_header):
        header_copy = block_header.copy()
        header_copy['ledger_manager_signature'] = ''
        header_string = json.dumps(header_copy, sort_keys=True)
        return hashlib.sha256(header_string.encode('utf-8')).hexdigest()
