"""
Trading Decision Engine
Combines analysis results and generates trading recommendations
"""
from typing import Dict, List
import numpy as np


class DecisionEngine:
    """Makes trading decisions based on multiple analysis inputs"""

    def __init__(self):
        """Initialize decision engine"""
        # Weights for different analysis methods
        self.weights = {
            'regime_switching': 0.4,
            'walk_forward': 0.4,
            'risk_management': 0.2
        }

    def make_decision(
        self,
        symbol: str,
        regime_analysis: Dict,
        walk_forward_analysis: Dict,
        risk_evaluation: Dict,
        current_position: Dict = None
    ) -> Dict:
        """
        Make trading decision for a symbol

        Args:
            symbol: Stock symbol
            regime_analysis: Results from regime-switching analysis
            walk_forward_analysis: Results from walk-forward optimization
            risk_evaluation: Risk management evaluation
            current_position: Current position (if any)

        Returns:
            Trading decision with recommendation and confidence
        """
        # Extract recommendations from each analysis
        regime_rec = self._interpret_regime(regime_analysis)
        wf_rec = self._interpret_walk_forward(walk_forward_analysis)
        risk_rec = self._interpret_risk(risk_evaluation)

        # Combine recommendations
        combined_score = (
            regime_rec['score'] * self.weights['regime_switching'] +
            wf_rec['score'] * self.weights['walk_forward'] +
            risk_rec['score'] * self.weights['risk_management']
        )

        # Determine final action
        if combined_score > 0.3:
            action = 'BUY'
        elif combined_score < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'

        # Adjust for current position
        if current_position:
            action, combined_score = self._adjust_for_position(
                action,
                combined_score,
                current_position,
                regime_analysis,
                walk_forward_analysis
            )

        # Calculate overall confidence
        confidence = min(abs(combined_score), 1.0)

        # Generate detailed reasoning
        reasoning = self._generate_reasoning(
            regime_rec,
            wf_rec,
            risk_rec,
            action,
            confidence
        )

        # Calculate suggested position size
        position_size = risk_evaluation.get('position_size', 0)
        position_value = risk_evaluation.get('position_value', 0)

        return {
            'symbol': symbol,
            'action': action,
            'confidence': round(confidence, 3),
            'combined_score': round(combined_score, 3),
            'position_size': position_size,
            'position_value': round(position_value, 2),
            'reasoning': reasoning,
            'analysis_breakdown': {
                'regime_switching': regime_rec,
                'walk_forward': wf_rec,
                'risk_management': risk_rec
            },
            'warnings': risk_evaluation.get('warnings', [])
        }

    def _interpret_regime(self, analysis: Dict) -> Dict:
        """Interpret regime-switching analysis results"""
        regime = analysis.get('regime', 'UNKNOWN')
        confidence = analysis.get('confidence', 0)
        trend_strength = analysis.get('trend_strength', 0)

        # Calculate score from -1 (bearish) to +1 (bullish)
        if regime == 'BULLISH':
            score = confidence * trend_strength
        elif regime == 'BEARISH':
            score = -confidence * trend_strength
        else:  # SIDEWAYS or UNKNOWN
            score = 0

        return {
            'score': score,
            'regime': regime,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'recommendation': 'BUY' if score > 0.3 else ('SELL' if score < -0.3 else 'HOLD')
        }

    def _interpret_walk_forward(self, analysis: Dict) -> Dict:
        """Interpret walk-forward optimization results"""
        recommendation = analysis.get('recommendation', 'HOLD')
        confidence = analysis.get('confidence', 0)
        expected_return = analysis.get('expected_return', 0)
        sharpe_ratio = analysis.get('sharpe_ratio', 0)

        # Calculate score
        if recommendation == 'BUY':
            score = confidence
        elif recommendation == 'SELL':
            score = -confidence
        else:
            score = 0

        # Adjust based on sharpe ratio
        if sharpe_ratio > 1.5:
            score *= 1.2
        elif sharpe_ratio < 0.5:
            score *= 0.8

        score = max(-1, min(1, score))

        return {
            'score': score,
            'recommendation': recommendation,
            'confidence': confidence,
            'expected_return': expected_return,
            'sharpe_ratio': sharpe_ratio
        }

    def _interpret_risk(self, risk_eval: Dict) -> Dict:
        """Interpret risk management evaluation"""
        approved = risk_eval.get('approved', False)
        reason = risk_eval.get('reason', '')
        warnings = risk_eval.get('warnings', [])

        # Risk is binary: either approved or not
        # But we can modulate based on warnings
        if not approved:
            score = -1.0  # Block the trade
        elif len(warnings) > 2:
            score = -0.5  # Multiple warnings, be cautious
        elif len(warnings) > 0:
            score = 0.0  # Some concerns
        else:
            score = 0.5  # All clear

        return {
            'score': score,
            'approved': approved,
            'warnings': warnings,
            'reason': reason
        }

    def _adjust_for_position(
        self,
        action: str,
        score: float,
        position: Dict,
        regime_analysis: Dict,
        wf_analysis: Dict
    ) -> tuple:
        """
        Adjust decision based on current position

        Args:
            action: Initial action recommendation
            score: Combined score
            position: Current position details
            regime_analysis: Regime analysis results
            wf_analysis: Walk-forward analysis results

        Returns:
            Tuple of (adjusted_action, adjusted_score)
        """
        unrealized_plpc = position.get('unrealized_plpc', 0)

        # If we have a profitable position
        if unrealized_plpc > 0.10:  # More than 10% profit
            # Check if we should take profits
            if regime_analysis.get('regime') == 'BEARISH' or wf_analysis.get('expected_return', 0) < 0:
                return 'SELL', -0.7  # Strong sell to lock in profits

        # If we have a losing position
        elif unrealized_plpc < -0.10:  # More than 10% loss
            # Check if we should cut losses
            if regime_analysis.get('regime') == 'BEARISH' and wf_analysis.get('recommendation') == 'SELL':
                return 'SELL', -0.8  # Strong sell to cut losses

            # Or if we should hold/average down
            elif regime_analysis.get('regime') == 'BULLISH' and action == 'BUY':
                return 'BUY', score * 0.7  # Reduce conviction for averaging down

        # If action is BUY but we already have a position
        if action == 'BUY':
            # Reduce score to avoid over-concentration
            return 'HOLD', score * 0.5

        # If action is SELL and we have a position
        if action == 'SELL' and position:
            # This is appropriate
            return action, score

        return action, score

    def _generate_reasoning(
        self,
        regime_rec: Dict,
        wf_rec: Dict,
        risk_rec: Dict,
        action: str,
        confidence: float
    ) -> List[str]:
        """Generate human-readable reasoning for the decision"""
        reasoning = []

        # Regime analysis reasoning
        regime = regime_rec.get('regime', 'UNKNOWN')
        regime_conf = regime_rec.get('confidence', 0)
        trend_strength = regime_rec.get('trend_strength', 0)

        if regime == 'BULLISH':
            reasoning.append(
                f"✓ Regime Analysis: {regime} market detected "
                f"(confidence: {regime_conf:.1%}, trend strength: {trend_strength:.1%})"
            )
        elif regime == 'BEARISH':
            reasoning.append(
                f"✗ Regime Analysis: {regime} market detected "
                f"(confidence: {regime_conf:.1%}, trend strength: {trend_strength:.1%})"
            )
        else:
            reasoning.append(
                f"○ Regime Analysis: {regime} market "
                f"(confidence: {regime_conf:.1%})"
            )

        # Walk-forward reasoning
        wf_recommendation = wf_rec.get('recommendation', 'HOLD')
        expected_return = wf_rec.get('expected_return', 0)
        sharpe = wf_rec.get('sharpe_ratio', 0)

        if wf_recommendation == 'BUY':
            reasoning.append(
                f"✓ Walk-Forward Optimization: {wf_recommendation} signal "
                f"(expected return: {expected_return:.2%}, Sharpe: {sharpe:.2f})"
            )
        elif wf_recommendation == 'SELL':
            reasoning.append(
                f"✗ Walk-Forward Optimization: {wf_recommendation} signal "
                f"(expected return: {expected_return:.2%}, Sharpe: {sharpe:.2f})"
            )
        else:
            reasoning.append(
                f"○ Walk-Forward Optimization: No clear signal "
                f"(Sharpe: {sharpe:.2f})"
            )

        # Risk management reasoning
        if not risk_rec.get('approved', False):
            reasoning.append(f"✗ Risk Check: {risk_rec.get('reason', 'Failed')}")
        elif risk_rec.get('warnings'):
            reasoning.append(f"⚠ Risk Check: Passed with warnings")
            for warning in risk_rec['warnings'][:2]:  # Show first 2 warnings
                reasoning.append(f"  • {warning}")
        else:
            reasoning.append("✓ Risk Check: All checks passed")

        # Final recommendation
        if action == 'BUY':
            reasoning.append(
                f"\n→ RECOMMENDATION: {action} with {confidence:.1%} confidence"
            )
        elif action == 'SELL':
            reasoning.append(
                f"\n→ RECOMMENDATION: {action} with {confidence:.1%} confidence"
            )
        else:
            reasoning.append(
                f"\n→ RECOMMENDATION: {action} - signals are mixed or inconclusive"
            )

        return reasoning

    def analyze_portfolio(
        self,
        symbols: List[str],
        regime_results: Dict[str, Dict],
        wf_results: Dict[str, Dict],
        risk_summary: Dict,
        positions: List[Dict],
        account: Dict,
        risk_manager
    ) -> Dict:
        """
        Analyze entire portfolio and generate recommendations

        Args:
            symbols: List of symbols to analyze
            regime_results: Regime analysis results for all symbols
            wf_results: Walk-forward results for all symbols
            risk_summary: Overall risk summary
            positions: Current positions
            account: Account information
            risk_manager: RiskManager instance

        Returns:
            Portfolio analysis with recommendations for each symbol
        """
        recommendations = []
        current_price_map = {}  # You'd get this from latest quotes

        for symbol in symbols:
            # Get current position if any
            current_position = next((p for p in positions if p['symbol'] == symbol), None)
            current_price = current_position['current_price'] if current_position else 0

            # Get analysis results
            regime = regime_results.get(symbol, {})
            wf = wf_results.get(symbol, {})

            # Get recommendation from walk-forward or regime
            action = wf.get('recommendation', 'HOLD')

            # Evaluate risk for this trade
            if current_price > 0:
                risk_eval = risk_manager.evaluate_trade(
                    symbol,
                    action,
                    account,
                    positions,
                    current_price
                )
            else:
                risk_eval = {'approved': False, 'reason': 'No current price data'}

            # Make decision
            decision = self.make_decision(
                symbol,
                regime,
                wf,
                risk_eval,
                current_position
            )

            recommendations.append(decision)

        # Sort by confidence (highest first)
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)

        # Categorize recommendations
        buy_recommendations = [r for r in recommendations if r['action'] == 'BUY']
        sell_recommendations = [r for r in recommendations if r['action'] == 'SELL']
        hold_recommendations = [r for r in recommendations if r['action'] == 'HOLD']

        return {
            'all_recommendations': recommendations,
            'buy_recommendations': buy_recommendations,
            'sell_recommendations': sell_recommendations,
            'hold_recommendations': hold_recommendations,
            'summary': {
                'total_symbols': len(symbols),
                'buy_signals': len(buy_recommendations),
                'sell_signals': len(sell_recommendations),
                'hold_signals': len(hold_recommendations)
            },
            'risk_summary': risk_summary
        }
