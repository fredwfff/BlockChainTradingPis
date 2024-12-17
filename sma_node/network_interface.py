"""
network_interface.py (SMA Node)

This module manages the communication between the SMA trading node and external systems. It serves as an API server for the node, handles transactions, and fetches performance data.

Core Features:
1. **API Server**:
   - Starts two HTTP endpoints: one for ledger operations (port 8080) and another for performance data (port 8081).
   - Handles incoming HTTP requests for various operations like fetching performance metrics or blockchain data.

2. **Transaction Submission**:
   - Submits trade transactions (buy/sell) to the ledger manager by signing and sending them over HTTP.

3. **Data Synchronisation**:
   - Fetches performance metrics from peer nodes (e.g., the Bollinger Node) for comparative analysis.
   - Allows external systems to retrieve the current node's performance metrics.

Key Methods:
- `start_api_server()`: Starts the API server on ports 8080 and 8081.
- `submit_transaction()`: Submits a transaction to the ledger manager after signing it with the node's private key.
- `fetch_other_node_data()`: Retrieves performance data from another node.

Handlers:
- `handle_get_performance_data`: Returns the performance data for the SMA node.
- Other handlers, such as `handle_get_balance` and `handle_submit_transaction`, respond to external requests but are simplified for this node.

This module ensures smooth communication between the SMA node, the ledger manager, and other nodes in the blockchain trading system.
"""

import aiohttp
from aiohttp import web
import asyncio
import socket
import traceback

class NetworkInterface:
    def __init__(self, wallet, security, performance_manager):
        self.wallet = wallet
        self.security = security
        self.performance_manager = performance_manager
        self.session = None
        self.ledger_manager_url = 'http://<LEDGER_MANAGER_IP:PORT>'
        self.other_node_url = "http://<BOLLINGER_IP:PORT>/get_performance_data"  # Bollinger Node IP
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        self.app.add_routes([
            web.get('/', self.handle_test_endpoint),
            web.post('/submit_transaction', self.handle_submit_transaction),
            web.get('/get_blockchain', self.handle_get_blockchain),
            web.get('/get_balance', self.handle_get_balance),
            web.post('/execute_smart_contract', self.handle_execute_smart_contract),
            web.get('/get_performance_data', self.handle_get_performance_data)
        ])

    async def start_api_server(self):
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            # Primary site for ledger operations
            site = web.TCPSite(runner, '0.0.0.0', 8080)
            await site.start()

            # Start a second site for performance data
            site2 = web.TCPSite(runner, '0.0.0.0', 8081)
            await site2.start()

            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            print(f"Error starting API server: {e}")
            traceback.print_exc()

    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def submit_transaction(self, trade_type, symbol, quantity, price):
        try:
            transaction_data = {
                'transaction_id': self.security.generate_transaction_id(),
                'sender_public_key': self.security.get_public_key_pem(),
                'trade_type': trade_type,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'timestamp': int(asyncio.get_event_loop().time())
            }
            transaction_string = self.security.transaction_to_string(transaction_data)
            signature = self.security.sign_data(transaction_string)
            transaction_data['signature'] = signature
            payload = {'transaction': transaction_data}
            url = f'{self.ledger_manager_url}/submit_transaction'

            session = await self.get_session()
            async with session.post(url, json=payload) as response:
                _ = await response.json()
        except Exception as e:
            print(f"Error submitting transaction: {e}")
            traceback.print_exc()

    async def fetch_other_node_data(self):
        try:
            session = await self.get_session()
            async with session.get(self.other_node_url) as resp:
                if resp.status == 200:
                    other_data = await resp.json()
                    return other_data
                else:
                    print(f"Failed to fetch performance data from Bollinger Node: {resp.status}")
                    return None
        except Exception as e:
            print(f"Error fetching other node data: {e}")
            traceback.print_exc()
            return None

    async def close(self):
        if self.session is not None:
            await self.session.close()

    async def handle_test_endpoint(self, request):
        return web.Response(text="SMA Node Interface Running.")

    async def handle_submit_transaction(self, request):
        return web.json_response({'status': 'error', 'reason': 'Direct submission not allowed here'})

    async def handle_get_blockchain(self, request):
        return web.json_response({'status': 'success', 'block': None})

    async def handle_get_balance(self, request):
        return web.json_response({'status': 'success', 'balance': self.wallet.get_balance()})

    async def handle_execute_smart_contract(self, request):
        return web.json_response({'status': 'error', 'reason': 'No SC here'})

    async def handle_get_performance_data(self, request):
        perf_data = self.performance_manager.get_performance_data()
        return web.json_response(perf_data)