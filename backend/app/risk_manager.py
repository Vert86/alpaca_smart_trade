"""
Risk Management System
Handles position sizing, account balance checks, and Pattern Day Trading (PDT) prevention
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import Config


class RiskManager:
    """Manages trading risk and position sizing"""

    def __init__(self, alpaca_client):
        """
        Initialize risk manager

        Args:
            alpaca_client: AlpacaClient instance
        """
        self.client = alpaca_client
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.min_account_balance = Config.MIN_ACCOUNT_BALANCE
        self.enable_pdt_protection = Config.ENABLE_PDT_PROTECTION

    def evaluate_trade(
        self,
        symbol: str,
        action: str,
        account: Dict,
        positions: List[Dict],
        current_price: float
    ) -> Dict:
        """
        Evaluate if a trade is safe to execute

        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            account: Account information
            positions: Current positions
            current_price: Current stock price

        Returns:
            Dictionary with approval status and details
        """
        checks = {
            'approved': True,
            'reason': '',
            'warnings': [],
            'position_size': 0,
            'position_value': 0.0,
            'checks': {}
        }

        # Get current position for symbol
        current_position = next((p for p in positions if p['symbol'] == symbol), None)

        # 1. Check account balance
        balance_check = self._check_account_balance(account)
        checks['checks']['account_balance'] = balance_check
        if not balance_check['passed']:
            checks['approved'] = False
            checks['reason'] = balance_check['message']
            return checks

        # 2. Check if account is blocked
        blocked_check = self._check_account_blocked(account)
        checks['checks']['account_blocked'] = blocked_check
        if not blocked_check['passed']:
            checks['approved'] = False
            checks['reason'] = blocked_check['message']
            return checks

        # 3. Check Pattern Day Trading (PDT) rules
        if action == 'BUY':
            pdt_check = self._check_pdt_rules(account)
            checks['checks']['pdt_protection'] = pdt_check
            if not pdt_check['passed']:
                checks['approved'] = False
                checks['reason'] = pdt_check['message']
                return checks

        # 4. Calculate position size
        if action == 'BUY':
            position_calc = self._calculate_position_size(
                account,
                positions,
                current_price,
                symbol
            )
            checks['checks']['position_sizing'] = position_calc

            if position_calc['max_shares'] <= 0:
                checks['approved'] = False
                checks['reason'] = 'Insufficient buying power for trade'
                return checks

            checks['position_size'] = position_calc['max_shares']
            checks['position_value'] = position_calc['position_value']

            # Add warning if position would be large
            if position_calc['portfolio_percentage'] > 0.15:
                checks['warnings'].append(
                    f"Large position: {position_calc['portfolio_percentage']*100:.1f}% of portfolio"
                )

        elif action == 'SELL':
            if not current_position:
                checks['approved'] = False
                checks['reason'] = f'No position to sell for {symbol}'
                return checks

            checks['position_size'] = current_position['qty']
            checks['position_value'] = current_position['market_value']

        # 5. Check portfolio concentration
        concentration_check = self._check_portfolio_concentration(
            account,
            positions,
            symbol,
            action,
            checks.get('position_value', 0)
        )
        checks['checks']['concentration'] = concentration_check

        if not concentration_check['passed']:
            checks['warnings'].append(concentration_check['message'])

        # 6. Check volatility risk
        volatility_check = self._check_volatility_risk(symbol, current_price)
        checks['checks']['volatility'] = volatility_check

        if volatility_check.get('warning'):
            checks['warnings'].append(volatility_check['warning'])

        return checks

    def _check_account_balance(self, account: Dict) -> Dict:
        """Check if account has sufficient balance"""
        cash = account.get('cash', 0)
        equity = account.get('equity', 0)

        if equity < self.min_account_balance:
            return {
                'passed': False,
                'message': f'Account equity (${equity:.2f}) below minimum (${self.min_account_balance:.2f})'
            }

        if cash < 100:  # Need at least $100 cash for trades
            return {
                'passed': False,
                'message': f'Insufficient cash balance: ${cash:.2f}'
            }

        return {
            'passed': True,
            'message': f'Sufficient balance: ${equity:.2f} equity, ${cash:.2f} cash'
        }

    def _check_account_blocked(self, account: Dict) -> Dict:
        """Check if account is blocked from trading"""
        if account.get('trading_blocked', False):
            return {
                'passed': False,
                'message': 'Account is blocked from trading'
            }

        if account.get('account_blocked', False):
            return {
                'passed': False,
                'message': 'Account is blocked'
            }

        return {
            'passed': True,
            'message': 'Account is active'
        }

    def _check_pdt_rules(self, account: Dict) -> Dict:
        """
        Check Pattern Day Trading rules

        PDT Rule: If account equity < $25,000, limited to 3 day trades in 5 business days
        """
        if not self.enable_pdt_protection:
            return {
                'passed': True,
                'message': 'PDT protection disabled'
            }

        equity = account.get('equity', 0)
        daytrade_count = account.get('daytrade_count', 0)
        is_pdt = account.get('pattern_day_trader', False)

        # If equity >= $25,000, PDT rules don't apply
        if equity >= 25000:
            return {
                'passed': True,
                'message': f'PDT rules not applicable (equity: ${equity:.2f})'
            }

        # Check daytrade count
        if daytrade_count >= 3:
            return {
                'passed': False,
                'message': f'PDT limit reached: {daytrade_count}/3 day trades used. Wait until next week or increase equity to $25,000+'
            }

        # Warning if approaching limit
        message = f'PDT check passed: {daytrade_count}/3 day trades used'
        if daytrade_count >= 2:
            message += ' (WARNING: Close to limit!)'

        return {
            'passed': True,
            'message': message,
            'daytrade_count': daytrade_count,
            'is_pattern_day_trader': is_pdt
        }

    def _calculate_position_size(
        self,
        account: Dict,
        positions: List[Dict],
        price: float,
        symbol: str
    ) -> Dict:
        """
        Calculate maximum position size based on risk parameters

        Args:
            account: Account information
            positions: Current positions
            price: Stock price
            symbol: Stock symbol

        Returns:
            Position sizing details
        """
        equity = account.get('equity', 0)
        buying_power = account.get('buying_power', 0)

        # Maximum position value based on portfolio percentage
        max_position_value = equity * self.max_position_size

        # Available buying power (considering existing position)
        current_position = next((p for p in positions if p['symbol'] == symbol), None)
        current_exposure = current_position['market_value'] if current_position else 0

        # Remaining allocation for this symbol
        remaining_allocation = max_position_value - current_exposure

        # Can't use more than available buying power
        available_value = min(remaining_allocation, buying_power)

        # Calculate shares (leave some buffer for price movement)
        buffer = 0.98  # 2% buffer
        max_shares = int((available_value * buffer) / price) if price > 0 else 0

        return {
            'max_shares': max_shares,
            'position_value': max_shares * price,
            'portfolio_percentage': (max_shares * price) / equity if equity > 0 else 0,
            'max_position_value': max_position_value,
            'current_exposure': current_exposure,
            'remaining_allocation': remaining_allocation
        }

    def _check_portfolio_concentration(
        self,
        account: Dict,
        positions: List[Dict],
        symbol: str,
        action: str,
        trade_value: float
    ) -> Dict:
        """Check if portfolio is too concentrated in few stocks"""
        equity = account.get('equity', 0)

        if equity == 0:
            return {'passed': True, 'message': 'No equity to evaluate'}

        # Calculate total concentration
        total_invested = sum(p['market_value'] for p in positions)

        if action == 'BUY':
            total_invested += trade_value

        concentration = total_invested / equity if equity > 0 else 0

        # Warning if more than 80% invested
        if concentration > 0.80:
            return {
                'passed': True,
                'message': f'High portfolio concentration: {concentration*100:.1f}% invested'
            }

        # Check number of positions
        num_positions = len(positions)
        if action == 'BUY' and symbol not in [p['symbol'] for p in positions]:
            num_positions += 1

        if num_positions > 15:
            return {
                'passed': True,
                'message': f'Large number of positions: {num_positions}'
            }

        return {
            'passed': True,
            'message': f'Concentration OK: {concentration*100:.1f}% invested in {num_positions} positions'
        }

    def _check_volatility_risk(self, symbol: str, price: float) -> Dict:
        """Check volatility risk (placeholder - can be enhanced with real volatility data)"""
        # This is a simple placeholder - in production, you'd calculate actual volatility
        # from historical data or use option-implied volatility

        return {
            'passed': True,
            'message': 'Volatility check not implemented',
            'warning': None
        }

    def get_risk_summary(self, account: Dict, positions: List[Dict]) -> Dict:
        """
        Get overall risk summary

        Args:
            account: Account information
            positions: Current positions

        Returns:
            Risk summary
        """
        equity = account.get('equity', 0)
        cash = account.get('cash', 0)
        daytrade_count = account.get('daytrade_count', 0)

        # Calculate portfolio metrics
        total_invested = sum(p['market_value'] for p in positions)
        total_unrealized_pl = sum(p['unrealized_pl'] for p in positions)

        # Position concentration
        position_values = [p['market_value'] for p in positions]
        largest_position = max(position_values) if position_values else 0
        largest_position_pct = (largest_position / equity) * 100 if equity > 0 else 0

        return {
            'account': {
                'equity': round(equity, 2),
                'cash': round(cash, 2),
                'invested': round(total_invested, 2),
                'invested_percentage': round((total_invested / equity) * 100, 1) if equity > 0 else 0
            },
            'pdt': {
                'daytrade_count': daytrade_count,
                'remaining_daytrades': max(0, 3 - daytrade_count),
                'pdt_restricted': equity < 25000 and daytrade_count >= 3
            },
            'portfolio': {
                'num_positions': len(positions),
                'total_unrealized_pl': round(total_unrealized_pl, 2),
                'total_unrealized_pl_pct': round((total_unrealized_pl / (total_invested - total_unrealized_pl)) * 100, 2) if (total_invested - total_unrealized_pl) > 0 else 0,
                'largest_position_value': round(largest_position, 2),
                'largest_position_pct': round(largest_position_pct, 1)
            },
            'warnings': self._generate_warnings(account, positions)
        }

    def _generate_warnings(self, account: Dict, positions: List[Dict]) -> List[str]:
        """Generate risk warnings"""
        warnings = []

        equity = account.get('equity', 0)
        cash = account.get('cash', 0)
        daytrade_count = account.get('daytrade_count', 0)

        # PDT warning
        if equity < 25000 and daytrade_count >= 2:
            warnings.append(f'⚠️ PDT Warning: {daytrade_count}/3 day trades used')

        # Low cash warning
        if cash < 500:
            warnings.append(f'⚠️ Low cash balance: ${cash:.2f}')

        # High concentration warning
        total_invested = sum(p['market_value'] for p in positions)
        if equity > 0 and (total_invested / equity) > 0.90:
            warnings.append(f'⚠️ High portfolio concentration: {(total_invested/equity)*100:.1f}% invested')

        # Large unrealized losses
        for pos in positions:
            if pos['unrealized_plpc'] < -0.15:  # More than 15% loss
                warnings.append(f'⚠️ Large loss in {pos["symbol"]}: {pos["unrealized_plpc"]*100:.1f}%')

        return warnings
