"""
wallet.py

This module manages the wallet functionality for the SMA trading node. It tracks the node's balance and assets, ensuring all updates are thread-safe.

Core Features:
1. **Wallet Storage**:
   - The wallet balance and asset holdings are stored in a JSON file (`wallet.json`) for persistence.

2. **Thread-Safe Operations**:
   - Uses an `RLock` to ensure that wallet operations (updates and reads) are thread-safe, preventing data corruption in concurrent scenarios.

3. **Balance and Asset Management**:
   - `deposit()`: Adds funds to the wallet.
   - `update_balance()`: Updates the wallet balance (e.g., after trades).
   - `update_asset()`: Adjusts the quantity of an asset in the wallet. If the quantity falls to zero or below, the asset is removed.

4. **Data Retrieval**:
   - `get_balance()`: Returns the current wallet balance.
   - `get_assets()`: Returns the asset holdings as a dictionary.

Important Notes:
- Wallet data is automatically saved to `wallet.json` after every update to ensure persistence.
- If the wallet file does not exist, a new one is created with an initial balance of 0.0 and no assets.

This module is integral to maintaining accurate financial data for the node's operations, ensuring that trades reflect the correct balance and asset holdings.
"""

import json
from threading import RLock

class Wallet:
    def __init__(self, security):
        self.security = security
        self.balance = 0.0
        self.assets = {}
        self.lock = RLock()
        self.load_wallet()

    def load_wallet(self):
        try:
            with self.lock:
                with open('wallet.json', 'r') as f:
                    data = json.load(f)
                    self.balance = data.get('balance', 0.0)
                    self.assets = data.get('assets', {})
        except FileNotFoundError:
            self.save_wallet()

    def save_wallet(self):
        with self.lock:
            data = {
                'balance': self.balance,
                'assets': self.assets
            }
            with open('wallet.json', 'w') as f:
                json.dump(data, f)

    def deposit(self, amount):
        with self.lock:
            self.balance += amount
            self.save_wallet()

    def update_balance(self, amount):
        with self.lock:
            self.balance += amount
            self.save_wallet()

    def update_asset(self, symbol, quantity):
        with self.lock:
            self.assets[symbol] = self.assets.get(symbol, 0) + quantity
            if self.assets[symbol] <= 0:
                del self.assets[symbol]
            self.save_wallet()

    def get_balance(self):
        return self.balance

    def get_assets(self):
        return self.assets.copy()