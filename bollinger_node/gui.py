"""
gui.py

This module provides a graphical user interface (GUI) for interacting with the Bollinger trading node. It allows users to monitor and control the trading process while visualising key metrics and trade history.

Core Features:
1. **Dashboard**:
   - Displays wallet balance, current holdings, and performance metrics such as ROI, total profit/loss, and best/worst trades.
   - Updates performance data dynamically as trades occur.

2. **Trading Control**:
   - Users can start and pause the trading process.
   - The GUI also manages initial deposits and portfolio tracking.

3. **Node Comparison**:
   - Fetches performance data from other nodes (e.g., SMA Node) to display comparative metrics.

4. **Trade History**:
   - Logs all executed trades, showing timestamps, types (buy/sell), symbols, quantities, and transaction amounts.

5. **Data Management**:
   - Provides the option to delete wallet and performance data upon exiting the application.

Key Functions:
- `start_trading()` and `pause_trading()`: Control the trading execution.
- `update_portfolio_display()` and `update_performance_display()`: Refresh displayed metrics based on the latest performance data.
- `fetch_other_node_data()`: Retrieves and displays comparative performance data from a peer trading node.

This module acts as a user-friendly interface for real-time monitoring and control of the Bollinger trading strategy, ensuring users can oversee trading activity and performance metrics effectively.
"""

import sys
import os
import asyncio
import aiohttp
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QMessageBox, QTabWidget,
    QTextEdit, QTableWidget, QTableWidgetItem, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from trading_strategy import TradingStrategy
from blockchain_sync import BlockchainSync
from network_interface import NetworkInterface
from wallet import Wallet
from security import Security
from performance_manager import PerformanceManager

import qasync

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bollinger Trading Node")
        self.setGeometry(100, 100, 800, 600)

        self.security = Security()
        self.wallet = Wallet(self.security)
        self.performance_manager = PerformanceManager(self.wallet, node_name="Bollinger")
        self.network_interface = NetworkInterface(self.wallet, self.security, self.performance_manager)
        self.blockchain_sync = BlockchainSync(self.wallet, self.network_interface)
        self.trading_strategy = TradingStrategy(self.wallet, self.network_interface, self.performance_manager)

        self.other_node_url = "http://<SMA_IP>:<PORT>/get_performance_data"  # SMA node perf endpoint

        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Dashboard Tab
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.dashboard_layout = QVBoxLayout()
        self.dashboard_tab.setLayout(self.dashboard_layout)

        # Welcome label
        self.welcome_label = QLabel("Welcome to the Bollinger Trading Node!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.dashboard_layout.addWidget(self.welcome_label)

        # Portfolio Summary
        self.portfolio_label = QLabel("Portfolio Summary:")
        self.portfolio_label.setStyleSheet("font-size: 16px;")
        self.portfolio_text = QTextEdit()
        self.portfolio_text.setReadOnly(True)
        self.dashboard_layout.addWidget(self.portfolio_label)
        self.dashboard_layout.addWidget(self.portfolio_text)

        # Performance Metrics Display
        self.metrics_label = QLabel("Performance Metrics:")
        self.metrics_label.setStyleSheet("font-size:16px; font-weight:bold;")
        self.dashboard_layout.addWidget(self.metrics_label)
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.dashboard_layout.addWidget(self.metrics_text)

        # Comparison with other node
        self.compare_label = QLabel("Comparison with SMA Node:")
        self.compare_label.setStyleSheet("font-size:16px; font-weight:bold;")
        self.dashboard_layout.addWidget(self.compare_label)
        self.compare_text = QTextEdit()
        self.compare_text.setReadOnly(True)
        self.dashboard_layout.addWidget(self.compare_text)

        # Control Buttons
        self.control_layout = QHBoxLayout()
        self.dashboard_layout.addLayout(self.control_layout)

        self.start_button = QPushButton("Start Trading")
        self.start_button.clicked.connect(self.start_trading)
        self.control_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause Trading")
        self.pause_button.clicked.connect(self.pause_trading)
        self.pause_button.setEnabled(False)
        self.control_layout.addWidget(self.pause_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.control_layout.addWidget(self.exit_button)

        # Trade History Tab
        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, "Trade History")
        self.history_layout = QVBoxLayout()
        self.history_tab.setLayout(self.history_layout)

        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(6)
        self.trade_table.setHorizontalHeaderLabels(["Timestamp", "Type", "Symbol", "Quantity", "Price", "Total"])
        self.history_layout.addWidget(self.trade_table)

        # Initial Deposit Dialog
        self.get_initial_deposit_task = asyncio.ensure_future(self.get_initial_deposit())

        # Setup timer to fetch other node data every 30 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: asyncio.ensure_future(self.fetch_other_node_data()))
        self.timer.start(30000)

        self.trading_task = None
        self.blockchain_task = None

    async def get_initial_deposit(self):
        deposit, ok = await self.async_get_double_input(
            "Initial Deposit",
            "Enter initial deposit amount:",
            min=0.0,
            max=1e12,
            decimals=2
        )
        if ok:
            self.wallet.deposit(deposit)
            self.performance_manager.set_initial_deposit(deposit)
            QMessageBox.information(self, "Deposit", f"Deposited ${deposit:,.2f} into your wallet.")
            self.update_portfolio_display()
        else:
            sys.exit()

    async def async_get_double_input(self, title, label, min=0.0, max=1e12, decimals=2):
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def _on_finished(result):
            value, ok = result
            future.set_result((value, ok))

        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setInputMode(QInputDialog.DoubleInput)
        dialog.setDoubleMinimum(min)
        dialog.setDoubleMaximum(max)
        dialog.setDoubleDecimals(decimals)
        dialog.accepted.connect(lambda: _on_finished((dialog.doubleValue(), True)))
        dialog.rejected.connect(lambda: _on_finished((None, False)))
        dialog.show()
        return await future

    def start_trading(self):
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.trading_task = asyncio.create_task(self.trading_strategy.start_trading(self.handle_update))
        self.blockchain_task = asyncio.create_task(self.blockchain_sync.sync_with_ledger_manager())
        asyncio.create_task(self.network_interface.start_api_server())

    def pause_trading(self):
        if self.trading_task and not self.trading_task.cancelled():
            self.trading_task.cancel()
            self.trading_task = None
            self.pause_button.setEnabled(False)
            self.start_button.setEnabled(True)
            QMessageBox.information(self, "Trading Paused", "Trading has been paused.")

    def handle_update(self, data):
        self.update_portfolio_display()
        if data.get('trade'):
            self.add_trade_to_history(data['trade'])

    def update_portfolio_display(self):
        balance = self.wallet.get_balance()
        assets = self.wallet.get_assets()
        text = f"Wallet Balance: ${balance:,.2f}\nAssets:\n"
        for symbol, quantity in assets.items():
            text += f"  {symbol}: {quantity:.4f}\n"
        self.portfolio_text.setText(text)
        self.update_performance_display()

    def update_performance_display(self):
        perf_data = self.performance_manager.get_performance_data()
        text = (
            f"Node Name: {perf_data['node_name']}\n"
            f"Initial Deposit: ${perf_data['initial_deposit']:.2f}\n"
            f"Additional Deposits: ${perf_data['additional_deposits']:.2f}\n"
            f"Trades Executed: {perf_data['trades_executed']}\n"
            f"Total Profit/Loss: ${perf_data['total_profit_loss']:.2f}\n"
            f"Current Portfolio Value: ${perf_data['current_portfolio_value']:.2f}\n"
            f"ROI Since Start: {perf_data['roi_since_start']*100:.2f}%\n"
        )
        if perf_data['best_trade']:
            text += f"Best Trade: {perf_data['best_trade']['type']} {perf_data['best_trade']['symbol']} Profit: ${perf_data['best_trade']['profit']:.2f}\n"
        if perf_data['worst_trade']:
            text += f"Worst Trade: {perf_data['worst_trade']['type']} {perf_data['worst_trade']['symbol']} Profit: ${perf_data['worst_trade']['profit']:.2f}\n"
        self.metrics_text.setText(text)

    def add_trade_to_history(self, trade):
        row = self.trade_table.rowCount()
        self.trade_table.insertRow(row)
        self.trade_table.setItem(row, 0, QTableWidgetItem(trade['timestamp']))
        self.trade_table.setItem(row, 1, QTableWidgetItem(trade['type']))
        self.trade_table.setItem(row, 2, QTableWidgetItem(trade['symbol']))
        self.trade_table.setItem(row, 3, QTableWidgetItem(f"{trade['quantity']:.4f}"))
        self.trade_table.setItem(row, 4, QTableWidgetItem(f"${trade['price']:,.2f}"))
        self.trade_table.setItem(row, 5, QTableWidgetItem(f"${trade['total']:,.2f}"))

    async def fetch_other_node_data(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.other_node_url) as resp:
                    other_data = await resp.json()
                    self.update_comparison_display(other_data)
            except Exception as e:
                self.compare_text.setText("Unable to fetch SMA node data.")

    def update_comparison_display(self, other_data):
        my_data = self.performance_manager.get_performance_data()
        text = "Comparing Bollinger to SMA Node:\n\n"
        text += f"Bollinger ROI: {my_data['roi_since_start']*100:.2f}% vs SMA ROI: {other_data['roi_since_start']*100:.2f}%\n"
        text += f"Bollinger Trades: {my_data['trades_executed']} vs SMA Trades: {other_data['trades_executed']}\n"
        text += f"Bollinger P/L: ${my_data['total_profit_loss']:.2f} vs SMA P/L: ${other_data['total_profit_loss']:.2f}\n"
        self.compare_text.setText(text)

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit")
        msg.setText("Do you want to delete your wallet and performance data?")
        msg.setIcon(QMessageBox.Question)
        cancel_button = msg.addButton("Cancel", QMessageBox.RejectRole)
        no_button = msg.addButton("No", QMessageBox.NoRole)
        yes_button = msg.addButton("Yes", QMessageBox.YesRole)

        msg.exec_()
        clicked_button = msg.clickedButton()
        if clicked_button == cancel_button:
            event.ignore()
            return
        elif clicked_button == yes_button:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            wallet_file = os.path.join(current_dir, "wallet.json")
            perf_file = os.path.join(current_dir, "performance_bollinger.json")

            if os.path.exists(wallet_file):
                os.remove(wallet_file)

            if os.path.exists(perf_file):
                os.remove(perf_file)

        if self.trading_task and not self.trading_task.cancelled():
            self.trading_task.cancel()
        if self.blockchain_task and not self.blockchain_task.cancelled():
            self.blockchain_task.cancel()
        asyncio.create_task(self.network_interface.close())
        event.accept()


def run_app():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()