# 📊 Alpaca Smart Trade

An intelligent trading automation system that analyzes stocks using advanced algorithms and provides actionable trading recommendations with risk management.

![Paper Trading](https://img.shields.io/badge/Paper%20Trading-Supported-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18.2-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Features

### Advanced Analysis
- **Walk-Forward Optimization** - Backtests trading strategies using rolling windows
- **Regime-Switching Indicators** - Identifies market regimes (Bullish, Bearish, Sideways)
- **Technical Analysis** - RSI, MACD, ADX, Bollinger Bands, Moving Averages, and more

### Risk Management
- **Position Sizing** - Automatic calculation based on portfolio percentage
- **PDT Protection** - Pattern Day Trading rule enforcement
- **Account Balance Monitoring** - Ensures sufficient funds before trading
- **Portfolio Concentration Checks** - Prevents over-allocation

### Trading Automation
- **Manual Execution** - All trades require manual approval
- **Market & Limit Orders** - Support for multiple order types
- **Real-time Analysis** - Get recommendations on demand
- **Telegram Notifications** - Receive analysis reports via Telegram

### Beautiful UI
- **Modern Design** - Clean, responsive interface
- **Real-time Data** - Live account and position updates
- **Interactive Charts** - Detailed analysis visualizations
- **Mobile Friendly** - Works on all devices

## 🏗️ Architecture

```
alpaca_smart_trade/
├── backend/
│   ├── app/
│   │   ├── alpaca_client.py          # Alpaca API integration
│   │   ├── analysis/
│   │   │   ├── regime_switching.py   # Market regime analysis
│   │   │   └── walk_forward.py       # Walk-forward optimization
│   │   ├── risk_manager.py           # Risk management system
│   │   ├── decision_engine.py        # Trading decision logic
│   │   ├── telegram_bot.py           # Telegram integration
│   │   └── api.py                    # Flask REST API
│   ├── config.py                     # Configuration management
│   ├── requirements.txt              # Python dependencies
│   └── .env.example                  # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AccountSummary.js     # Account dashboard
│   │   │   ├── StockSelector.js      # Stock selection UI
│   │   │   ├── AnalysisResults.js    # Analysis display
│   │   │   ├── TradingPanel.js       # Trade execution UI
│   │   │   └── LoadingSpinner.js     # Loading indicator
│   │   ├── App.js                    # Main application
│   │   └── index.js                  # Entry point
│   └── package.json                  # Node dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Alpaca Trading Account (get one at [alpaca.markets](https://alpaca.markets))
- (Optional) Telegram Bot for notifications

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/alpaca_smart_trade.git
cd alpaca_smart_trade
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

**Required Environment Variables:**

```env
# Alpaca API Credentials (REQUIRED)
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Telegram Bot (OPTIONAL)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
DEFAULT_STOCKS=NVDA,MSFT,AMZN,GOOGL,TSLA,UNH,CRWD,V,ASML,PLTR
MAX_POSITION_SIZE=0.10
MIN_ACCOUNT_BALANCE=1000
ENABLE_PDT_PROTECTION=True
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app/api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The application will open at `http://localhost:3000`

## 📖 How to Use

### 1. Get Your Alpaca API Credentials

1. Sign up at [alpaca.markets](https://alpaca.markets)
2. Go to **Paper Trading** dashboard
3. Generate API keys (Keep these secure!)
4. Add them to your `.env` file

### 2. (Optional) Set Up Telegram Notifications

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token to `.env`
4. Start a chat with your bot
5. Get your chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response
   - Add it to `.env`

### 3. Run Analysis

1. **Select Stocks** - Choose from the default list or add custom symbols
2. **Click "Run Analysis"** - The system will:
   - Fetch historical market data
   - Run regime-switching analysis
   - Perform walk-forward optimization
   - Calculate risk metrics
   - Generate recommendations
3. **Review Results** - Examine the detailed analysis and recommendations
4. **Send to Telegram** (Optional) - Share the report with your Telegram bot
5. **Execute Trades** - Manually approve and execute recommended trades

## 🎓 Understanding the Analysis

### Walk-Forward Optimization

Tests trading strategies using a rolling window approach:
- **Training Window**: Optimizes strategy parameters on historical data
- **Testing Window**: Validates performance on out-of-sample data
- **Metrics**: Sharpe ratio, win rate, expected return, max drawdown

### Regime-Switching Indicators

Identifies the current market regime using technical indicators:
- **Bullish**: Strong upward trend, positive momentum
- **Bearish**: Strong downward trend, negative momentum
- **Sideways**: Range-bound, no clear trend

Technical indicators used:
- Moving Averages (SMA 20, 50, 200)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Bollinger Bands
- Stochastic Oscillator

### Risk Management

Protects your capital with multiple safety checks:
- **Position Size Limits**: Max 10% of portfolio per position
- **PDT Protection**: Prevents exceeding 3 day trades in 5 days
- **Account Balance**: Ensures minimum balance requirements
- **Concentration Checks**: Prevents over-allocation to few stocks

## 🛡️ Safety Features

- **Paper Trading Default**: Uses Alpaca paper trading by default
- **Manual Approval**: No automatic trade execution
- **Risk Warnings**: Clear warnings for risky trades
- **PDT Protection**: Built-in Pattern Day Trading safeguards
- **Position Limits**: Automatic position sizing

## 📊 API Endpoints

### Account & Positions
- `GET /api/account` - Get account information
- `GET /api/positions` - Get current positions

### Analysis
- `POST /api/analyze` - Run stock analysis
  ```json
  {
    "symbols": ["NVDA", "MSFT"],
    "lookback_days": 60
  }
  ```

### Trading
- `POST /api/execute-trade` - Execute a trade
  ```json
  {
    "symbol": "NVDA",
    "action": "BUY",
    "quantity": 10,
    "order_type": "market"
  }
  ```
- `GET /api/orders` - Get order history
- `DELETE /api/cancel-order/<order_id>` - Cancel an order
- `POST /api/close-position/<symbol>` - Close a position

### Notifications
- `POST /api/send-telegram` - Send analysis to Telegram

## 🔧 Configuration Options

Edit these in `backend/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_POSITION_SIZE` | Max % of portfolio per position | 0.10 (10%) |
| `MIN_ACCOUNT_BALANCE` | Minimum account balance | 1000 |
| `ENABLE_PDT_PROTECTION` | Enable PDT checks | True |
| `LOOKBACK_DAYS` | Days of historical data | 60 |
| `REGIME_PERIODS` | SMA periods for regime detection | 20,50,200 |
| `WALK_FORWARD_TRAIN_DAYS` | Training window size | 30 |
| `WALK_FORWARD_TEST_DAYS` | Testing window size | 5 |

## 🐛 Troubleshooting

### Backend Issues

**Error: "Missing required environment variables"**
- Check that your `.env` file has `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`

**Error: "Failed to get account info"**
- Verify your API keys are correct
- Check you're using the right base URL (paper vs live)

### Frontend Issues

**Error: "Failed to load account data"**
- Ensure backend is running on port 5000
- Check browser console for CORS errors

**Analysis not running**
- Check that stocks are selected
- Verify backend is running and accessible

## ⚠️ Important Warnings

1. **Paper Trading First**: Always test with paper trading before using real money
2. **Review Recommendations**: This is a tool to aid decision-making, not financial advice
3. **Understand Risks**: Trading involves risk of loss
4. **Monitor Regularly**: Check positions and account regularly
5. **Keep Credentials Safe**: Never commit your `.env` file to git

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Alpaca Markets](https://alpaca.markets) for the trading API
- Technical analysis libraries: `ta`, `pandas-ta`
- React and Flask communities

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review Alpaca API docs: https://docs.alpaca.markets

---

**Disclaimer**: This software is for educational purposes only. Trading involves risk. Past performance does not guarantee future results. Always do your own research and consult with financial professionals before making investment decisions.
