"""
User command handlers
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import TradingStrategy, WALLET_ADDRESSES, ADMIN_USER_IDS
from database import db
from handlers.utils import clear_awaiting_states
from market_data import market
import random

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    if not user.username:
        await update.message.reply_text(
            "⚠️ Username Required!\n\n"
            "Please set a Telegram username first:\n"
            "1. Go to Settings → Edit Profile\n"
            "2. Create a username\n"
            "3. Come back and use /start again\n\n"
            "A username is required for security and tracking."
        )
        return
    
    # Check if user is registered
    user_data = db.get_user(user.id)
    if user_data and len(user_data) >= 5 and user_data[3] and user_data[4]:
        await show_main_menu(update, context, user)
        return
    
    # Handle referral code from command args
    referred_by_id = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
        
        # Lookup referrer by code
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            
            if referrer:
                referred_by_id = referrer[0]
                referrer_username = referrer[1]
                
                # Notify user about referral
                await update.message.reply_text(
                    f"🎁 Welcome! You were referred by @{referrer_username}!\n\n"
                    f"Complete registration to activate your referral bonus.\n"
                    f"Your referrer will earn 5% when you make your first investment! 🚀"
                )
            else:
                logging.warning(f"Invalid referral code used: {referral_code}")
    
    # Store referral info for registration
    context.user_data['referred_by_id'] = referred_by_id
    context.user_data['registration_step'] = 'name'
    
    await update.message.reply_text(
        "🚀 Welcome to 🧠 𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 𝗔𝗶!\n\n"
        "To get started, please provide your full name:"
    )

async def show_main_menu(update, context, user):
    """Display the main menu with enhanced dashboard"""
    # Get user data for personalized greeting
    user_data = db.get_user(user.id)
    
    full_name = user_data[3] if user_data and user_data[3] else user.first_name
    current_balance = user_data[8] if user_data and len(user_data) > 8 else 0
    # Get current date
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Get top 5 cryptocurrencies by market cap
    try:
        crypto_prices = market.get_top_crypto_prices(limit=5)
        crypto_list = sorted(crypto_prices.items(), key=lambda x: x[1]['rank'])[:5]
        
        # Build crypto price display
        crypto_text = "💎 Top 5 Cryptocurrencies:\n"
        for crypto_id, info in crypto_list:
            change_emoji = "📈" if info['change_24h'] > 0 else "📉" if info['change_24h'] < 0 else "⚪"
            crypto_text += f"{change_emoji} {info['symbol']}: ${info['price']:,.2f} ({info['change_24h']:+.2f}%)\n"
    except Exception as e:
        logging.error(f"Error fetching crypto prices for dashboard: {e}")
        crypto_text = "💎 Market Data Loading...\n"
    
    # Define keyboard WITHOUT leaderboard
    keyboard = [
        [InlineKeyboardButton("💼 Portfolio", callback_data="portfolio"),
         InlineKeyboardButton("💸 Invest", callback_data="invest_menu")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile"),
         InlineKeyboardButton("📈 Live Prices", callback_data="live_prices")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq"),
         InlineKeyboardButton("📖 Help", callback_data="help")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🧠 𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 𝗔𝗶 

{current_date}

Hello {full_name}! 👋

Balance : ${current_balance:,.2f}

⚡ Auto Trading: ON 🟢
🤖 Bot Stat: Active 
⚙️ Active Strategies: All 🟢

{crypto_text}
━━━━━━━━━━━━━━
    """
    
    # Use permanent menu (don't auto-delete main menu)
    if update.message:
        sent_message = await update.message.reply_text(welcome_text.strip(), reply_markup=reply_markup, parse_mode='HTML')
        db.log_message(sent_message.chat_id, sent_message.message_id, user.id, 'main_menu', True)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text.strip(), reply_markup=reply_markup, parse_mode='HTML')
        db.log_message(update.callback_query.message.chat_id, update.callback_query.message.message_id, user.id, 'main_menu', True)

    clear_awaiting_states(context)


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user portfolio with recent profit activity"""
    user = update.effective_user
    
    try:
        user_data = db.get_user(user.id)
        if not user_data:
            error_msg = "❌ You're not registered yet. Use /start first!"
            if update.message:
                await update.message.reply_text(error_msg)
            else:
                await update.callback_query.message.edit_text(error_msg)
            return
        calculate_user_profits()
        user_data = db.get_user(user.id)  # Refresh data
        
        if len(user_data) < 14:
            logging.error(f"Incomplete user data for user {user.id}")
            error_msg = "❌ Account data incomplete. Please contact support."
            if update.message:
                await update.message.reply_text(error_msg)
            else:
                await update.callback_query.message.edit_text(error_msg)
            return
        
        # Unpack user data safely (Upgraded: 'plan' -> 'strategy')
        (user_id, username, first_name, full_name, email, reg_date, 
         strategy, total_invested, current_balance, profit_earned, 
         last_update, referral_code, referred_by, wallet_address) = user_data
        
        # Build portfolio text (Upgraded: 'Strategy' display)
        portfolio_text = f"""💼 𝗣𝗢𝗥𝗧𝗙𝗢𝗟𝗜𝗢

👤 Account Details:
• Username: @{username or 'N/A'}
• Strategy: {strategy if strategy else 'No active strategy'}
• Member Since: {reg_date[:10] if reg_date else 'Unknown'}

💰 Financial Summary:
• Total Invested: ${total_invested:,.2f}
• Current Balance: ${current_balance:,.2f}
• Total Bot Profit: ${profit_earned:,.2f}"""
        
        # Add ROI calculation
        if total_invested > 0:
            roi = ((current_balance / total_invested - 1) * 100)
            portfolio_text += f"\n• Crypto ROI: {roi:.2f}%"
        
        # Add daily earnings (Upgraded map with all strategies and 'expected_daily_return')
        # In portfolio_command function, update the daily earnings section:
        if total_invested > 0 and strategy:
            strategy_map = {
                'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
                'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
                'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
                'SCALPING': TradingStrategy.SCALPING.value,
                'ARBITRAGE': TradingStrategy.ARBITRAGE.value
            }
            strategy_info = strategy_map.get(strategy.upper())
            if strategy_info:
                # ✅ Calculate on current balance, not total_invested
                daily_earnings = current_balance * strategy_info['expected_daily_return']
                portfolio_text += f"\n\n💎 Daily Earnings: ${daily_earnings:.2f}"
                portfolio_text += f"\n📈 Growing on ${current_balance:,.2f}"
            
            portfolio_text += f"\n\n🎁 Referral Code: `{referral_code}`"
            portfolio_text += "\nShare your code and earn 5% commission!"
            portfolio_text += f"\n\n⏰ Profit Updates: Every 1-3 hours"
            portfolio_text += f"\n📊 Next Update: Within 1 hour"
            portfolio_text += f"\n💫 Variation: ±30% per update"
        keyboard = [
            [InlineKeyboardButton("💰 Invest More", callback_data="invest_menu"),
             InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("📜 History", callback_data="user_history"),
             InlineKeyboardButton("👥 Referrals", callback_data="referrals")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        
        if update.message:
            await update.message.reply_text(portfolio_text.strip(), reply_markup=reply_markup, parse_mode='HTML')
        elif update.callback_query:
            await update.callback_query.message.edit_text(portfolio_text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    
    except Exception as e:
        logging.error(f"Error in portfolio_command: {e}")
        error_text = "❌ Error loading portfolio. Please try again later."
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(error_text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text(error_text, reply_markup=reply_markup)

def calculate_user_profits(context=None):
    """Calculate and update user profits with hourly random profits"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get users with investments
            cursor.execute('''
                SELECT user_id, total_invested, current_balance, strategy, last_profit_update
                FROM users
                WHERE total_invested > 0 AND strategy IS NOT NULL
            ''')
            users = cursor.fetchall()
            
            for user_id, total_invested, current_balance, strategy, last_update in users:
                try:
                    last_update_date = datetime.fromisoformat(last_update)
                    hours_passed = int((datetime.now() - last_update_date).total_seconds() / 3600)
                    
                    if hours_passed >= 1:  # At least 1 hour passed
                        strategy_map = {
                            'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
                            'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
                            'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
                            'SCALPING': TradingStrategy.SCALPING.value,
                            'ARBITRAGE': TradingStrategy.ARBITRAGE.value
                        }
                        strategy_info = strategy_map.get(strategy.upper())
                        
                        if strategy_info and total_invested >= strategy_info['min_amount']:
                            daily_return = strategy_info['expected_daily_return']
                            
                            # Calculate hourly profit with randomness
                            total_profit = 0
                            starting_balance = current_balance
                            
                            for hour in range(min(hours_passed, 24)):
                                base_hourly_rate = daily_return / 24
                                random_factor = random.uniform(0.8, 1.3)
                                hourly_rate = base_hourly_rate * random_factor
                                hourly_profit = current_balance * hourly_rate
                                total_profit += hourly_profit
                                current_balance += hourly_profit
                            
                            new_balance = current_balance
                            
                            cursor.execute('''
                                UPDATE users
                                SET current_balance = ?, profit_earned = profit_earned + ?, last_profit_update = ?
                                WHERE user_id = ?
                            ''', (new_balance, total_profit, datetime.now().isoformat(), user_id))
                            
                            logging.info(f"Hourly profit calculated for user {user_id}: ${total_profit:.4f} over {hours_passed} hours")
                            
                            # Send notification if context is available and profit is significant
                            if context and total_profit > starting_balance * 0.001:
                                asyncio.create_task(send_profit_notification_with_context(context, user_id, total_profit, hours_passed, new_balance))
                
                except Exception as e:
                    logging.error(f"Error calculating profit for user {user_id}: {e}")
            
            conn.commit()
    
    except Exception as e:
        logging.error(f"Error in calculate_user_profits: {e}")

async def send_profit_notification_with_context(context, user_id, profit_amount, hours, new_balance):
    """Send auto-deleting notification using provided context"""
    try:
        if profit_amount > 0.001:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=f"💰 PROFIT UPDATE!\n\n"
                     f"📈 Added: ${profit_amount:.4f}\n"
                     f"💼 New Balance: ${new_balance:,.2f}\n"
                     f"⏰ Period: {hours} hour(s)\n\n"
                     f"💡 Auto-disappearing in 30s...",
                parse_mode='HTML'
            )
            
            # Schedule deletion
            asyncio.create_task(schedule_message_deletion_with_context(context, user_id, sent_message.message_id, 30))
            
    except Exception as e:
        logging.error(f"Failed to send profit notification to {user_id}: {e}")

async def schedule_message_deletion_with_context(context, chat_id, message_id, delay_seconds=30):
    """Schedule message deletion using provided context"""
    try:
        await asyncio.sleep(delay_seconds)
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.debug(f"Failed to auto-delete message {message_id}: {e}")

def get_random_wallet(crypto_type: str) -> str:
    """Get random wallet address for crypto type"""
    if crypto_type.lower() in WALLET_ADDRESSES:
        return random.choice(WALLET_ADDRESSES[crypto_type.lower()])
    return None