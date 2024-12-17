# The SmartContractExecutor class is responsible for executing smart contracts that are included
# in transactions. Smart contracts are self-executing scripts that define the terms of a contract 
# and can automate certain actions within the blockchain.

# Key functionalities:
# 1. **execute_contract**: Executes the smart contract code embedded in a transaction. The contract 
#    code is executed in a restricted environment for security reasons, preventing malicious actions.
# 2. **allowed_builtins**: Defines a list of safe built-in functions that are available to the 
#    smart contract code during execution. This is done to ensure the contract code does not 
#    access potentially harmful functions or manipulate the environment.

# The Smart Contract Executor works by using a special Python execution environment to run 
# user-provided contract code. This allows blockchain applications to create dynamic and 
# customizable functionality directly within the blockchain's structure.

import json
import threading

class SmartContractExecutor:
    def __init__(self, blockchain, logger):
        self.blockchain = blockchain
        self.logger = logger
        self.lock = threading.Lock()

    def execute_contract(self, transaction):
        contract_code = transaction.get('contract_code')
        if not contract_code:
            return None  # No smart contract to execute

        # Define a restricted execution environment
        allowed_builtins = {
            '__builtins__': {
                'range': range,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'dict': dict,
                'list': list,
                'print': print,
            }
        }

        # Prepare the contract execution context
        contract_globals = {}
        contract_locals = {
            'blockchain': self.blockchain,
            'transaction': transaction
        }

        try:
            with self.lock:
                exec(contract_code, allowed_builtins, contract_locals)
            contract_result = contract_locals.get('result', None)
            self.logger.log_event(f"Smart contract executed successfully: {transaction['transaction_id']}", "INFO")
            return contract_result
        except Exception as e:
            self.logger.log_error(f"Smart contract execution failed: {str(e)}")
            return None
