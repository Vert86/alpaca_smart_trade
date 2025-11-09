"""
Telegram Bot Integration
Sends trading analysis and notifications to Telegram
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, List
from config import Config


class TelegramNotifier:
    """Sends notifications via Telegram bot"""

    def __init__(self):
        """Initialize Telegram bot"""
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.bot = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)

    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return self.bot_token is not None and self.chat_id is not None

    async def send_message(self, message: str) -> bool:
        """
        Send a message to Telegram

        Args:
            message: Message text (supports Markdown)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            print("Telegram not configured")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except TelegramError as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def send_analysis_report(self, analysis_results: Dict) -> bool:
        """
        Send trading analysis report to Telegram

        Args:
            analysis_results: Portfolio analysis results

        Returns:
            True if successful
        """
        message = self._format_analysis_report(analysis_results)
        return await self.send_message(message)

    async def send_trade_notification(self, trade_details: Dict) -> bool:
        """
        Send trade execution notification

        Args:
            trade_details: Trade details

        Returns:
            True if successful
        """
        message = self._format_trade_notification(trade_details)
        return await self.send_message(message)

    async def send_alert(self, alert_message: str, alert_type: str = 'INFO') -> bool:
        """
        Send an alert message

        Args:
            alert_message: Alert text
            alert_type: Type of alert (INFO, WARNING, ERROR)

        Returns:
            True if successful
        """
        emoji_map = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '🚨',
            'SUCCESS': '✅'
        }

        emoji = emoji_map.get(alert_type, 'ℹ️')
        message = f"{emoji} *{alert_type}*\n\n{alert_message}"

        return await self.send_message(message)

    def _format_analysis_report(self, results: Dict) -> str:
        """Format analysis results as a Telegram message"""
        summary = results.get('summary', {})
        buy_recs = results.get('buy_recommendations', [])
        sell_recs = results.get('sell_recommendations', [])
        risk_summary = results.get('risk_summary', {})

        # Header
        message = "📊 *Alpaca Smart Trade Analysis Report*\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # Account summary
        if 'account' in risk_summary:
            account = risk_summary['account']
            message += f"💰 *Account Status*\n"
            message += f"• Equity: ${account.get('equity', 0):,.2f}\n"
            message += f"• Cash: ${account.get('cash', 0):,.2f}\n"
            message += f"• Invested: ${account.get('invested', 0):,.2f} ({account.get('invested_percentage', 0):.1f}%)\n\n"

        # PDT Status
        if 'pdt' in risk_summary:
            pdt = risk_summary['pdt']
            message += f"📅 *Pattern Day Trading Status*\n"
            message += f"• Day Trades Used: {pdt.get('daytrade_count', 0)}/3\n"
            message += f"• Remaining: {pdt.get('remaining_daytrades', 0)}\n"
            if pdt.get('pdt_restricted', False):
                message += "⚠️ *PDT RESTRICTED*\n"
            message += "\n"

        # Trading signals summary
        message += f"📈 *Trading Signals*\n"
        message += f"• Buy Signals: {summary.get('buy_signals', 0)}\n"
        message += f"• Sell Signals: {summary.get('sell_signals', 0)}\n"
        message += f"• Hold Signals: {summary.get('hold_signals', 0)}\n\n"

        # Buy recommendations (top 3)
        if buy_recs:
            message += "🟢 *TOP BUY RECOMMENDATIONS*\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
            for i, rec in enumerate(buy_recs[:3], 1):
                message += f"\n*{i}. {rec['symbol']}*\n"
                message += f"• Action: {rec['action']}\n"
                message += f"• Confidence: {rec['confidence']:.1%}\n"
                message += f"• Position Size: {rec['position_size']} shares (${rec['position_value']:,.2f})\n"

                # Add key reasoning points
                reasoning = rec.get('reasoning', [])
                if reasoning:
                    message += f"• Analysis: {reasoning[0][:80]}...\n" if len(reasoning[0]) > 80 else f"• Analysis: {reasoning[0]}\n"

            message += "\n"

        # Sell recommendations (top 3)
        if sell_recs:
            message += "🔴 *TOP SELL RECOMMENDATIONS*\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
            for i, rec in enumerate(sell_recs[:3], 1):
                message += f"\n*{i}. {rec['symbol']}*\n"
                message += f"• Action: {rec['action']}\n"
                message += f"• Confidence: {rec['confidence']:.1%}\n"

                # Add key reasoning points
                reasoning = rec.get('reasoning', [])
                if reasoning:
                    message += f"• Analysis: {reasoning[0][:80]}...\n" if len(reasoning[0]) > 80 else f"• Analysis: {reasoning[0]}\n"

            message += "\n"

        # Warnings
        warnings = risk_summary.get('warnings', [])
        if warnings:
            message += "⚠️ *WARNINGS*\n"
            for warning in warnings[:3]:  # Top 3 warnings
                message += f"• {warning}\n"
            message += "\n"

        # Footer
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🕐 Report generated at {self._get_current_time()}\n"

        return message

    def _format_trade_notification(self, trade: Dict) -> str:
        """Format trade notification message"""
        symbol = trade.get('symbol', 'UNKNOWN')
        action = trade.get('action', 'UNKNOWN')
        qty = trade.get('qty', 0)
        price = trade.get('price', 0)
        status = trade.get('status', 'UNKNOWN')

        emoji = '🟢' if action == 'BUY' else '🔴'

        message = f"{emoji} *TRADE NOTIFICATION*\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"Symbol: *{symbol}*\n"
        message += f"Action: *{action}*\n"
        message += f"Quantity: {qty} shares\n"
        message += f"Price: ${price:.2f}\n"
        message += f"Total Value: ${qty * price:,.2f}\n"
        message += f"Status: {status}\n\n"
        message += f"🕐 {self._get_current_time()}\n"

        return message

    def _format_recommendation(self, rec: Dict) -> str:
        """Format a single recommendation for Telegram"""
        symbol = rec.get('symbol', 'UNKNOWN')
        action = rec.get('action', 'HOLD')
        confidence = rec.get('confidence', 0)

        emoji = '🟢' if action == 'BUY' else ('🔴' if action == 'SELL' else '🟡')

        message = f"{emoji} *{symbol}* - {action}\n"
        message += f"Confidence: {confidence:.1%}\n"

        # Add analysis breakdown
        breakdown = rec.get('analysis_breakdown', {})
        if breakdown:
            regime = breakdown.get('regime_switching', {})
            if regime:
                message += f"• Regime: {regime.get('regime', 'N/A')} "
                message += f"({regime.get('confidence', 0):.1%})\n"

            wf = breakdown.get('walk_forward', {})
            if wf:
                message += f"• Expected Return: {wf.get('expected_return', 0):.2%}\n"
                message += f"• Sharpe Ratio: {wf.get('sharpe_ratio', 0):.2f}\n"

        return message

    def _get_current_time(self) -> str:
        """Get current time formatted for messages"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Synchronous wrappers for easier use
    def send_message_sync(self, message: str) -> bool:
        """Synchronous wrapper for send_message"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_message(message))

    def send_analysis_report_sync(self, analysis_results: Dict) -> bool:
        """Synchronous wrapper for send_analysis_report"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_analysis_report(analysis_results))

    def send_trade_notification_sync(self, trade_details: Dict) -> bool:
        """Synchronous wrapper for send_trade_notification"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_trade_notification(trade_details))

    def send_alert_sync(self, alert_message: str, alert_type: str = 'INFO') -> bool:
        """Synchronous wrapper for send_alert"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_alert(alert_message, alert_type))
