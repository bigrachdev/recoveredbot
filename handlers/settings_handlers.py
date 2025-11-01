import logging
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from config import TradingStrategy
from handlers.utils import clear_awaiting_states

# ========== CALCULATOR FUNCTIONS ==========

async def show_investment_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show investment calculator menu"""
    text = """
📊 𝗜𝗡𝗩𝗘𝗦𝗧𝗠𝗘𝗡𝗧 𝗖𝗔𝗟𝗖𝗨𝗟𝗔𝗧𝗢𝗥

Select a strategy to calculate potential returns:
    """
    
    keyboard = [
        [InlineKeyboardButton("📈 Trend Following", callback_data="calc_strategy_TREND_FOLLOWING")],
        [InlineKeyboardButton("🚀 Momentum Trading", callback_data="calc_strategy_MOMENTUM_TRADING")],
        [InlineKeyboardButton("🔄 Mean Reversion", callback_data="calc_strategy_MEAN_REVERSION")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="calc_strategy_SCALPING")],
        [InlineKeyboardButton("💱 Arbitrage", callback_data="calc_strategy_ARBITRAGE")],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def handle_calc_strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle strategy selection for calculator"""
    strategy = data.split("_")[-1]  # e.g., "TREND_FOLLOWING"
    context.user_data['calc_strategy'] = strategy
    context.user_data['awaiting_settings_edit'] = 'calc_amount'
    
    strategy_map = {
        'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
        'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
        'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
        'SCALPING': TradingStrategy.SCALPING.value,
        'ARBITRAGE': TradingStrategy.ARBITRAGE.value
    }
    
    strategy_info = strategy_map.get(strategy)
    if not strategy_info:
        await update.callback_query.message.edit_text("❌ Invalid strategy selected.")
        return
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="settings_calculator")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"📊 Selected Strategy: {strategy_info['name']}\n"
        f"📈 Daily Return: {strategy_info['expected_daily_return'] * 100:.2f}%\n"
        f"💰 Minimum: ${strategy_info['min_amount']:,}\n\n"
        "Please enter your investment amount in USD (e.g., 1000):",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_calc_time_periods(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float, strategy_info: dict):
    """Show time period selection buttons for calculator"""
    daily_return = strategy_info['expected_daily_return']
    
    # Calculate quick previews for buttons
    profit_30 = amount * ((1 + daily_return) ** 30) - amount
    profit_60 = amount * ((1 + daily_return) ** 60) - amount
    profit_90 = amount * ((1 + daily_return) ** 90) - amount
    
    text = f"""
💰 CALCULATE PROFITS

Strategy: {strategy_info['name']}
Investment: ${amount:,.2f}
Daily Return: {daily_return * 100:.2f}%

Select time period to see your projected returns:
    """
    
    keyboard = [
        [InlineKeyboardButton(f"📅 30 Days (+${profit_30:,.2f})", callback_data=f"calc_period_30")],
        [InlineKeyboardButton(f"📅 60 Days (+${profit_60:,.2f})", callback_data=f"calc_period_60")],
        [InlineKeyboardButton(f"📅 90 Days (+${profit_90:,.2f})", callback_data=f"calc_period_90")],
        [InlineKeyboardButton("📝 Custom Days", callback_data="calc_period_custom")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_calculator")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_calc_period_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle time period selection for calculator"""
    period = data.split("_")[-1]  # e.g., "30", "60", "90", or "custom"
    
    if period == "custom":
        context.user_data['awaiting_settings_edit'] = 'calc_duration'
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="settings_calculator")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            "📝 CUSTOM DURATION\n\n"
            "Enter the number of days (e.g., 45, 120, 365):\n\n"
            "💡 Tip: Try different durations to find your optimal investment period!",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        days = int(period)
        await show_calc_results(update, context, days)

async def show_calc_results(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    """Show detailed calculation results"""
    strategy = context.user_data.get('calc_strategy')
    amount = context.user_data.get('calc_amount')
    
    if not strategy or not amount:
        await update.callback_query.message.edit_text("❌ Session expired. Please start calculator again.")
        return
    
    strategy_map = {
        'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
        'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
        'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
        'SCALPING': TradingStrategy.SCALPING.value,
        'ARBITRAGE': TradingStrategy.ARBITRAGE.value
    }
    strategy_info = strategy_map.get(strategy.upper())
    
    if not strategy_info:
        await update.callback_query.message.edit_text("❌ Invalid strategy.")
        return
    
    daily_return = strategy_info['expected_daily_return']
    
    # Calculate with compound interest
    total = amount * ((1 + daily_return) ** days)
    profit = total - amount
    
    # Calculate ROI
    roi_percent = (profit / amount) * 100
    
    # Calculate daily average
    avg_daily_profit = profit / days
    
    # Calculate break-even (days to double)
    if daily_return > 0:
        break_even_days = math.log(2) / math.log(1 + daily_return)
    else:
        break_even_days = float('inf')
    
    # Risk-adjusted estimate (92% of projected)
    risk_adjusted = profit * 0.92
    
    text = f"""
📊 PROFIT PROJECTION

🎯 Strategy: {strategy_info['name']}
💰 Investment: ${amount:,.2f}
📅 Duration: {days} days
📈 Daily Return: {daily_return * 100:.2f}%

💵 PROJECTED RESULTS:
━━━━━━━━━━━━━━━━━━━━
• Total Profit: ${profit:,.2f}
• Final Balance: ${total:,.2f}
• ROI: {roi_percent:.1f}%
• Avg Daily: ${avg_daily_profit:.2f}

📊 BENCHMARKS:
• Days to Double: {break_even_days:.0f} days
• Risk-Adjusted: ${risk_adjusted:,.2f}
• Monthly Equiv: ${(profit/days)*30:,.2f}
• Annual Equiv: ${(profit/days)*365:,.2f}

💡 This is a projection based on consistent daily returns with compound interest. Actual results may vary based on market conditions.
    """
    
    keyboard = [
        [InlineKeyboardButton("📅 Try Different Days", callback_data=f"calc_recalc")],
        [InlineKeyboardButton("💰 Change Amount", callback_data=f"calc_strategy_{strategy}")],
        [InlineKeyboardButton("🚀 Invest Now", callback_data="invest_menu")],
        [InlineKeyboardButton("🔙 Calculator Menu", callback_data="settings_calculator")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text.strip(),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text.strip(),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

# ========== SETTINGS CALLBACK HANDLER ==========

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle settings-related callbacks"""

    if data == "settings_cancel_edit":
        # Clear ALL awaiting states
        context.user_data.pop('awaiting_settings_edit', None)
        context.user_data.pop('edit_field', None)
        context.user_data.pop('edit_user_id', None)
        
        await show_settings_menu(update, context)
        return

    if data == "settings_menu":
        await show_settings_menu(update, context)
    elif data == "settings_edit_name":
        await setup_name_edit(update, context)
    elif data == "settings_edit_email":
        await setup_email_edit(update, context)
    elif data == "settings_edit_wallet":
        await setup_wallet_edit(update, context)
    elif data == "settings_delete_account":
        await confirm_account_deletion(update, context)
    elif data == "settings_confirm_delete":
        await delete_user_account(update, context)
    elif data == "settings_calculator":
        await show_investment_calculator(update, context)
    elif data.startswith("calc_strategy_"):
        await handle_calc_strategy_selection(update, context, data)
    elif data.startswith("calc_period_"):
        await handle_calc_period_selection(update, context, data)
    elif data == "calc_recalc":
        strategy = context.user_data.get('calc_strategy')
        if strategy:
            await show_calc_time_periods(update, context, context.user_data['calc_amount'], 
                                       TradingStrategy[strategy].value)
        else:
            await show_investment_calculator(update, context)

# ========== TEXT INPUT HANDLER ==========

async def handle_settings_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle text input for settings edits"""
    edit_type = context.user_data.get('awaiting_settings_edit')
    
    if not edit_type:
        return False
    
    user = update.effective_user
    
    try:
        if edit_type == 'calc_amount':
            try:
                amount = float(text.replace('$', '').replace(',', ''))
                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be positive. Please enter a valid amount:")
                    return True
                
                strategy = context.user_data.get('calc_strategy')
                if not strategy:
                    await update.message.reply_text("❌ Strategy not selected. Please start over.")
                    return True
                
                strategy_map = {
                    'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
                    'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
                    'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
                    'SCALPING': TradingStrategy.SCALPING.value,
                    'ARBITRAGE': TradingStrategy.ARBITRAGE.value
                }
                strategy_info = strategy_map.get(strategy.upper())
                
                if not strategy_info:
                    await update.message.reply_text("❌ Invalid strategy. Please start again.")
                    return True
                
                # Check minimum investment
                if amount < strategy_info['min_amount']:
                    await update.message.reply_text(
                        f"❌ Minimum investment for {strategy_info['name']} is ${strategy_info['min_amount']:,}. "
                        f"Please enter at least ${strategy_info['min_amount']:,}:"
                    )
                    return True
                
                context.user_data['calc_amount'] = amount
                await show_calc_time_periods(update, context, amount, strategy_info)
                return True
                
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a number (e.g., 1000):")
                return True
        
        elif edit_type == 'calc_duration':
            try:
                days = int(text)
                if days <= 0:
                    await update.message.reply_text("❌ Duration must be positive. Please enter a valid number of days:")
                    return True
                
                await show_calc_results(update, context, days)
                return True
                
            except ValueError:
                await update.message.reply_text("❌ Invalid duration. Please enter a whole number (e.g., 30):")
                return True
        
        # ... (rest of your existing text handlers for name, email, wallet)
        
        return False
        
    except Exception as e:
        logging.error(f"Error handling settings input: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return True

# ========== SETTINGS MENU FUNCTIONS ==========

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the settings menu"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.callback_query.message.edit_text("❌ You're not registered yet. Use /start first!")
        return
    
    username = user_data[1] if len(user_data) > 1 else None
    full_name = user_data[3] if len(user_data) > 3 else None
    email = user_data[4] if len(user_data) > 4 else None
    wallet_address = get_user_wallet_address(user.id)
    
    text = f"""
⚙️ 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦

👤 Current Information:
• Username: @{username or 'N/A'}
• Full Name: {full_name or 'Not set'}
• Email: {email or 'Not set'}
• Wallet Address: {wallet_address[:20] + '...' if wallet_address else 'Not set'}

Select an option below to manage your account:
    """
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data="settings_edit_name"),
         InlineKeyboardButton("📧 Edit Email", callback_data="settings_edit_email")],
        [InlineKeyboardButton("💳 Edit Wallet", callback_data="settings_edit_wallet")],
        [InlineKeyboardButton("📊 Investment Calculator", callback_data="settings_calculator")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="settings_delete_account")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)
    
async def setup_name_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup name editing"""
    context.user_data['awaiting_settings_edit'] = 'name'
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="settings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "✏️ 𝗘𝗗𝗜𝗧 𝗡𝗔𝗠𝗘\n\n"
        "Please enter your new full name (minimum 2 characters):\n\n"
        "Type your new name below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def setup_email_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup email editing"""
    context.user_data['awaiting_settings_edit'] = 'email'
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="settings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "📧 𝗘𝗗𝗜𝗧 𝗘𝗠𝗔𝗜𝗟\n\n"
        "Please enter your new email address:\n\n"
        "Example: user@example.com\n\n"
        "Type your new email below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def setup_wallet_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup wallet address editing"""
    user = update.effective_user
    current_wallet = get_user_wallet_address(user.id)
    
    context.user_data['awaiting_settings_edit'] = 'wallet'
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="settings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "💳 𝗘𝗗𝗜𝗧 𝗪𝗔𝗟𝗟𝗘𝗧 𝗔𝗗𝗗𝗥𝗘𝗦𝗦\n\n"
    if current_wallet:
        text += f"Current Wallet: `{current_wallet}`\n\n"
    text += (
        "Please enter your USDT wallet address (TRC20 network only):\n\n"
        "⚠️ Important:\n"
        "• Only TRC20 USDT addresses accepted\n"
        "• Must start with 'T'\n"
        "• Must be exactly 34 characters\n"
        "• Double-check carefully!\n\n"
        "Type your wallet address below:"
    )
    
    await update.callback_query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def confirm_account_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation for account deletion"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.callback_query.message.edit_text("❌ User data not found.")
        return
    
    keyboard = [
        [InlineKeyboardButton("⚠️ YES, DELETE MY ACCOUNT", callback_data="settings_confirm_delete")],
        [InlineKeyboardButton("❌ Cancel", callback_data="settings_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "⚠️ CONFIRM ACCOUNT DELETION\n\n"
        "Are you absolutely sure you want to delete your account?\n\n"
        "This will permanently delete:\n"
        "• Your profile and account data\n"
        "• All investment records\n"
        "• Transaction history\n"
        "• Referral information\n\n"
        "⚠️ THIS CANNOT BE UNDONE!\n\n"
        "Note: Please withdraw all funds before deleting your account.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def delete_user_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete user account from database"""
    user = update.effective_user
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete user data from all tables
            cursor.execute('DELETE FROM investments WHERE user_id = ?', (user.id,))
            cursor.execute('DELETE FROM withdrawals WHERE user_id = ?', (user.id,))
            cursor.execute('DELETE FROM referrals WHERE referrer_id = ? OR referred_id = ?', (user.id, user.id))
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user.id,))
            
            conn.commit()
        
        await update.callback_query.message.edit_text(
            "✅ ACCOUNT DELETED\n\n"
            "Your account has been permanently deleted.\n\n"
            "We're sorry to see you go! If you change your mind, "
            "you can always register again with /start.\n\n"
            "Thank you for using 𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 𝗔𝗶! 👋"
        )
        
        # Clear user data from context
        context.user_data.clear()
        
    except Exception as e:
        logging.error(f"Error deleting user account {user.id}: {e}")
        await update.callback_query.message.edit_text(
            f"❌ Error deleting account: {str(e)}\n\n"
            "Please contact support for assistance.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Settings", callback_data="settings_menu")]])
        )

async def handle_settings_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle text input for settings edits"""
    edit_type = context.user_data.get('awaiting_settings_edit')
    
    if not edit_type:
        return False  # Not a settings edit
    
    user = update.effective_user
    
    try:
        if edit_type == 'name':
            # Validate name
            if len(text) < 2:
                await update.message.reply_text("❌ Name must be at least 2 characters long. Please try again:")
                return True
            
            # Update name in database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (text, user.id))
                conn.commit()
            
            await update.message.reply_text(
                f"✅ NAME UPDATED\n\nYour name has been changed to: {text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Back to Settings", callback_data="settings_menu")]]),
                parse_mode='HTML'
            )
        
        elif edit_type == 'email':
            # Validate email
            if '@' not in text or '.' not in text:
                await update.message.reply_text("❌ Invalid email format. Please enter a valid email address:")
                return True
            
            # Update email in database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET email = ? WHERE user_id = ?', (text, user.id))
                conn.commit()
            
            await update.message.reply_text(
                f"✅ EMAIL UPDATED\n\nYour email has been changed to: {text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Back to Settings", callback_data="settings_menu")]]),
                parse_mode='HTML'
            )
        
        elif edit_type == 'wallet':
            # Validate wallet address (TRC20 USDT)
            if not text.startswith('T') or len(text) != 34:
                await update.message.reply_text(
                    "❌ Invalid USDT TRC20 address format.\n\n"
                    "TRC20 addresses should:\n"
                    "• Start with 'T'\n"
                    "• Be exactly 34 characters long\n\n"
                    "Please provide a valid address:"
                )
                return True
            
            # Update wallet address in database
            set_user_wallet_address(user.id, text)
            
            await update.message.reply_text(
                f"✅ WALLET ADDRESS UPDATED\n\nYour wallet address has been saved:\n`{text}`\n\n"
                "This address will be used for all future withdrawals.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Back to Settings", callback_data="settings_menu")]]),
                parse_mode='HTML'
            )
        
        elif edit_type == 'calc_amount':
            try:
                amount = float(text.replace('$', '').replace(',', ''))
                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be positive. Please enter a valid amount:")
                    return True
                
                context.user_data['calc_amount'] = amount
                context.user_data['awaiting_settings_edit'] = 'calc_duration'
                
                await update.message.reply_text(
                    f"✅ Amount set: ${amount:,.2f}\n\n"
                    "Enter duration in days (e.g., 30):",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="settings_calculator")]]),
                    parse_mode='HTML'
                )
                return True
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a number (e.g., 1000):")
                return True
        
        elif edit_type == 'calc_duration':
            try:
                days = int(text)
                if days <= 0:
                    await update.message.reply_text("❌ Duration must be positive. Please enter a valid number of days:")
                    return True
                
                strategy = context.user_data.get('calc_strategy')
                amount = context.user_data.get('calc_amount')
                
                if not strategy or not amount:
                    await update.message.reply_text("❌ Session error. Please start calculator again.")
                    context.user_data.pop('awaiting_settings_edit', None)
                    return True
                
                strategy_map = {
                    'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
                    'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
                    'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
                    'SCALPING': TradingStrategy.SCALPING.value,
                    'ARBITRAGE': TradingStrategy.ARBITRAGE.value
                }
                strategy_info = strategy_map.get(strategy.upper())
                
                if not strategy_info:
                    await update.message.reply_text("❌ Invalid strategy. Please start again.")
                    context.user_data.pop('awaiting_settings_edit', None)
                    return True
                
                daily_return = strategy_info['expected_daily_return']
                
                # Calculate compound interest
                total = amount * ((1 + daily_return) ** days)
                profit = total - amount
                
                # Simple simulation with volatility
                import random
                current_amount = amount
                for day in range(days):
                    # Add realistic volatility based on strategy risk level
                    volatility_factor = {
                        'TREND_FOLLOWING': 0.008,      # 0.8% volatility
                        'MOMENTUM_TRADING': 0.012,     # 1.2% volatility  
                        'MEAN_REVERSION': 0.010,       # 1.0% volatility
                        'SCALPING': 0.015,             # 1.5% volatility
                        'ARBITRAGE': 0.006             # 0.6% volatility (lowest - arbitrage)
                    }.get(strategy.upper(), 0.010)
                    
                    daily_change = daily_return + random.uniform(-volatility_factor, volatility_factor)
                    current_amount *= (1 + daily_change)
                
                sim_profits = current_amount - amount
                risk_adjusted = profit * 0.92  # 8% risk adjustment factor
                
                # Calculate days to double investment using compound interest formula
                # amount * (1 + daily_return)^days = 2 * amount
                # (1 + daily_return)^days = 2
                # days = log(2) / log(1 + daily_return)
                import math
                if daily_return > 0:
                    break_even_days = math.log(2) / math.log(1 + daily_return)
                else:
                    break_even_days = float('inf')
                
                # Strategy-specific insights
                strategy_insights = {
                    'TREND_FOLLOWING': "Stable growth with low volatility. Good for beginners.",
                    'MOMENTUM_TRADING': "Higher returns with moderate risk. Requires active monitoring.",
                    'MEAN_REVERSION': "Balanced approach. Works well in ranging markets.",
                    'SCALPING': "High frequency trading. Best for experienced traders.",
                    'ARBITRAGE': "Lowest risk premium strategy. Requires large capital."
                }
                
                await update.message.reply_text(
                    f"📊 𝗣𝗥𝗢𝗝𝗘𝗖𝗧𝗘𝗗 𝗥𝗘𝗧𝗨𝗥𝗡𝗦\n\n"
                    f"💰 Strategy: {strategy_info['name']}\n"
                    f"📈 Investment: ${amount:,.2f}\n"
                    f"⏰ Duration: {days} days\n"
                    f"🎯 Daily Return: {daily_return * 100:.2f}%\n"
                    f"📊 Expected Annual Return: {((1 + daily_return) ** 365 - 1) * 100:.1f}%\n\n"
                    f"💵 Estimated Profit: ${profit:,.2f}\n"
                    f"🏦 Total Value: ${total:,.2f}\n\n"
                    f"🎲 Simulated Profit (w/ Volatility): ${sim_profits:,.2f}\n"
                    f"🛡️ Risk-Adjusted Estimate: ${risk_adjusted:,.2f}\n"
                    f"⏱️ Days to Double: {break_even_days:.0f} days\n\n"
                    f"💡 AI Insight: {strategy_insights.get(strategy.upper(), 'Consider diversifying across strategies.')}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Calculate Again", callback_data="settings_calculator")],
                        [InlineKeyboardButton("⚙️ Back to Settings", callback_data="settings_menu")]
                    ]),
                    parse_mode='HTML'
                )
                
                # Clear calculator data
                context.user_data.pop('calc_strategy', None)
                context.user_data.pop('calc_amount', None)
                context.user_data.pop('awaiting_settings_edit', None)
                return True
                
            except ValueError:
                await update.message.reply_text("❌ Invalid duration. Please enter a whole number (e.g., 30):")
                return True
        
        return True
    
    except Exception as e:
        logging.error(f"Error handling settings input: {e}")
        await update.message.reply_text(f"❌ Error updating settings: {str(e)}")
        return True
    
def get_user_wallet_address(user_id: int) -> str:
    """Get user's stored wallet address"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'wallet_address' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN wallet_address TEXT')
                conn.commit()
            
            cursor.execute('SELECT wallet_address FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
    except Exception as e:
        logging.error(f"Error getting wallet address: {e}")
        return None

def set_user_wallet_address(user_id: int, wallet_address: str) -> bool:
    """Set user's wallet address"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'wallet_address' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN wallet_address TEXT')
            
            cursor.execute('UPDATE users SET wallet_address = ? WHERE user_id = ?', (wallet_address, user_id))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Error setting wallet address: {e}")
        return False