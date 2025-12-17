"""
Interactive CLI prompt for manual trading with Alpaca Smart Trade.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from config import Config
from app.alpaca_client import AlpacaClient
from app.analysis.regime_switching import RegimeSwitchingAnalyzer
from app.analysis.walk_forward import WalkForwardOptimizer
from app.risk_manager import RiskManager
from app.decision_engine import DecisionEngine
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


def _get_mid_price(quote: Dict) -> float:
    bid = float(quote.get("bid_price", 0) or 0)
    ask = float(quote.get("ask_price", 0) or 0)
    if bid and ask:
        return (bid + ask) / 2.0
    return ask or bid or 0.0


def _analyze_symbol(
    client: AlpacaClient,
    decision_engine: DecisionEngine,
    risk_manager: RiskManager,
    regime_analyzer: RegimeSwitchingAnalyzer,
    walk_forward_optimizer: WalkForwardOptimizer,
    symbol: str,
) -> Dict:
    account = client.get_account()
    positions = client.get_positions()
    current_position = next((p for p in positions if p.get("symbol", "").upper() == symbol), None)

    quotes = client.get_latest_quotes([symbol])
    quote = quotes.get(symbol, {})
    current_price = _get_mid_price(quote)

    historical = client.get_historical_bars([symbol], days=Config.LOOKBACK_DAYS)
    df = historical.get(symbol)

    regime = regime_analyzer.analyze(df) if df is not None else {}
    wf = walk_forward_optimizer.optimize(df) if df is not None else {}

    regime_rec = decision_engine._interpret_regime(regime)  # intentional: CLI needs a provisional action
    wf_rec = decision_engine._interpret_walk_forward(wf)
    technical_score = (
        regime_rec["score"] * decision_engine.weights["regime_switching"]
        + wf_rec["score"] * decision_engine.weights["walk_forward"]
    )

    if technical_score > decision_engine.buy_threshold:
        suggested_action = "BUY"
    elif technical_score < decision_engine.sell_threshold:
        suggested_action = "SELL"
    else:
        suggested_action = "HOLD"

    if suggested_action == "HOLD":
        risk_eval = {
            "approved": True,
            "reason": "No trade suggested (HOLD)",
            "warnings": [],
            "position_size": 0,
            "position_value": 0.0,
        }
    elif current_price > 0:
        risk_eval = risk_manager.evaluate_trade(
            symbol=symbol,
            action=suggested_action,
            account=account,
            positions=positions,
            current_price=current_price,
        )
    else:
        risk_eval = {"approved": False, "reason": "No current price data"}

    decision = decision_engine.make_decision(
        symbol=symbol,
        regime_analysis=regime,
        walk_forward_analysis=wf,
        risk_evaluation=risk_eval,
        current_position=current_position,
    )

    return {
        "account": account,
        "positions": positions,
        "current_position": current_position,
        "quote": quote,
        "current_price": current_price,
        "regime": regime,
        "walk_forward": wf,
        "technical_score": technical_score,
        "suggested_action": decision.get("action", "HOLD"),
        "decision": decision,
        "risk_eval": risk_eval,
    }


def _confirm_trade(decision: Dict) -> bool:
    action = decision.get("action", "HOLD")
    if action == "HOLD":
        return False

    while True:
        raw = input(f"Execute suggested action ({action})? [y/N]: ").strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"", "n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def main() -> int:
    Config.validate()

    client = AlpacaClient()
    telegram = TelegramNotifier()
    risk_manager = RiskManager(client)
    decision_engine = DecisionEngine()
    regime_analyzer = RegimeSwitchingAnalyzer(sma_periods=Config.REGIME_PERIODS)
    walk_forward_optimizer = WalkForwardOptimizer(
        train_days=Config.WALK_FORWARD_TRAIN_DAYS,
        test_days=Config.WALK_FORWARD_TEST_DAYS,
    )

    print("\nAlpaca Smart Trade - Interactive Trader\n")
    _print_account_and_holdings(client)

    defaults = Config.DEFAULT_STOCKS
    while True:
        symbol = _pick_symbol(defaults)
        if symbol is None:
            print("Goodbye.")
            return 0

        analysis = _analyze_symbol(
            client=client,
            decision_engine=decision_engine,
            risk_manager=risk_manager,
            regime_analyzer=regime_analyzer,
            walk_forward_optimizer=walk_forward_optimizer,
            symbol=symbol,
        )

        decision = analysis["decision"]
        suggested_action = analysis["suggested_action"]
        current_price = float(analysis.get("current_price", 0) or 0)
        risk_eval = analysis.get("risk_eval", {})

        print("\n" + "-" * 72)
        print(f"Analysis for {symbol}")
        print("-" * 72)
        if current_price:
            print(f"Price (approx): {_format_money(current_price)}")
        print(f"Suggested Action: {suggested_action}  (confidence {(decision.get('confidence', 0) * 100):.1f}%)")
        for line in decision.get("reasoning", [])[:8]:
            print(f"- {line}")
        if not risk_eval.get("approved", True):
            print(f"\nBlocked by risk manager: {risk_eval.get('reason', 'Unknown')}")
        print("-" * 72 + "\n")

        if suggested_action == "HOLD" or not risk_eval.get("approved", True):
            input("Press Enter to continue...")
            continue

        if not _confirm_trade(decision):
            print("Skipped.")
            continue

        positions = client.get_positions()
        holdings = _get_holdings_map(positions)

        max_sell_qty = None
        default_qty = float(decision.get("position_size", 0) or 0)
        if suggested_action == "SELL":
            held = holdings.get(symbol, 0.0)
            if held <= 0:
                print(f"\nYou don't currently hold any shares of {symbol}; cannot SELL.\n")
                continue
            max_sell_qty = held
            default_qty = held

        if default_qty > 0:
            raw = input(f"Shares to {suggested_action} (Enter for default {default_qty:g}): ").strip()
            if raw == "":
                qty = default_qty
            else:
                try:
                    qty = float(raw)
                except ValueError:
                    print("Invalid quantity.")
                    continue
        else:
            qty = _pick_quantity(max_qty=max_sell_qty)
            if qty is None:
                continue

        if suggested_action == "SELL" and max_sell_qty is not None and qty > max_sell_qty:
            print("Quantity exceeds current holdings.")
            continue

        order = client.place_market_order(symbol=symbol, qty=qty, side=suggested_action.lower())

        print(
            f"\nConfirmed: {suggested_action} {qty:g} shares of {symbol}"
            + (f" @ ~{_format_money(float(current_price))}" if current_price else "")
            + f" (order_id={order.get('id')}, status={order.get('status')})\n"
        )

        if telegram.is_configured():
            telegram.send_trade_notification_sync(
                {
                    "symbol": symbol,
                    "action": suggested_action,
                    "qty": qty,
                    "price": float(current_price) if current_price else 0.0,
                    "status": order.get("status", "UNKNOWN"),
                }
            )

        _print_account_and_holdings(client)


if __name__ == "__main__":
    raise SystemExit(main())
