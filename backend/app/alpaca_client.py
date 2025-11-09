"""
Alpaca API Client for trading and market data operations
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
from config import Config


class AlpacaClient:
    """Wrapper for Alpaca API operations"""

    def __init__(self):
        """Initialize Alpaca clients"""
        self.trading_client = TradingClient(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            paper=Config.is_paper_trading()
        )

        self.data_client = StockHistoricalDataClient(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY
        )

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {
                'account_number': account.account_number,
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'last_equity': float(account.last_equity),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'transfers_blocked': account.transfers_blocked,
                'account_blocked': account.account_blocked,
                'daytrade_count': account.daytrade_count,
                'status': account.status
            }
        except Exception as e:
            raise Exception(f"Failed to get account info: {str(e)}")

    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'side': pos.side
                }
                for pos in positions
            ]
        except Exception as e:
            raise Exception(f"Failed to get positions: {str(e)}")

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a specific symbol"""
        try:
            position = self.trading_client.get_open_position(symbol)
            return {
                'symbol': position.symbol,
                'qty': float(position.qty),
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'side': position.side
            }
        except Exception:
            return None

    def get_historical_bars(
        self,
        symbols: List[str],
        days: int = 60,
        timeframe: str = '1Day'
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical bar data for symbols

        Args:
            symbols: List of stock symbols
            days: Number of days of historical data
            timeframe: Bar timeframe (1Min, 5Min, 1Hour, 1Day)

        Returns:
            Dictionary mapping symbols to DataFrames with OHLCV data
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days)

            # Map timeframe string to TimeFrame enum
            timeframe_map = {
                '1Min': TimeFrame.Minute,
                '5Min': TimeFrame(5, 'Min'),
                '15Min': TimeFrame(15, 'Min'),
                '1Hour': TimeFrame.Hour,
                '1Day': TimeFrame.Day
            }

            request_params = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe_map.get(timeframe, TimeFrame.Day),
                start=start,
                end=end
            )

            bars = self.data_client.get_stock_bars(request_params)

            # Convert to dictionary of DataFrames
            result = {}
            for symbol in symbols:
                if symbol in bars.data:
                    df = pd.DataFrame([
                        {
                            'timestamp': bar.timestamp,
                            'open': float(bar.open),
                            'high': float(bar.high),
                            'low': float(bar.low),
                            'close': float(bar.close),
                            'volume': int(bar.volume)
                        }
                        for bar in bars.data[symbol]
                    ])
                    df.set_index('timestamp', inplace=True)
                    result[symbol] = df

            return result

        except Exception as e:
            raise Exception(f"Failed to get historical bars: {str(e)}")

    def get_latest_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get latest quote for symbols"""
        try:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbols)
            quotes = self.data_client.get_stock_latest_quote(request_params)

            result = {}
            for symbol, quote in quotes.items():
                result[symbol] = {
                    'bid_price': float(quote.bid_price),
                    'bid_size': int(quote.bid_size),
                    'ask_price': float(quote.ask_price),
                    'ask_size': int(quote.ask_size),
                    'timestamp': quote.timestamp
                }

            return result

        except Exception as e:
            raise Exception(f"Failed to get latest quotes: {str(e)}")

    def place_market_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = 'day'
    ) -> Dict:
        """
        Place a market order

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns:
            Order details
        """
        try:
            side_enum = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }

            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side_enum,
                time_in_force=tif_map.get(time_in_force.lower(), TimeInForce.DAY)
            )

            order = self.trading_client.submit_order(order_data)

            return {
                'id': str(order.id),
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'created_at': order.created_at,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
            }

        except Exception as e:
            raise Exception(f"Failed to place market order: {str(e)}")

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = 'day'
    ) -> Dict:
        """
        Place a limit order

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            limit_price: Limit price
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns:
            Order details
        """
        try:
            side_enum = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }

            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side_enum,
                time_in_force=tif_map.get(time_in_force.lower(), TimeInForce.DAY),
                limit_price=limit_price
            )

            order = self.trading_client.submit_order(order_data)

            return {
                'id': str(order.id),
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'limit_price': float(order.limit_price),
                'status': order.status.value,
                'created_at': order.created_at,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
            }

        except Exception as e:
            raise Exception(f"Failed to place limit order: {str(e)}")

    def get_orders(self, status: str = 'all') -> List[Dict]:
        """
        Get orders

        Args:
            status: 'open', 'closed', 'all'

        Returns:
            List of orders
        """
        try:
            status_map = {
                'open': QueryOrderStatus.OPEN,
                'closed': QueryOrderStatus.CLOSED,
                'all': QueryOrderStatus.ALL
            }

            request = GetOrdersRequest(
                status=status_map.get(status.lower(), QueryOrderStatus.ALL)
            )

            orders = self.trading_client.get_orders(filter=request)

            return [
                {
                    'id': str(order.id),
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side.value,
                    'type': order.type.value,
                    'status': order.status.value,
                    'created_at': order.created_at,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0
                }
                for order in orders
            ]

        except Exception as e:
            raise Exception(f"Failed to get orders: {str(e)}")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")

    def close_position(self, symbol: str, qty: Optional[float] = None) -> Dict:
        """
        Close a position (or partial position)

        Args:
            symbol: Stock symbol
            qty: Quantity to close (None = close all)

        Returns:
            Order details
        """
        try:
            if qty:
                order = self.trading_client.close_position(symbol, close_options={'qty': qty})
            else:
                order = self.trading_client.close_position(symbol)

            return {
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'status': order.status.value
            }

        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")
