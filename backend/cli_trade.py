"""
Interactive CLI prompt for manual trading with Alpaca Smart Trade.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from config import Config
from app.alpaca_client import AlpacaClient
from app.telegram_bot import TelegramNotifier


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _get_holdings_map(positions: List[Dict]) -> Dict[str, float]:
    holdings: Dict[str, float] = {}
    for pos in positions:
        try:
            holdings[pos["symbol"].upper()] = float(pos.get("qty", 0))
        except Exception:
            continue
    return holdings


def _print_account_and_holdings(client: AlpacaClient) -> Tuple[Dict, List[Dict]]:
    account = client.get_account()
    positions = client.get_positions()

    print("\n" + "=" * 72)
    print("Account")
    print("-" * 72)
    print(f"Cash:          {_format_money(account.get('cash', 0))}")
    print(f"Buying Power:  {_format_money(account.get('buying_power', 0))}")
    print(f"Equity:        {_format_money(account.get('equity', 0))}")
    print(f"Portfolio Val: {_format_money(account.get('portfolio_value', 0))}")

    print("\nHoldings")
    print("-" * 72)
    if not positions:
        print("(none)")
    else:
        for pos in sorted(positions, key=lambda p: p.get("symbol", "")):
            symbol = str(pos.get("symbol", "")).upper()
            qty = float(pos.get("qty", 0))
            avg = float(pos.get("avg_entry_price", 0))
            cur = float(pos.get("current_price", 0))
            mv = float(pos.get("market_value", 0))
            upl = float(pos.get("unrealized_pl", 0))
            print(
                f"{symbol:6} qty={qty:10.4f}  avg={_format_money(avg):>12}  "
                f"cur={_format_money(cur):>12}  mv={_format_money(mv):>12}  "
                f"uP/L={_format_money(upl):>12}"
            )
    print("=" * 72 + "\n")
    return account, positions


def _pick_symbol(defaults: List[str]) -> Optional[str]:
    defaults = [s.strip().upper() for s in defaults if s.strip()]
    if not defaults:
        return None

    print("Select a stock:")
    for i, sym in enumerate(defaults, 1):
        print(f"{i}. {sym}")
    print("0. Exit")

    while True:
        raw = input("Choice (number): ").strip()
        if raw == "0":
            return None
        try:
            idx = int(raw)
        except ValueError:
            print("Enter a number from the list.")
            continue
        if 1 <= idx <= len(defaults):
            return defaults[idx - 1]
        print("Invalid selection.")


def _pick_action() -> Optional[str]:
    print("\nAction:")
    print("1. BUY")
    print("2. SELL")
    print("0. Back")
    while True:
        raw = input("Choice (number): ").strip()
        if raw == "0":
            return None
        if raw == "1":
            return "BUY"
        if raw == "2":
            return "SELL"
        print("Invalid selection.")


def _pick_quantity(max_qty: Optional[float] = None) -> Optional[float]:
    hint = ""
    if max_qty is not None:
        hint = f" (max {max_qty:g})"
    while True:
        raw = input(f"How many shares?{hint}: ").strip()
        if raw.lower() in {"b", "back"}:
            return None
        try:
            qty = float(raw)
        except ValueError:
            print("Enter a number (or type 'back').")
            continue
        if qty <= 0:
            print("Quantity must be > 0.")
            continue
        if max_qty is not None and qty > max_qty:
            print("Quantity exceeds current holdings.")
            continue
        return qty


def main() -> int:
    Config.validate()

    client = AlpacaClient()
    telegram = TelegramNotifier()

    print("\nAlpaca Smart Trade - Interactive Trader\n")
    _print_account_and_holdings(client)

    defaults = Config.DEFAULT_STOCKS
    while True:
        symbol = _pick_symbol(defaults)
        if symbol is None:
            print("Goodbye.")
            return 0

        action = _pick_action()
        if action is None:
            continue

        positions = client.get_positions()
        holdings = _get_holdings_map(positions)

        max_sell_qty = None
        if action == "SELL":
            held = holdings.get(symbol, 0.0)
            if held <= 0:
                print(f"\nYou don't currently hold any shares of {symbol}; cannot SELL.\n")
                continue
            max_sell_qty = held

        qty = _pick_quantity(max_qty=max_sell_qty)
        if qty is None:
            continue

        quotes = client.get_latest_quotes([symbol])
        price = quotes.get(symbol, {}).get("ask_price" if action == "BUY" else "bid_price", 0) or 0

        order = client.place_market_order(
            symbol=symbol,
            qty=qty,
            side=action.lower(),
        )

        print(
            f"\nConfirmed: {action} {qty:g} shares of {symbol}"
            + (f" @ ~{_format_money(float(price))}" if price else "")
            + f" (order_id={order.get('id')}, status={order.get('status')})\n"
        )

        if telegram.is_configured():
            telegram.send_trade_notification_sync(
                {
                    "symbol": symbol,
                    "action": action,
                    "qty": qty,
                    "price": float(price) if price else 0.0,
                    "status": order.get("status", "UNKNOWN"),
                }
            )

        _print_account_and_holdings(client)


if __name__ == "__main__":
    raise SystemExit(main())

