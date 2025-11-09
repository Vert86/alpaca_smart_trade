"""
Regime-Switching Indicator Analysis
Identifies market regimes (Bullish, Bearish, Sideways) using technical indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import ta


class RegimeSwitchingAnalyzer:
    """Analyzes market regime using multiple technical indicators"""

    def __init__(self, sma_periods: List[int] = [20, 50, 200]):
        """
        Initialize regime analyzer

        Args:
            sma_periods: Simple Moving Average periods for regime detection
        """
        self.sma_periods = sma_periods

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analyze market regime for a stock

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            Dictionary with regime analysis results
        """
        if df is None or len(df) < max(self.sma_periods):
            return {
                'regime': 'UNKNOWN',
                'confidence': 0.0,
                'trend_strength': 0.0,
                'volatility': 0.0,
                'indicators': {}
            }

        # Calculate technical indicators
        indicators = self._calculate_indicators(df)

        # Determine regime
        regime_score = self._calculate_regime_score(indicators)

        # Determine regime type
        if regime_score > 0.3:
            regime = 'BULLISH'
        elif regime_score < -0.3:
            regime = 'BEARISH'
        else:
            regime = 'SIDEWAYS'

        # Calculate confidence
        confidence = min(abs(regime_score), 1.0)

        # Calculate trend strength
        trend_strength = self._calculate_trend_strength(indicators)

        # Calculate volatility
        volatility = indicators.get('atr_pct', 0.0)

        return {
            'regime': regime,
            'confidence': round(confidence, 3),
            'trend_strength': round(trend_strength, 3),
            'volatility': round(volatility, 3),
            'indicators': {
                'price': float(df['close'].iloc[-1]),
                'sma_20': round(indicators.get('sma_20', 0), 2),
                'sma_50': round(indicators.get('sma_50', 0), 2),
                'sma_200': round(indicators.get('sma_200', 0), 2),
                'rsi': round(indicators.get('rsi', 0), 2),
                'macd': round(indicators.get('macd', 0), 2),
                'macd_signal': round(indicators.get('macd_signal', 0), 2),
                'adx': round(indicators.get('adx', 0), 2),
                'atr': round(indicators.get('atr', 0), 2),
                'bollinger_position': round(indicators.get('bb_position', 0), 3)
            }
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        indicators = {}
        close = df['close']
        high = df['high']
        low = df['low']

        # Simple Moving Averages
        for period in self.sma_periods:
            if len(df) >= period:
                indicators[f'sma_{period}'] = close.rolling(window=period).mean().iloc[-1]

        # RSI (Relative Strength Index)
        if len(df) >= 14:
            indicators['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

        # MACD (Moving Average Convergence Divergence)
        if len(df) >= 26:
            macd = ta.trend.MACD(close)
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_diff'] = macd.macd_diff().iloc[-1]

        # ADX (Average Directional Index) - Trend Strength
        if len(df) >= 14:
            adx = ta.trend.ADXIndicator(high, low, close, window=14)
            indicators['adx'] = adx.adx().iloc[-1]
            indicators['adx_pos'] = adx.adx_pos().iloc[-1]
            indicators['adx_neg'] = adx.adx_neg().iloc[-1]

        # ATR (Average True Range) - Volatility
        if len(df) >= 14:
            atr = ta.volatility.AverageTrueRange(high, low, close, window=14)
            indicators['atr'] = atr.average_true_range().iloc[-1]
            # ATR as percentage of price
            indicators['atr_pct'] = (indicators['atr'] / close.iloc[-1]) * 100

        # Bollinger Bands
        if len(df) >= 20:
            bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
            bb_high = bb.bollinger_hband().iloc[-1]
            bb_low = bb.bollinger_lband().iloc[-1]
            bb_mid = bb.bollinger_mavg().iloc[-1]
            current_price = close.iloc[-1]

            # Position within Bollinger Bands (0 = lower band, 1 = upper band)
            if bb_high != bb_low:
                indicators['bb_position'] = (current_price - bb_low) / (bb_high - bb_low)
            else:
                indicators['bb_position'] = 0.5

            indicators['bb_width'] = ((bb_high - bb_low) / bb_mid) * 100

        # Stochastic Oscillator
        if len(df) >= 14:
            stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]

        # Volume indicators
        if len(df) >= 20:
            indicators['volume_sma'] = df['volume'].rolling(window=20).mean().iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']

        return indicators

    def _calculate_regime_score(self, indicators: Dict) -> float:
        """
        Calculate regime score from -1 (bearish) to +1 (bullish)

        Args:
            indicators: Dictionary of technical indicators

        Returns:
            Regime score
        """
        score = 0.0
        weights = []

        current_price = indicators.get('sma_20', 0)  # Use SMA20 as proxy for current price

        # SMA alignment (most important)
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        sma_200 = indicators.get('sma_200', 0)

        if sma_20 and sma_50 and sma_200:
            if sma_20 > sma_50 > sma_200:
                score += 1.0  # Strong bullish alignment
                weights.append(1.0)
            elif sma_20 < sma_50 < sma_200:
                score -= 1.0  # Strong bearish alignment
                weights.append(1.0)
            elif sma_20 > sma_50:
                score += 0.5  # Moderate bullish
                weights.append(0.5)
            elif sma_20 < sma_50:
                score -= 0.5  # Moderate bearish
                weights.append(0.5)

        # RSI
        rsi = indicators.get('rsi', 50)
        if rsi:
            if rsi > 70:
                score -= 0.3  # Overbought (bearish)
            elif rsi > 60:
                score += 0.3  # Strong momentum (bullish)
            elif rsi < 30:
                score += 0.3  # Oversold (bullish reversal potential)
            elif rsi < 40:
                score -= 0.3  # Weak momentum (bearish)
            weights.append(0.3)

        # MACD
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 0.4  # Bullish crossover
            else:
                score -= 0.4  # Bearish crossover
            weights.append(0.4)

        # ADX and trend direction
        adx = indicators.get('adx', 0)
        adx_pos = indicators.get('adx_pos', 0)
        adx_neg = indicators.get('adx_neg', 0)

        if adx and adx_pos and adx_neg:
            if adx > 25:  # Strong trend
                if adx_pos > adx_neg:
                    score += 0.5  # Strong bullish trend
                else:
                    score -= 0.5  # Strong bearish trend
                weights.append(0.5)

        # Bollinger Band position
        bb_position = indicators.get('bb_position', 0.5)
        if bb_position is not None:
            # Position near upper band is bullish, lower band is bearish
            score += (bb_position - 0.5) * 0.4
            weights.append(0.4)

        # Normalize score
        total_weight = sum(weights) if weights else 1.0
        normalized_score = score / total_weight if total_weight > 0 else 0.0

        return max(-1.0, min(1.0, normalized_score))

    def _calculate_trend_strength(self, indicators: Dict) -> float:
        """
        Calculate trend strength from 0 (no trend) to 1 (strong trend)

        Args:
            indicators: Dictionary of technical indicators

        Returns:
            Trend strength score
        """
        adx = indicators.get('adx', 0)

        if not adx:
            return 0.0

        # ADX interpretation:
        # 0-25: Weak/No trend
        # 25-50: Strong trend
        # 50-75: Very strong trend
        # 75-100: Extremely strong trend

        if adx < 25:
            return adx / 25.0  # 0.0 to 1.0
        elif adx < 50:
            return 1.0  # Strong trend
        else:
            return min(1.0, adx / 50.0)  # Very strong trend

    def analyze_multiple(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Analyze multiple stocks

        Args:
            data_dict: Dictionary mapping symbols to DataFrames

        Returns:
            Dictionary mapping symbols to analysis results
        """
        results = {}

        for symbol, df in data_dict.items():
            try:
                results[symbol] = self.analyze(df)
            except Exception as e:
                results[symbol] = {
                    'regime': 'ERROR',
                    'confidence': 0.0,
                    'trend_strength': 0.0,
                    'volatility': 0.0,
                    'error': str(e)
                }

        return results
