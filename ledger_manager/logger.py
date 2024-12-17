"""
The `logger.py` file defines a logging utility for the Ledger Manager. 
This utility enables logging of events, transactions, and errors at various levels (INFO, DEBUG, ERROR, etc.).

Key functionalities:
1. **log_event**: Logs general events or system activities.
2. **log_transaction**: Logs details of a transaction, typically when it is added or processed.
3. **log_error**: Logs errors or exceptions encountered during execution.

The logger writes logs to both the terminal (console) and a file (`ledger_manager.log`) for persistence.
It uses Python's `logging` module with a specified format to standardise log entries.
"""
import logging

class Logger:
    def __init__(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[
                logging.FileHandler("ledger_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LedgerManager')

    def log_event(self, message, level="INFO"):
        if level == "DEBUG":
            self.logger.debug(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def log_transaction(self, transaction):
        self.logger.info(f"Transaction logged: {transaction}")

    def log_error(self, error):
        self.logger.error(error)
