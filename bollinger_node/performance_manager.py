"""
performance_manager.py

This module manages the performance metrics of the trading node. It tracks and records important statistics such as:
1. **Initial Deposit and Additional Deposits**: Tracks the total capital injected into the trading node.
2. **Trades Executed**: Logs the number of trades completed by the node.
3. **Profit/Loss Tracking**: Maintains the total profit or loss from all trades, as well as identifying the best and worst trades.
4. **Trade History**: Maintains a history of all trades executed with key details.
5. **Portfolio Value and ROI**: Calculates the return on investment (ROI) by comparing the current portfolio value with the total invested amount.

The file persists data to a JSON file (`performance_bollinger.json`) to ensure metrics are stored between runs.

**Benchmarks**: If processed, benchmarks represent reference values or targets (e.g., the performance of a specific stock or portfolio) used to compare the node's performance over time.

Key Methods:
- `set_initial_deposit()`: Records the initial and additional deposits.
- `record_trade()`: Updates trade metrics after each trade.
- `get_performance_data()`: Provides a summary of all performance metrics.
- `update_portfolio_value()`: Updates the latest portfolio value for ROI calculation.

"""
import json
import os
from datetime import datetime

class PerformanceManager:
    def __init__(self, wallet, node_name="Bollinger"):
        self.wallet = wallet
        self.node_name = node_name
        self.filename = "performance_bollinger.json"
        self.data = {
            "initial_deposit": 0.0,
            "additional_deposits": 0.0,
            "trades_executed": 0,
            "total_profit_loss": 0.0,
            "best_trade": None,   # Will store {"type":..., "symbol":..., "profit":..., "timestamp":...}
            "worst_trade": None,  # Same structure as best_trade
            "trade_history": []   # Store small info on each trade to compute stats later
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.data = json.load(f)

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=2)

    def set_initial_deposit(self, amount):
        # Called at startup after user sets initial deposit.
        # If initial_deposit is 0, set it. Otherwise, treat as additional deposit.
        if self.data["initial_deposit"] == 0.0:
            self.data["initial_deposit"] = amount
        else:
            # Additional deposit
            self.data["additional_deposits"] += amount
        self.save_data()

    def record_trade(self, trade_type, symbol, quantity, price, total):
        # Update trades executed
        self.data["trades_executed"] += 1

        # Compute profit/loss of this trade relative to the trade's cost:
        # For a 'buy', profit impact = -total
        # For a 'sell', profit impact = +total
        # Profit/Loss is considered as how it affects the cash after initial deposit.
        if trade_type.lower() == 'buy':
            pl = -total
        else:  # sell
            pl = total

        self.data["total_profit_loss"] += pl

        # Check best/worst trade
        # Profit of a single trade in this simplified approach = pl of that trade
        # Actually, for a buy transaction alone, it's a cost, not a profit. Typically you'd measure profit after a buy and subsequent sell.
        # But we'll just track largest positive (best) and most negative (worst) immediate impact.
        trade_info = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "type": trade_type,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total": total,
            "profit_loss": pl
        }
        self.data["trade_history"].append(trade_info)

        # Update best trade
        if self.data["best_trade"] is None or pl > self.data["best_trade"]["profit"]:
            self.data["best_trade"] = {
                "type": trade_type,
                "symbol": symbol,
                "profit": pl,
                "timestamp": trade_info["timestamp"]
            }

        # Update worst trade
        if self.data["worst_trade"] is None or pl < self.data["worst_trade"]["profit"]:
            self.data["worst_trade"] = {
                "type": trade_type,
                "symbol": symbol,
                "profit": pl,
                "timestamp": trade_info["timestamp"]
            }

        self.save_data()

    def get_performance_data(self):
        # Current portfolio value
        current_value = self.wallet.get_balance()
        for symbol, qty in self.wallet.get_assets().items():
            pass

        # total_invested is initial_deposit + additional_deposits
        total_invested = self.data["initial_deposit"] + self.data["additional_deposits"]

        # ROI since start (dynamic calculation): (current_portfolio_value - total_invested) / total_invested
        current_portfolio_value = self.data.get("latest_portfolio_value", self.wallet.get_balance())
        if total_invested > 0:
            roi = (current_portfolio_value - total_invested) / total_invested
        else:
            roi = 0.0

        # Final dict
        return {
            "node_name": self.node_name,
            "initial_deposit": self.data["initial_deposit"],
            "additional_deposits": self.data["additional_deposits"],
            "trades_executed": self.data["trades_executed"],
            "total_profit_loss": self.data["total_profit_loss"],
            "best_trade": self.data["best_trade"],
            "worst_trade": self.data["worst_trade"],
            "current_portfolio_value": current_portfolio_value,
            "roi_since_start": roi
        }

    def update_portfolio_value(self, value):
        self.data["latest_portfolio_value"] = value
        self.save_data()