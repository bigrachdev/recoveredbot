"""
Configuration settings for the trading bot
"""
import os
from dotenv import load_dotenv

# LOAD ENVIRONMENT VARIABLES FIRST - before any other imports
load_dotenv()

from enum import Enum
from typing import Dict, List

# Bot Configuration from environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_USER_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_USER_IDS', '').split(',') if id.strip()]

# Trading Strategies (Upgraded with new return rates and amount ranges)
class TradingStrategy(Enum):
    TREND_FOLLOWING = {
        "name": "Trend Following (Stable Growth)",
        "description": "Follows market trends using moving averages to buy rising assets and sell falling ones.",
        "how_it_works": "Identifies and follows established market trends using moving averages and momentum indicators. Buys during uptrends, sells during downtrends.",
        "best_for": "Beginners and conservative investors",
        "min_amount": 500,
        "max_amount": 5000,
        "expected_daily_return": 0.0138  # 1.38% for entry-level investments
    }
    MOMENTUM_TRADING = {
        "name": "Momentum Trading (High Velocity)",
        "description": "Capitalizes on strong price movements, entering trades with high volume and RSI indicators.",
        "how_it_works": "Trades assets showing strong upward or downward momentum based on volume and price action. Captures short-term price movements.",
        "best_for": "Moderate risk tolerance investors",
        "min_amount": 6000,
        "max_amount": 15000,
        "expected_daily_return": 0.0185  # 1.85% for mid-tier growth
    }
    MEAN_REVERSION = {
        "name": "Mean Reversion (Balanced Recovery)",
        "description": "Bets on prices returning to historical averages after deviations, using Bollinger Bands.",
        "how_it_works": "Bets on prices returning to historical averages after deviations using Bollinger Bands and statistical analysis.",
        "best_for": "Experienced investors who understand market cycles",
        "min_amount": 16000,
        "max_amount": 30000,
        "expected_daily_return": 0.0226  # 2.26% for balanced strategies
    }
    SCALPING = {
        "name": "Scalping (Quick Hits)",
        "description": "Makes numerous small trades to capture tiny price changes, often using bots for high frequency.",
        "how_it_works": "Executes numerous small trades to capture tiny price changes using high-frequency trading algorithms and tight spreads.",
        "best_for": "Advanced traders with high risk tolerance",
        "min_amount": 31000,
        "max_amount": 50000,
        "expected_daily_return": 0.0283  # 2.83% for high-frequency trading
    }
    ARBITRAGE = {
        "name": "Arbitrage (Risk-Arbitrage)",
        "description": "Exploits price differences across exchanges for risk-free profits.",
        "how_it_works": "Simultaneously buys and sells the same asset on different exchanges to profit from price differences with minimal risk.",
        "best_for": "Institutional and high-net-worth investors",
        "min_amount": 51000,
        "max_amount": float('inf'),
        "expected_daily_return": 0.0314  # 3.14% for premium, high-capital strategies
    }

# Crypto Wallet Addresses from environment variables
WALLET_ADDRESSES = {
    'btc': [addr.strip() for addr in os.environ.get('BTC_WALLETS', '').split(',') if addr.strip()],
    'usdt': [addr.strip() for addr in os.environ.get('USDT_WALLETS', '').split(',') if addr.strip()],
    'sol': [addr.strip() for addr in os.environ.get('SOL_WALLETS', '').split(',') if addr.strip()],
    'ton': [addr.strip() for addr in os.environ.get('TON_WALLETS', '').split(',') if addr.strip()],
    'eth': [addr.strip() for addr in os.environ.get('ETH_WALLETS', '').split(',') if addr.strip()]
}

SUPPORTED_LANGUAGES = ['en', 'es', 'zh', 'ar']
DEFAULT_LANGUAGE = 'en'


# Validation to ensure required environment variables are set
def validate_config():
    """Validate that all required environment variables are set"""
    if not BOT_TOKEN:
        raise ValueError("Missing required environment variable: BOT_TOKEN")
    
    if not ADMIN_USER_IDS:
        raise ValueError("Missing required environment variable: ADMIN_USER_IDS")
    
    # Check if at least one wallet type has addresses
    wallet_types_with_addresses = [key for key, addresses in WALLET_ADDRESSES.items() if addresses]
    if not wallet_types_with_addresses:
        raise ValueError("No wallet addresses configured. Please set at least one wallet type in environment variables")

# Validate configuration on import
validate_config()

# Conversation states
REGISTER_NAME, REGISTER_EMAIL = range(2)
AWAITING_PAYMENT_DETAILS, AWAITING_WITHDRAW_AMOUNT = range(2, 4)
AWAITING_WITHDRAW_ADDRESS, AWAITING_BROADCAST_MESSAGE = range(4, 6)