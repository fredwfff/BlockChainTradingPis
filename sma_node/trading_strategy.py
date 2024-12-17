"""
trading_strategy.py (SMA Node)

This module implements the **Simple Moving Average (SMA) trading strategy** for the SMA trading node. 
The strategy uses financial data fetched from Yahoo Finance to generate **buy** and **sell** signals 
based on short-term and long-term SMA crossovers. The module performs the following key functions:

1. Fetch historical price data for a set of predefined assets (stocks and cryptocurrencies).
2. Calculate short-term and long-term SMAs to detect **crossover signals**:
   - **Buy Signal**: Short SMA crosses above the long SMA.
   - **Sell Signal**: Short SMA crosses below the long SMA.
3. Execute trades (buy/sell) based on the generated signals.
4. Track and record the trades using the `PerformanceManager`.
5. Update the current portfolio value asynchronously by calculating the market value of all assets.

The trading strategy runs continuously in an event loop and updates the system every 60 seconds. 
It interacts with the **wallet** to check balances and update holdings, and communicates with the 
**network interface** to submit transactions to the ledger manager.

Classes:
- TradingStrategy: Implements the core trading logic, including fetching data, generating signals, 
  executing trades, and updating performance metrics.

Key Concepts:
- **SMA (Simple Moving Average)**: A moving average calculated over a specified time window. 
  Short-term and long-term SMAs are compared to detect price trend changes.
- **Event Loop**: The strategy uses asynchronous programming to continuously fetch data and process trades.

"""

import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import functools
import traceback

class TradingStrategy:
    def __init__(self, wallet, network_interface, performance_manager):
        """
        Initialise the TradingStrategy class.

        Args:
            wallet: Manages balances and asset holdings.
            network_interface: Handles communication with the ledger manager.
            performance_manager: Tracks and evaluates trade performance.
        """
        self.wallet = wallet
        self.network_interface = network_interface
        self.performance_manager = performance_manager
        self.assets_symbols = ['NVDA', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD', 'SOL-USD']
        self.short_sma_window = 2  # Short-term SMA window
        self.long_sma_window = 3   # Long-term SMA window
        self.min_data_points = 5   # Minimum data points required to calculate SMAs

    async def start_trading(self, handle_update):
        """
        Starts the trading loop, which fetches data, generates signals, executes trades, 
        and updates portfolio performance.

        Args:
            handle_update: A callback function to update the GUI or log new trades.
        """
        while True:
            try:
                data = await self.get_historical_prices()
                if not data:
                    await asyncio.sleep(5)
                    continue

                for symbol, df in data.items():
                    signal = self.generate_signal(df, symbol)
                    if signal == 'buy':
                        trade = await self.buy_decision(symbol, df)
                        if trade:
                            self.performance_manager.record_trade('Buy', symbol, trade['quantity'], trade['price'], trade['total'])
                            handle_update({'trade': trade})
                    elif signal == 'sell':
                        trade = await self.sell_decision(symbol, df)
                        if trade:
                            self.performance_manager.record_trade('Sell', symbol, trade['quantity'], trade['price'], trade['total'])
                            handle_update({'trade': trade})

                # Update portfolio value
                portfolio_value = await self.calculate_portfolio_value()
                self.performance_manager.update_portfolio_value(portfolio_value)
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def get_historical_prices(self):
        """
        Fetch historical price data for the defined assets using Yahoo Finance API.

        Returns:
            A dictionary where keys are asset symbols and values are DataFrames containing price data.
        """
        try:
            symbols_to_fetch = self.assets_symbols.copy()
            data = {}
            loop = asyncio.get_event_loop()

            for symbol in symbols_to_fetch:
                try:
                    ticker = yf.Ticker(symbol)
                    df = await loop.run_in_executor(
                        None,
                        functools.partial(
                            ticker.history,
                            period='5d',
                            interval='1m',
                            auto_adjust=False,
                            actions=False,
                            prepost=True
                        )
                    )
                    if df.empty or 'Close' not in df.columns:
                        continue
                    df = df.dropna(subset=['Close'])
                    if len(df) < self.min_data_points:
                        continue
                    df = df.iloc[-self.min_data_points:]
                    df['Symbol'] = symbol
                    data[symbol] = df
                except:
                    continue
            return data
        except:
            return None

    def generate_signal(self, df, symbol):
        """
        Generate a buy or sell signal based on SMA crossover logic.

        Args:
            df: A DataFrame containing historical price data.
            symbol: The asset symbol.

        Returns:
            A string representing the signal: 'buy', 'sell', or None.
        """
        try:
            if len(df) < self.min_data_points:
                return None

            # Calculate short-term and long-term SMAs
            df['ShortSMA'] = df['Close'].rolling(window=self.short_sma_window).mean()
            df['LongSMA'] = df['Close'].rolling(window=self.long_sma_window).mean()

            if len(df) < self.long_sma_window:
                return None

            short_sma_prev = df['ShortSMA'].iloc[-2]
            long_sma_prev = df['LongSMA'].iloc[-2]
            short_sma_now = df['ShortSMA'].iloc[-1]
            long_sma_now = df['LongSMA'].iloc[-1]

            if short_sma_now > long_sma_now and short_sma_prev <= long_sma_prev:
                return 'buy'
            if short_sma_now < long_sma_now and short_sma_prev >= long_sma_prev:
                return 'sell'
            return None
        except:
            return None

    async def buy_decision(self, symbol, df):
        """
        Make a buy decision based on the available balance.

        Args:
            symbol: The asset symbol.
            df: The DataFrame containing price data.

        Returns:
            A dictionary representing the trade details.
        """
        try:
            price = df['Close'].iloc[-1]
            balance = self.wallet.get_balance()
            if balance <= 0:
                return None
            quantity = (0.1 * balance) / price
            quantity = round(quantity, 4)
            cost = quantity * price
            await self.execute_trade('buy', symbol, quantity, price)
            return {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'Buy',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'total': cost
            }
        except:
            return None

    async def sell_decision(self, symbol, df):
        """
        Make a sell decision based on the available assets.

        Args:
            symbol: The asset symbol.
            df: The DataFrame containing price data.

        Returns:
            A dictionary representing the trade details.
        """
        try:
            assets = self.wallet.get_assets()
            if symbol not in assets or assets[symbol] <= 0:
                return None
            max_quantity = assets[symbol]
            price = df['Close'].iloc[-1]
            quantity = 0.5 * max_quantity
            quantity = round(quantity, 4)
            total_value = quantity * price
            await self.execute_trade('sell', symbol, quantity, price)
            return {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'Sell',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'total': total_value
            }
        except:
            return None

    async def execute_tra
