# The TransactionPool class manages incoming transactions for the blockchain.
# It provides a way to add, retrieve, and remove transactions before they are processed into a block.

# Key functionalities:
# 1. **add_transaction**: Adds a new transaction to the pool if it is not a duplicate.
# 2. **get_transactions**: Retrieves a specified number of transactions for block generation.
# 3. **remove_transactions**: Removes transactions from the pool once they have been included in a block.
# 4. **clear_transactions**: Clears the entire pool, useful during resets or synchronisations.
# 5. **is_duplicate**: Checks whether a transaction with the same ID already exists in the pool to avoid redundancy.

from threading import Lock

class TransactionPool:
    def __init__(self, logger):
        self.transactions = []
        self.lock = Lock()
        self.logger = logger

    def add_transaction(self, transaction):
        with self.lock:
            if not self.is_duplicate(transaction):
                self.transactions.append(transaction)
                self.logger.log_event(f"Transaction added to pool: {transaction['transaction_id']}", "INFO")
            else:
                self.logger.log_event(f"Duplicate transaction detected: {transaction['transaction_id']}", "WARNING")

    def get_transactions(self, max_count):
        with self.lock:
            return self.transactions[:max_count]

    def remove_transactions(self, transactions):
        with self.lock:
            for tx in transactions:
                if tx in self.transactions:
                    self.transactions.remove(tx)
                    self.logger.log_event(f"Transaction removed from pool: {tx['transaction_id']}", "DEBUG")

    def clear_transactions(self):
        with self.lock:
            self.transactions.clear()
            self.logger.log_event("Transaction pool cleared", "INFO")

    def is_duplicate(self, transaction):
        return any(tx['transaction_id'] == transaction['transaction_id'] for tx in self.transactions)
