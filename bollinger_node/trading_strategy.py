"""
trading_strategy.py

This module implements the Bollinger-based trading strategy, which evaluates financial assets using Bollinger Bands to make buy or sell decisions. 
It automates trading processes and manages portfolio value dynamically.

Core Features:
1. **Bollinger Bands**:
   - Bollinger Bands consist of an upper, middle (moving average), and lower band.
   - The strategy generates a "buy" signal when the asset price crosses below the lower band and a "sell" signal when it exceeds the upper band.

2. **Asynchronous Trading**:
   - Fetches real-time historical prices using the Yahoo Finance API.
   - Processes financial data, generates trading signals, and executes trades asynchronously.

3. **Portfolio Management**:
   - Automates buying and selling of assets.
   - Updates wallet balance, asset holdings, and performance metrics after each trade.

Key Methods:
- `generate_signal()`: Analyses price data to generate buy or sell signals.
- `buy_decision()` and `sell_decision()`: Execute trades based on signals.
- `calculate_portfolio_value()`: Updates the total portfolio value.

The module integrates tightly with the `wallet` and `performance_manager` to track trades and ensure the trading system remains efficient and reactive to market conditions.
"""

import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time as dt_time
import functools
import traceback

class TradingStrategy:
    def __init__(self, wallet, network_interface, performance_manager):
        self.wallet = wallet
        self.network_interface = network_interface
        self.performance_manager = performance_manager
        self.assets_symbols = ['NVDA', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD', 'SOL-USD']
        self.stock_symbols = ['NVDA', 'MSFT', 'GOOGL']
        self.crypto_symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        self.market_open = dt_time(14, 30)
        self.market_close = dt_time(21, 0)
        self.min_data_points = 4
        self.ma_window = 3
        self.std_multiplier = 0.5

    async def start_trading(self, handle_update):
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
                    else:
                        pass

                # Update portfolio value
                portfolio_value = await self.calculate_portfolio_value()
                self.performance_manager.update_portfolio_value(portfolio_value)

                await asyncio.sleep(60)
            except asyncio.CancelledError:
                print("Trading loop cancelled.")
                break
            except Exception as e:
                print(f"Exception in trading loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(5)

    async def get_historical_prices(self):
        try:
            current_time = datetime.utcnow().time()
            symbols_to_fetch = self.crypto_symbols.copy()
            if self.market_open <= current_time <= self.market_close:
                symbols_to_fetch.extend(self.stock_symbols)

            data = {}
            loop = asyncio.get_event_loop()

            for symbol in symbols_to_fetch:
                try:
                    ticker = yf.Ticker(symbol)
                    df = await loop.run_in_executor(
                        None,
                        functools.partial(
                            ticker.history,
                            period='1d',
                            interval='1m',
                            auto_adjust=False,
                            actions=False,
                            prepost=False,
                        )
                    )
                    if df.empty or 'Close' not in df.columns:
                        continue
                    df['Symbol'] = symbol
                    df = df.dropna(subset=['Close'])
                    df = df.iloc[-self.min_data_points:]
                    data[symbol] = df
                except:
                    continue

            return data
        except:
            return None

    def generate_signal(self, df, symbol):
        try:
            if len(df) < self.min_data_points:
                return None

            df['MA'] = df['Close'].rolling(window=self.ma_window).mean()
            df['STD'] = df['Close'].rolling(window=self.ma_window).std()
            df['Upper'] = df['MA'] + (self.std_multiplier * df['STD'])
            df['Lower'] = df['MA'] - (self.std_multiplier * df['STD'])

            last_row = df.iloc[-1]
            if last_row[['Close','MA','STD','Upper','Lower']].isnull().any():
                return None

            last_close = last_row['Close']
            upper_band = last_row['Upper']
            lower_band = last_row['Lower']

            if last_close > upper_band:
                return 'sell'
            elif last_close < lower_band:
                return 'buy'
            else:
                return None
        except:
            return None

    async def buy_decision(self, symbol, df):
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
        try:
            assets = self.wallet.get_assets()
            if symbol not in assets or assets[symbol] <= 0:
                return None
            max_quantity = assets[symbol]
            price = df['Close'].iloc[-1]
            quantity = 0.5 * max_quantity
            quantity = round(quantity,4)
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

    async def execute_trade(self, trade_type, symbol, quantity, price):
        try:
            amount = quantity * price
            if trade_type == 'buy':
                if self.wallet.get_balance() >= amount:
                    self.wallet.update_balance(-amount)
                    self.wallet.update_asset(symbol, quantity)
                    await self.network_interface.submit_transaction(trade_type, symbol, quantity, price)
            else:
                if self.wallet.get_assets().get(symbol,0) >= quantity:
                    self.wallet.update_balance(amount)
                    self.wallet.update_asset(symbol, -quantity)
                    await self.network_interface.submit_transaction(trade_type, symbol, quantity, price)
        except:
            pass

    async def calculate_portfolio_value(self):
        try:
            total_value = self.wallet.get_balance()
            assets = self.wallet.get_assets()
            if not assets:
                return total_value
            loop = asyncio.get_event_loop()
            tasks = [self.get_current_price(symbol, loop) for symbol in assets.keys()]
            results = await asyncio.gather(*tasks)
            current_prices = dict(zip(assets.keys(), results))
            for symbol,quantity in assets.items():
                price = current_prices.get(symbol,0)
                total_value += quantity*price
            return total_value
        except:
            return self.wallet.get_balance()

    async def get_current_price(self, symbol, loop):
        try:
            ticker = yf.Ticker(symbol)
            df = await loop.run_in_executor(
                None,
                functools.partial(
                    ticker.history,
                    period='1d',
                    interval='1m',
                    auto_adjust=False,
                    actions=False,
                    prepost=False,
                )
            )
            if not df.empty:
                return df['Close'].iloc[-1]
            else:
                return 0
        except:
            return 0