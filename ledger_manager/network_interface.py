"""
The `network_interface.py` file facilitates communication between the Ledger Manager 
and external clients or nodes. It handles REST API requests for submitting transactions, 
retrieving the blockchain state, checking balances, and executing smart contracts.

Key functionalities:
1. **API Server**: Starts an asynchronous web server using `aiohttp` to listen for 
   incoming HTTP requests.
2. **Route Handlers**:
    - `/submit_transaction`: Accepts transactions, validates them, and adds them to the transaction pool.
    - `/get_blockchain`: Returns the latest blockchain data.
    - `/get_balance`: Returns the balance for a given public key.
    - `/execute_smart_contract`: Executes smart contracts embedded in transactions.
3. **Discovery Listener**: Listens for discovery messages via UDP, responding to clients 
   looking for the Ledger Manager.

The `start_api_server` method runs the server and maintains it indefinitely. The server 
operates on port `8080` by default.
"""
import aiohttp
from aiohttp import web
import asyncio
import socket
import traceback

class NetworkInterface:
    def __init__(self, validator, transaction_pool, blockchain, security, logger, smart_contract_executor):
        self.validator = validator
        self.transaction_pool = transaction_pool
        self.blockchain = blockchain
        self.security = security
        self.logger = logger
        self.smart_contract_executor = smart_contract_executor
        self.discovery_port = 9999
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.add_routes([
            web.get('/', self.handle_test_endpoint),
            web.post('/submit_transaction', self.handle_submit_transaction),
            web.get('/get_blockchain', self.handle_get_blockchain),
            web.get('/get_balance', self.handle_get_balance),
            web.post('/execute_smart_contract', self.handle_execute_smart_contract),
        ])

    async def start_api_server(self):
        try:
            print("Setting up API server...")
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 8080)
            await site.start()
            self.logger.log_event("API server started", "INFO")
            print("API server setup complete.")

            asyncio.create_task(self.start_discovery_listener())
            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            self.logger.log_error(f"Error starting API server: {e}")
            print(f"Error starting API server: {e}")
            traceback.print_exc()

    async def start_discovery_listener(self):
        try:
            loop = asyncio.get_event_loop()
            await loop.create_datagram_endpoint(
                lambda: DiscoveryProtocol(self.logger),
                local_addr=('0.0.0.0', self.discovery_port)
            )
            self.logger.log_event("Started Ledger Manager discovery listener", "INFO")
        except Exception as e:
            self.logger.log_error(f"Error starting discovery listener: {e}")
            traceback.print_exc()

    async def handle_test_endpoint(self, request):
        return web.Response(text="Ledger Manager is running.")

    async def handle_submit_transaction(self, request):
        try:
            self.logger.log_event("Received transaction submission request", "DEBUG")
            data = await request.json()
            transaction = data['transaction']
            is_valid, reason = self.validator.validate_transaction(transaction)
            if is_valid:
                self.transaction_pool.add_transaction(transaction)
                self.logger.log_event(f"Transaction accepted: {transaction['transaction_id']}", "INFO")
                return web.json_response({'status': 'success', 'message': 'Transaction accepted'})
            else:
                self.logger.log_event(f"Transaction rejected: {transaction['transaction_id']} - {reason}", "WARNING")
                return web.json_response({'status': 'error', 'reason': reason})
        except Exception as e:
            self.logger.log_error(f"Error in handle_submit_transaction: {str(e)}")
            return web.json_response({'status': 'error', 'reason': str(e)})

    async def handle_get_blockchain(self, request):
        try:
            latest_block = self.blockchain.get_latest_block()
            if latest_block is None:
                return web.json_response({'status': 'success', 'block': None})
            return web.json_response({'status': 'success', 'block': latest_block})
        except Exception as e:
            self.logger.log_error(f"Error in handle_get_blockchain: {str(e)}")
            return web.json_response({'status': 'error', 'reason': str(e)})

    async def handle_get_balance(self, request):
        try:
            public_key = request.query.get('public_key')
            if not public_key:
                return web.json_response({'status': 'error', 'reason': 'public_key parameter is missing'})
            balance = self.blockchain.get_balance(public_key)
            return web.json_response({'status': 'success', 'balance': balance})
        except Exception as e:
            self.logger.log_error(f"Error in handle_get_balance: {str(e)}")
            return web.json_response({'status': 'error', 'reason': str(e)})

    async def handle_execute_smart_contract(self, request):
        try:
            data = await request.json()
            transaction = data['transaction']
            result = self.smart_contract_executor.execute_contract(transaction)
            if result is not None:
                return web.json_response({'status': 'success', 'result': result})
            else:
                return web.json_response({'status': 'error', 'reason': 'Contract execution failed'})
        except Exception as e:
            self.logger.log_error(f"Error in handle_execute_smart_contract: {str(e)}")
            return web.json_response({'status': 'error', 'reason': str(e)})

class DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, logger):
        self.logger = logger

    def datagram_received(self, data, addr):
        message = data.decode('utf-8')
        if message == 'DISCOVER_LEDGER_MANAGER':
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto('LEDGER_MANAGER_HERE'.encode('utf-8'), addr)
            sock.close()
