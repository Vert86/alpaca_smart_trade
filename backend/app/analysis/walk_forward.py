"""
Walk-Forward Optimization Analysis
Uses rolling window optimization to test trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class WalkForwardOptimizer:
    """Walk-forward optimization for trading strategies"""

    def __init__(self, train_days: int = 30, test_days: int = 5):
        """
        Initialize walk-forward optimizer

        Args:
            train_days: Number of days for training/optimization window
            test_days: Number of days for testing/validation window
        """
        self.train_days = train_days
        self.test_days = test_days

    def optimize(self, df: pd.DataFrame) -> Dict:
        """
        Perform walk-forward optimization on a stock

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with optimization results and recommendations
        """
        if df is None or len(df) < self.train_days + self.test_days:
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'expected_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'optimal_params': {}
            }

        # Perform walk-forward optimization
        results = self._walk_forward_analysis(df)

        # Generate recommendation based on results
        recommendation = self._generate_recommendation(results)

        return {
            'recommendation': recommendation['action'],
            'confidence': round(recommendation['confidence'], 3),
            'expected_return': round(results['expected_return'], 4),
            'sharpe_ratio': round(results['sharpe_ratio'], 3),
            'win_rate': round(results['win_rate'], 3),
            'max_drawdown': round(results['max_drawdown'], 3),
            'avg_return': round(results['avg_return'], 4),
            'optimal_params': results['optimal_params'],
            'recent_performance': results['recent_performance']
        }

    def _walk_forward_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Perform walk-forward analysis

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Analysis results
        """
        # Calculate returns
        df = df.copy()
        df['returns'] = df['close'].pct_change()

        # Find optimal parameters on training window
        train_data = df.iloc[-(self.train_days + self.test_days):-self.test_days]
        optimal_params = self._optimize_parameters(train_data)

        # Test on out-of-sample data
        test_data = df.iloc[-self.test_days:]
        test_results = self._backtest_strategy(test_data, optimal_params)

        # Calculate overall performance metrics
        all_trades = test_results['trades']

        if len(all_trades) > 0:
            returns = [t['return'] for t in all_trades]
            expected_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (expected_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0
            win_rate = sum(1 for r in returns if r > 0) / len(returns)

            # Calculate max drawdown
            cumulative_returns = np.cumprod([1 + r for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(min(drawdown)) if len(drawdown) > 0 else 0.0
        else:
            expected_return = 0.0
            sharpe_ratio = 0.0
            win_rate = 0.0
            max_drawdown = 0.0

        # Recent performance (last 5 days)
        recent_returns = df['returns'].iloc[-5:].tolist()
        recent_performance = {
            'daily_returns': [round(r, 4) for r in recent_returns if not np.isnan(r)],
            'cumulative_return': round(np.prod([1 + r for r in recent_returns if not np.isnan(r)]) - 1, 4)
        }

        return {
            'expected_return': expected_return,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'avg_return': expected_return,
            'optimal_params': optimal_params,
            'recent_performance': recent_performance,
            'num_trades': len(all_trades)
        }

    def _optimize_parameters(self, df: pd.DataFrame) -> Dict:
        """
        Optimize strategy parameters on training data

        Args:
            df: Training data

        Returns:
            Optimal parameters
        """
        # Grid search over parameter space
        best_sharpe = -999
        best_params = {}

        # Test different moving average combinations
        fast_periods = [5, 10, 15, 20]
        slow_periods = [20, 30, 50]
        rsi_periods = [7, 14, 21]

        for fast in fast_periods:
            for slow in slow_periods:
                for rsi_period in rsi_periods:
                    if fast >= slow:
                        continue

                    params = {
                        'fast_ma': fast,
                        'slow_ma': slow,
                        'rsi_period': rsi_period,
                        'rsi_oversold': 30,
                        'rsi_overbought': 70
                    }

                    # Backtest with these parameters
                    results = self._backtest_strategy(df, params)

                    if results['sharpe_ratio'] > best_sharpe:
                        best_sharpe = results['sharpe_ratio']
                        best_params = params

        return best_params if best_params else {
            'fast_ma': 10,
            'slow_ma': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }

    def _backtest_strategy(self, df: pd.DataFrame, params: Dict) -> Dict:
        """
        Backtest a strategy with given parameters

        Args:
            df: DataFrame with OHLCV data
            params: Strategy parameters

        Returns:
            Backtest results
        """
        if len(df) < max(params['slow_ma'], params['rsi_period']):
            return {
                'sharpe_ratio': 0.0,
                'trades': [],
                'total_return': 0.0
            }

        # Calculate indicators
        df = df.copy()
        df['fast_ma'] = df['close'].rolling(window=params['fast_ma']).mean()
        df['slow_ma'] = df['close'].rolling(window=params['slow_ma']).mean()

        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Generate signals
        df['signal'] = 0

        # Buy signal: fast MA crosses above slow MA and RSI < 70
        df.loc[(df['fast_ma'] > df['slow_ma']) &
               (df['fast_ma'].shift(1) <= df['slow_ma'].shift(1)) &
               (df['rsi'] < params['rsi_overbought']), 'signal'] = 1

        # Sell signal: fast MA crosses below slow MA or RSI > 70
        df.loc[(df['fast_ma'] < df['slow_ma']) &
               (df['fast_ma'].shift(1) >= df['slow_ma'].shift(1)) |
               (df['rsi'] > params['rsi_overbought']), 'signal'] = -1

        # Simulate trades
        trades = []
        position = None

        for i in range(len(df)):
            if df['signal'].iloc[i] == 1 and position is None:
                # Buy
                position = {
                    'entry_price': df['close'].iloc[i],
                    'entry_date': df.index[i]
                }
            elif df['signal'].iloc[i] == -1 and position is not None:
                # Sell
                exit_price = df['close'].iloc[i]
                trade_return = (exit_price - position['entry_price']) / position['entry_price']

                trades.append({
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'return': trade_return,
                    'entry_date': position['entry_date'],
                    'exit_date': df.index[i]
                })

                position = None

        # Calculate performance metrics
        if len(trades) > 0:
            returns = [t['return'] for t in trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0
            total_return = np.prod([1 + r for r in returns]) - 1
        else:
            sharpe_ratio = 0.0
            total_return = 0.0

        return {
            'sharpe_ratio': sharpe_ratio,
            'trades': trades,
            'total_return': total_return
        }

    def _generate_recommendation(self, results: Dict) -> Dict:
        """
        Generate trading recommendation based on optimization results

        Args:
            results: Optimization results

        Returns:
            Recommendation with action and confidence
        """
        sharpe = results['sharpe_ratio']
        win_rate = results['win_rate']
        expected_return = results['expected_return']
        max_drawdown = results['max_drawdown']

        # Calculate confidence score
        confidence_factors = []

        # Sharpe ratio factor (0-1)
        if sharpe > 2.0:
            confidence_factors.append(1.0)
        elif sharpe > 1.0:
            confidence_factors.append(0.7)
        elif sharpe > 0.5:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.2)

        # Win rate factor
        confidence_factors.append(min(win_rate * 1.5, 1.0))

        # Max drawdown factor (lower drawdown = higher confidence)
        if max_drawdown < 0.05:
            confidence_factors.append(1.0)
        elif max_drawdown < 0.10:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)

        confidence = np.mean(confidence_factors)

        # Determine action
        if expected_return > 0.02 and sharpe > 1.0 and win_rate > 0.5:
            action = 'BUY'
        elif expected_return < -0.02 and sharpe < 0 and win_rate < 0.4:
            action = 'SELL'
        else:
            action = 'HOLD'

        return {
            'action': action,
            'confidence': confidence
        }

    def optimize_multiple(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Optimize multiple stocks

        Args:
            data_dict: Dictionary mapping symbols to DataFrames

        Returns:
            Dictionary mapping symbols to optimization results
        """
        results = {}

        for symbol, df in data_dict.items():
            try:
                results[symbol] = self.optimize(df)
            except Exception as e:
                results[symbol] = {
                    'recommendation': 'HOLD',
                    'confidence': 0.0,
                    'error': str(e)
                }

        return results
