"""
Configuration management for Alpaca Smart Trade
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Alpaca API Configuration
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

    # Trading Configuration
    DEFAULT_STOCKS = os.getenv('DEFAULT_STOCKS', 'NVDA,MSFT,AMZN,GOOGL,TSLA,UNH,CRWD,V,ASML,PLTR').split(',')
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.10))
    MIN_ACCOUNT_BALANCE = float(os.getenv('MIN_ACCOUNT_BALANCE', 1000))
    ENABLE_PDT_PROTECTION = os.getenv('ENABLE_PDT_PROTECTION', 'True').lower() == 'true'

    # Analysis Configuration
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', 60))
    REGIME_PERIODS = [int(x) for x in os.getenv('REGIME_PERIODS', '20,50,200').split(',')]
    WALK_FORWARD_TRAIN_DAYS = int(os.getenv('WALK_FORWARD_TRAIN_DAYS', 30))
    WALK_FORWARD_TEST_DAYS = int(os.getenv('WALK_FORWARD_TEST_DAYS', 5))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        missing = []

        if not cls.ALPACA_API_KEY:
            missing.append('ALPACA_API_KEY')
        if not cls.ALPACA_SECRET_KEY:
            missing.append('ALPACA_SECRET_KEY')

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True

    @classmethod
    def is_paper_trading(cls):
        """Check if using paper trading"""
        return 'paper' in cls.ALPACA_BASE_URL.lower()
