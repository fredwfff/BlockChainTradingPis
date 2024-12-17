"""
The `main.py` file serves as the entry point for running the Ledger Manager. It 
initialises all components of the system and starts the core services: an API server 
and the block creation loop.

Key functionalities:
1. **Initialisation**: Loads and connects all modules, including blockchain, transaction 
   pool, validator, consensus mechanism, and the network interface.
2. **API Server**: Starts the web server to listen for incoming API requests for 
   transactions, blockchain data, and balances.
3. **Block Creation Loop**: Periodically creates new blocks using transactions from 
   the pool and adds them to the blockchain.
4. **Error Handling**: Logs errors and ensures the system continues running smoothly 
   during unexpected failures.
"""
import asyncio
from blockchain import Blockchain
from transaction_pool import TransactionPool
from validator import Validator
from network_interface import NetworkInterface
from security import Security
from logger import Logger
from consensus import Consensus
from block_generator import BlockGenerator
from smart_contract_executor import SmartContractExecutor
import traceback

async def main():
    try:
        print("Initialising Ledger Manager modules...")
        logger = Logger()
        security = Security()
        blockchain = Blockchain(logger)
        transaction_pool = TransactionPool(logger)
        validator = Validator(blockchain, logger, security)
        smart_contract_executor = SmartContractExecutor(blockchain, logger)
        consensus = Consensus(security, logger)
        block_generator = BlockGenerator(transaction_pool, blockchain, consensus, logger, smart_contract_executor)
        network_interface = NetworkInterface(
            validator, transaction_pool, blockchain, security, logger, smart_contract_executor
        )
        print("Modules initialised.")

        api_server_task = asyncio.create_task(network_interface.start_api_server())
        logger.log_event("Ledger Manager is running.", "INFO")
        print("API server started.")

        block_creation_task = asyncio.create_task(block_creation_loop(block_generator, transaction_pool, logger))
        print("Block creation loop started.")

        await asyncio.gather(api_server_task, block_creation_task)
    except Exception as e:
        logger.log_error(f"Error in main: {e}")
        traceback.print_exc()

async def block_creation_loop(block_generator, transaction_pool, logger):
    while True:
        try:
            block = block_generator.create_block()
            if block:
                transaction_pool.remove_transactions(block['body']['transactions'])
            await asyncio.sleep(10)
        except Exception as e:
            logger.log_error(f"Error in block creation loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
