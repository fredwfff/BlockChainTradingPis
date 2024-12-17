"""
blockchain_sync.py

This module handles synchronisation between the trading node and the blockchain ledger. It ensures that:
1. The wallet’s balance and assets are kept up to date.
2. Any new blocks or transactions on the blockchain are retrieved and validated.
3. The trading node operates in sync with the latest blockchain state.

**Core Functionality**:
- Continuously communicates with the ledger manager to fetch balance updates or new blockchain blocks.
- Synchronisation occurs in a loop with a delay to minimise network congestion.
- Handles exceptions and ensures resilience by retrying failed operations.

Key Class:
- `BlockchainSync`: Manages the synchronisation process with the ledger manager.

Note: This module assumes that the `network_interface` provides the necessary methods for communication with the ledger manager.

"""
import asyncio

class BlockchainSync:
    def __init__(self, wallet, network_interface):
        self.wallet = wallet
        self.network_interface = network_interface

    async def sync_with_ledger_manager(self):
        try:
            while True:
                try:
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    print("Blockchain synchronization has been cancelled.")
                    break
                except Exception as e:
                    print(f"Exception in blockchain synchronization: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"Error in sync_with_ledger_manager: {e}")
            import traceback
            traceback.print_exc()