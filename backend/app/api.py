"""
Flask API for Alpaca Smart Trade
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import traceback

from config import Config
from app.alpaca_client import AlpacaClient
from app.analysis.regime_switching import RegimeSwitchingAnalyzer
from app.analysis.walk_forward import WalkForwardOptimizer
from app.risk_manager import RiskManager
from app.decision_engine import DecisionEngine
from app.telegram_bot import TelegramNotifier

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize components
alpaca_client = None
regime_analyzer = None
walk_forward_optimizer = None
risk_manager = None
decision_engine = None
telegram_notifier = None


def initialize_components():
    """Initialize all trading components"""
    global alpaca_client, regime_analyzer, walk_forward_optimizer
    global risk_manager, decision_engine, telegram_notifier

    try:
        Config.validate()

        alpaca_client = AlpacaClient()
        regime_analyzer = RegimeSwitchingAnalyzer(sma_periods=Config.REGIME_PERIODS)
        walk_forward_optimizer = WalkForwardOptimizer(
            train_days=Config.WALK_FORWARD_TRAIN_DAYS,
            test_days=Config.WALK_FORWARD_TEST_DAYS
        )
        risk_manager = RiskManager(alpaca_client)
        decision_engine = DecisionEngine()
        telegram_notifier = TelegramNotifier()

        print("✓ All components initialized successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to initialize components: {e}")
        return False


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'paper_trading': Config.is_paper_trading(),
        'telegram_configured': telegram_notifier.is_configured() if telegram_notifier else False
    })


@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    try:
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()
        risk_summary = risk_manager.get_risk_summary(account, positions)

        return jsonify({
            'success': True,
            'account': account,
            'positions': positions,
            'risk_summary': risk_summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions"""
    try:
        positions = alpaca_client.get_positions()

        return jsonify({
            'success': True,
            'positions': positions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_stocks():
    """
    Analyze stocks and generate trading recommendations

    Request body:
    {
        "symbols": ["NVDA", "MSFT", ...],
        "lookback_days": 60  # optional
    }
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', Config.DEFAULT_STOCKS)
        lookback_days = data.get('lookback_days', Config.LOOKBACK_DAYS)

        # Validate symbols
        if not symbols or not isinstance(symbols, list):
            return jsonify({
                'success': False,
                'error': 'Invalid symbols list'
            }), 400

        # Get account and positions
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()

        # Fetch historical data
        print(f"Fetching historical data for {len(symbols)} symbols...")
        historical_data = alpaca_client.get_historical_bars(
            symbols=symbols,
            days=lookback_days
        )

        # Perform regime-switching analysis
        print("Performing regime-switching analysis...")
        regime_results = regime_analyzer.analyze_multiple(historical_data)

        # Perform walk-forward optimization
        print("Performing walk-forward optimization...")
        wf_results = walk_forward_optimizer.optimize_multiple(historical_data)

        # Get risk summary
        risk_summary = risk_manager.get_risk_summary(account, positions)

        # Generate recommendations using decision engine
        print("Generating trading recommendations...")
        analysis = decision_engine.analyze_portfolio(
            symbols=symbols,
            regime_results=regime_results,
            wf_results=wf_results,
            risk_summary=risk_summary,
            positions=positions,
            account=account,
            risk_manager=risk_manager
        )

        # Add detailed breakdown for each symbol
        detailed_results = []
        for symbol in symbols:
            regime = regime_results.get(symbol, {})
            wf = wf_results.get(symbol, {})
            position = next((p for p in positions if p['symbol'] == symbol), None)

            # Find recommendation for this symbol
            recommendation = next(
                (r for r in analysis['all_recommendations'] if r['symbol'] == symbol),
                None
            )

            detailed_results.append({
                'symbol': symbol,
                'regime_analysis': regime,
                'walk_forward_analysis': wf,
                'current_position': position,
                'recommendation': recommendation
            })

        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'detailed_results': detailed_results,
            'account': account,
            'risk_summary': risk_summary
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/send-telegram', methods=['POST'])
def send_telegram():
    """
    Send analysis report to Telegram

    Request body:
    {
        "analysis": { ... }  # Analysis results from /api/analyze
    }
    """
    try:
        if not telegram_notifier.is_configured():
            return jsonify({
                'success': False,
                'error': 'Telegram is not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file'
            }), 400

        data = request.get_json()
        analysis = data.get('analysis')

        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Missing analysis data'
            }), 400

        # Send report
        success = telegram_notifier.send_analysis_report_sync(analysis)

        if success:
            return jsonify({
                'success': True,
                'message': 'Analysis report sent to Telegram successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send Telegram message'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/execute-trade', methods=['POST'])
def execute_trade():
    """
    Execute a trade

    Request body:
    {
        "symbol": "NVDA",
        "action": "BUY",  # or "SELL"
        "quantity": 10,
        "order_type": "market",  # or "limit"
        "limit_price": 450.00  # only for limit orders
    }
    """
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        action = data.get('action', '').upper()
        quantity = data.get('quantity')
        order_type = data.get('order_type', 'market').lower()
        limit_price = data.get('limit_price')

        # Validate inputs
        if not symbol or not action or not quantity:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, action, quantity'
            }), 400

        if action not in ['BUY', 'SELL']:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Must be BUY or SELL'
            }), 400

        # Get account and positions for risk check
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()

        # Get current price
        quotes = alpaca_client.get_latest_quotes([symbol])
        current_price = quotes.get(symbol, {}).get('ask_price', 0) if action == 'BUY' else quotes.get(symbol, {}).get('bid_price', 0)

        if not current_price:
            return jsonify({
                'success': False,
                'error': f'Could not get current price for {symbol}'
            }), 400

        # Perform risk check
        risk_eval = risk_manager.evaluate_trade(
            symbol=symbol,
            action=action,
            account=account,
            positions=positions,
            current_price=current_price
        )

        if not risk_eval['approved']:
            return jsonify({
                'success': False,
                'error': f"Trade blocked by risk management: {risk_eval['reason']}",
                'risk_evaluation': risk_eval
            }), 400

        # Execute the trade
        if order_type == 'market':
            order = alpaca_client.place_market_order(
                symbol=symbol,
                qty=quantity,
                side=action.lower()
            )
        elif order_type == 'limit':
            if not limit_price:
                return jsonify({
                    'success': False,
                    'error': 'limit_price required for limit orders'
                }), 400

            order = alpaca_client.place_limit_order(
                symbol=symbol,
                qty=quantity,
                side=action.lower(),
                limit_price=limit_price
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid order_type. Must be market or limit'
            }), 400

        # Send Telegram notification if configured
        if telegram_notifier.is_configured():
            telegram_notifier.send_trade_notification_sync({
                'symbol': symbol,
                'action': action,
                'qty': quantity,
                'price': current_price,
                'status': order.get('status', 'UNKNOWN')
            })

        return jsonify({
            'success': True,
            'order': order,
            'risk_evaluation': risk_eval
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get orders (open, closed, or all)"""
    try:
        status = request.args.get('status', 'all')
        orders = alpaca_client.get_orders(status=status)

        return jsonify({
            'success': True,
            'orders': orders
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cancel-order/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        success = alpaca_client.cancel_order(order_id)

        return jsonify({
            'success': success,
            'message': f'Order {order_id} cancelled' if success else 'Failed to cancel order'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/close-position/<symbol>', methods=['POST'])
def close_position(symbol):
    """Close a position"""
    try:
        data = request.get_json() or {}
        qty = data.get('qty')  # Optional: close partial position

        order = alpaca_client.close_position(symbol, qty=qty)

        # Send Telegram notification if configured
        if telegram_notifier.is_configured():
            telegram_notifier.send_trade_notification_sync({
                'symbol': symbol,
                'action': 'CLOSE',
                'qty': order.get('qty', 0),
                'price': 0,
                'status': order.get('status', 'UNKNOWN')
            })

        return jsonify({
            'success': True,
            'order': order
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'success': True,
        'config': {
            'default_stocks': Config.DEFAULT_STOCKS,
            'max_position_size': Config.MAX_POSITION_SIZE,
            'min_account_balance': Config.MIN_ACCOUNT_BALANCE,
            'enable_pdt_protection': Config.ENABLE_PDT_PROTECTION,
            'lookback_days': Config.LOOKBACK_DAYS,
            'regime_periods': Config.REGIME_PERIODS,
            'walk_forward_train_days': Config.WALK_FORWARD_TRAIN_DAYS,
            'walk_forward_test_days': Config.WALK_FORWARD_TEST_DAYS,
            'paper_trading': Config.is_paper_trading(),
            'telegram_configured': telegram_notifier.is_configured() if telegram_notifier else False
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Alpaca Smart Trade - Starting Backend Server")
    print("=" * 60)

    if initialize_components():
        print(f"\n🚀 Server starting on port {Config.FLASK_PORT}")
        print(f"📊 Paper Trading: {Config.is_paper_trading()}")
        print(f"💬 Telegram Configured: {telegram_notifier.is_configured()}")
        print(f"📈 Default Stocks: {', '.join(Config.DEFAULT_STOCKS)}")
        print("\n" + "=" * 60 + "\n")

        app.run(
            host='0.0.0.0',
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    else:
        print("\n✗ Failed to start server due to initialization errors")
        print("Please check your .env file and ensure all required variables are set")
