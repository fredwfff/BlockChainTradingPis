"""
main.py

This is the entry point of the Bollinger trading node application. It launches the graphical user interface (GUI),
which allows the user to interact with and monitor the trading node. The GUI provides:
1. Portfolio summaries and metrics (profit/loss, ROI, trades).
2. Trade history and real-time performance updates.
3. Synchronisation status with the blockchain ledger.
4. Comparison of performance with other nodes (e.g., SMA node).

**How It Works**:
- The `run_app()` function (imported from `gui.py`) starts the Qt-based GUI loop.
- The user interacts with the application through the GUI, triggering trading operations and viewing performance metrics.

Usage:
Run this file to start the Bollinger trading node:
    `python main.py`

Dependencies:
- GUI components are handled in `gui.py`.
- Other modules such as `trading_strategy`, `performance_manager`, and `blockchain_sync` are integrated into the GUI.

"""

import sys
from gui import run_app

if __name__ == '__main__':
    run_app()
