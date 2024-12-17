"""
The `blockchain.py` file manages the blockchain's core functionalities, including 
block creation, transaction storage, and balance calculations. It uses an SQLite 
database (`blockchain.db`) to persist blocks and transactions.

Key functionalities:
1. **create_block**: Generates a new block using transactions and a reference to the previous block's hash.
   - Hashing ensures the integrity of the block by creating a cryptographic fingerprint.
2. **add_block**: Adds a block and its transactions to the database, ensuring immutability.
3. **get_latest_block**: Retrieves the most recent block added to the blockchain.
4. **get_balance**: Calculates the balance for a given public key based on incoming and outgoing transactions.
5. **is_transaction_processed**: Checks whether a transaction has already been added to the blockchain.

Important Concepts:
- **Blocks**: A block contains a header (previous hash, timestamp, and block hash) and a body (list of transactions).
- **Transactions**: A transaction includes sender, recipient, amount, timestamp, and a unique transaction ID.
- **Database Locking**: Thread safety is ensured using a lock (`threading.Lock`) to handle concurrent access to the SQLite database.
"""
import sqlite3
import json
import threading
import hashlib
import time

class Blockchain:
    def __init__(self, logger):
        self.logger = logger
        self.lock = threading.Lock()
        self.db_connection = sqlite3.connect('blockchain.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.lock:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    block_hash TEXT PRIMARY KEY,
                    block_data TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    block_hash TEXT,
                    sender_public_key TEXT,
                    recipient_public_key TEXT,
                    amount REAL,
                    timestamp INTEGER,
                    data TEXT
                )
            ''')
            self.db_connection.commit()

    def create_block(self, transactions, previous_hash):
        block = {
            'header': {
                'previous_hash': previous_hash,
                'timestamp': int(time.time()),
                'block_hash': '',
            },
            'body': {
                'transactions': transactions
            }
        }
        block_string = json.dumps(block['body'], sort_keys=True).encode('utf-8')
        block_hash = hashlib.sha256(block_string).hexdigest()
        block['header']['block_hash'] = block_hash
        return block

    def add_block(self, block):
        with self.lock:
            cursor = self.db_connection.cursor()
            block_hash = block['header']['block_hash']
            block_data = json.dumps(block)
            cursor.execute('INSERT INTO blocks (block_hash, block_data) VALUES (?, ?)', (block_hash, block_data))

            for transaction in block['body']['transactions']:
                cursor.execute('''
                    INSERT INTO transactions (
                        transaction_id,
                        block_hash,
                        sender_public_key,
                        recipient_public_key,
                        amount,
                        timestamp,
                        data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction['transaction_id'],
                    block_hash,
                    transaction['sender_public_key'],
                    transaction.get('recipient_public_key', ''),
                    transaction.get('amount', 0),
                    transaction['timestamp'],
                    json.dumps(transaction)
                ))
            self.db_connection.commit()
            self.logger.log_event(f"Block added with hash: {block_hash}", "INFO")

    def get_latest_block(self):
        with self.lock:
            cursor = self.db_connection.cursor()
            cursor.execute('SELECT block_data FROM blocks ORDER BY rowid DESC LIMIT 1')
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            else:
                return None

    def get_balance(self, public_key):
        with self.lock:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT SUM(amount) FROM transactions
                WHERE recipient_public_key = ?
            ''', (public_key,))
            total_received = cursor.fetchone()[0] or 0

            cursor.execute('''
                SELECT SUM(amount) FROM transactions
                WHERE sender_public_key = ?
            ''', (public_key,))
            total_sent = cursor.fetchone()[0] or 0

            return total_received - total_sent

    def is_transaction_processed(self, transaction_id):
        with self.lock:
            cursor = self.db_connection.cursor()
            cursor.execute('SELECT 1 FROM transactions WHERE transaction_id = ?', (transaction_id,))
            return cursor.fetchone() is not None
