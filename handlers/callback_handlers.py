"""
Callback query handlers for inline keyboards
"""
import logging
import qrcode
from io import BytesIO
import requests
from tkinter.constants import PAGES
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import yfinance as yf
from config import TradingStrategy, ADMIN_USER_IDS
from database import db
from handlers.admin_handlers import handle_admin_callback
from handlers.message_handlers import notify_admins_new_withdrawal
from handlers.user_handlers import show_main_menu, get_random_wallet
from config import ADMIN_USER_IDS
import asyncio
from handlers.utils import clear_awaiting_states
from market_data import market

qr = qrcode.QRCode()
qr.add_data("test")
print("✅ QR code package working!")
print("✅ Requests package working!")

async def schedule_message_deletion(context, chat_id, message_id, delay_seconds=120):
    """Schedule a message for deletion after delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.error(f"Failed to delete message {message_id}: {e}")

async def send_temporary_message(update, context, text, reply_markup=None, parse_mode=None, delete_after=120):
    """Send a message that will be auto-deleted"""
    if update.message:
        sent_message = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        # Schedule deletion of both user message and bot response
        asyncio.create_task(schedule_message_deletion(context, update.message.chat_id, update.message.message_id, delete_after))
        asyncio.create_task(schedule_message_deletion(context, sent_message.chat_id, sent_message.message_id, delete_after))
        return sent_message
    elif update.callback_query:
        # For callback queries, edit the message and schedule deletion
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        asyncio.create_task(schedule_message_deletion(context, update.callback_query.message.chat_id, 
                                                    update.callback_query.message.message_id, delete_after))
        return update.callback_query.message
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query handler - handles ALL callback queries"""
     


    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user

    if data in ["invest_menu", "main_menu", "settings_cancel_edit", "withdraw"]:
        # Clear ALL awaiting states
        for key in ['awaiting_settings_edit', 'awaiting_investment_amount', 
                   'awaiting_payment_details', 'awaiting_withdraw_amount',
                   'awaiting_tx_details', 'investment_data']:
            context.user_data.pop(key, None)

    try:
        # Main navigation
        if data == "main_menu":
            await show_main_menu(update, context, user)
        
        elif data == "crypto_strategies":
            await show_crypto_strategies(update, context)

        elif data == "portfolio":
            from handlers.user_handlers import portfolio_command
            await portfolio_command(update, context)
        
        elif data == "refresh_portfolio":
            from handlers.user_handlers import portfolio_command, calculate_user_profits
            calculate_user_profits()
            await portfolio_command(update, context)
        
        elif data == "invest_menu":
            await show_invest_menu(update, context)
        
        elif data == "withdraw":
            await show_withdraw_menu(update, context)
       
        elif data.startswith("withdraw_"):
            await handle_withdrawal_options(update, context, data)
        
        # Withdrawal confirmation callback
        elif data.startswith("confirm_withdraw_"):
            await process_withdrawal_confirmation(update, context, data)
            
            
        elif data == "live_prices":
            await show_live_prices_menu(update, context)
        
        # FIXED: Handle live_crypto with pagination
        elif data == "live_crypto" or data.startswith("live_crypto_"):
            await show_live_crypto_prices(update, context)
        
        elif data == "referrals":
            await show_referrals(update, context)
            
        elif data == "leaderboard":
            await show_leaderboard(update, context)
        
        elif data == "profile":
            await show_profile(update, context)
        
        elif data == "help":
            await show_help(update, context)
        
        elif data == "faq":
            await show_faq(update, context)

        elif data == "settings_menu":
            from handlers.settings_handlers import show_settings_menu
            await show_settings_menu(update, context)    
        # Settings callbacks
        elif data.startswith("settings_"):
            from handlers.settings_handlers import handle_settings_callback
            await handle_settings_callback(update, context, data)

        elif data.startswith("calc_strategy_"):
            from handlers.settings_handlers import handle_calc_strategy_selection
            await handle_calc_strategy_selection(update, context, data)

        elif data.startswith("calc_period_"):
            from handlers.settings_handlers import handle_calc_period_selection
            await handle_calc_period_selection(update, context, data)

        elif data == "calc_recalc":
            from handlers.settings_handlers import handle_settings_callback
            await handle_settings_callback(update, context, data)

        # Investment flow - FIXED: Handle strategy info and selection
        elif data.startswith("strategy_info_"):
            await show_strategy_details(update, context, data)
        
        elif data.startswith("strategy_select_"):
            await handle_strategy_selection(update, context, data)
        
        elif data.startswith("crypto_"):
            await handle_crypto_selection(update, context, data)
        
        elif data == "confirm_payment":
            await handle_payment_confirmation(update, context)
        
        elif data == "user_history":
            await show_user_transaction_history(update, context)

        elif data == "user_history" or data.startswith("user_history_page_"):
            page = 0 if data == "user_history" else int(data.split("_")[-1])
            await show_user_transaction_history(update, context, page)


        # Admin callbacks
        elif data.startswith("admin_"):
            if user.id in ADMIN_USER_IDS:
                logging.info(f"Routing admin callback: {data}")
                await handle_admin_callback(update, context, data)  # Log before call
            else:
                await query.message.edit_text(
                    "❌ You do not have permission to access the admin panel.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]])
                )
        
        else:
            await query.message.edit_text(
                "❌ Unknown action. Returning to main menu.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]])
            )
    
    except Exception as e:
        logging.error(f"Error in callback handler for '{data}': {e}")
        await query.message.edit_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]])
        )

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle all admin-related callbacks"""
    from handlers.admin_handlers import handle_admin_callback, admin_command
    
    if data == "admin_panel":
        clear_awaiting_states(context)
        await admin_command(update, context)
    else:
        await handle_admin_callback(update, context, data)

async def show_invest_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show investment options menu (Upgraded to reference strategies)"""
    keyboard = [
        [InlineKeyboardButton("💰 Strategies", callback_data="crypto_strategies")],  # Updated callback
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
💰 𝗜𝗡𝗩𝗘𝗦𝗧𝗠𝗘𝗡𝗧 𝗢𝗣𝗧𝗜𝗢𝗡𝗦

Choose your investment type:

🤖 𝗧𝗥𝗔𝗗𝗜𝗡𝗚  𝗦𝗧𝗥𝗔𝗧𝗘𝗚𝗜𝗘𝗦

Automated daily profits with our tiered strategies:
- Trend Following: 1.38% daily (Min: $500)
- Momentum Trading: 1.85% daily (Min: $6,000) 
- Mean Reversion: 2.26% daily (Min: $16,000)
- Scalping: 2.83% daily (Min: $31,000)
- Arbitrage: 3.14% daily (Min: $51,000)


Your investment journey starts here! 👇
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    
async def show_crypto_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show crypto investment strategies with brief overview"""
    keyboard = [
        [InlineKeyboardButton("🥉 Trend Following", callback_data="strategy_info_trendfollowing")],
        [InlineKeyboardButton("🥈 Momentum Trading", callback_data="strategy_info_momentumtrading")],
        [InlineKeyboardButton("🥇 Mean Reversion", callback_data="strategy_info_meanreversion")],
        [InlineKeyboardButton("🏆 Scalping", callback_data="strategy_info_scalping")],
        [InlineKeyboardButton("💎 Arbitrage", callback_data="strategy_info_arbitrage")],
        [InlineKeyboardButton("🔙 Invest Menu", callback_data="invest_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
🤖 𝗧𝗥𝗔𝗗𝗜𝗡𝗚 𝗦𝗧𝗥𝗔𝗧𝗘𝗚𝗜𝗘𝗦

🥉 TREND FOLLOWING - Perfect for Beginners
• Range: $500 - $5,000
• Daily Return: 1.38%

🥈 MOMENTUM TRADING - Balanced Approach  
• Range: $6,000 - $15,000
• Daily Return: 1.85%

🥇 MEAN REVERSION - Recovery Focused
• Range: $16,000 - $30,000
• Daily Return: 2.26%

🏆 SCALPING - Quick Profits
• Range: $31,000 - $50,000
• Daily Return: 2.83%

💎 ARBITRAGE - Premium Strategy
• Range: $51,000+
• Daily Return: 3.14%

Select strategy for details: 👇
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)

async def show_strategy_details(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Show detailed strategy information before selection"""
    strategy_type = data.split("_")[2]  # e.g., "trendfollowing"
    
    strategy_map = {
        "trendfollowing": TradingStrategy.TREND_FOLLOWING.value,
        "momentumtrading": TradingStrategy.MOMENTUM_TRADING.value,
        "meanreversion": TradingStrategy.MEAN_REVERSION.value,
        "scalping": TradingStrategy.SCALPING.value,
        "arbitrage": TradingStrategy.ARBITRAGE.value
    }
    
    strategy_info = strategy_map.get(strategy_type)
    if not strategy_info:
        await update.callback_query.message.edit_text("❌ Invalid strategy selected.")
        return
    
    daily_return = strategy_info['expected_daily_return']
    monthly_return = ((1 + daily_return) ** 30 - 1) * 100
    annual_return = ((1 + daily_return) ** 365 - 1) * 100
    
    keyboard = [
        [InlineKeyboardButton("🚀 Use This Strategy", callback_data=f"strategy_select_{strategy_type}")],
        [InlineKeyboardButton("🔙 Back to Strategies", callback_data="crypto_strategies")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎯 {strategy_info['name'].upper()} STRATEGY

{strategy_info['description']}

🤖 How It Works:
{strategy_info.get('how_it_works', 'Advanced algorithmic trading with real-time market analysis.')}

💰 Investment Range: 
• Minimum: ${strategy_info['min_amount']:,}
• Maximum: ${'Unlimited' if strategy_info['max_amount'] == float('inf') else f"{strategy_info['max_amount']:,}"}

📈 Expected Returns:
• Daily: {daily_return * 100:.2f}%
• Monthly: ~{monthly_return:.1f}%
• Annual: ~{annual_return:.1f}%

⚡ Key Features:
• Automated trading 24/7
• Real-time market monitoring
• Risk management protocols
• Compound interest applied daily

💡 Best For: {strategy_info.get('best_for', 'All investor types')}

Ready to start with {strategy_info['name']}?
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def handle_strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle strategy selection - ask for amount first"""
    strategy_type = data.split("_")[2]
    
    strategy_map = {
        "trendfollowing": TradingStrategy.TREND_FOLLOWING.value,
        "momentumtrading": TradingStrategy.MOMENTUM_TRADING.value,
        "meanreversion": TradingStrategy.MEAN_REVERSION.value,
        "scalping": TradingStrategy.SCALPING.value,
        "arbitrage": TradingStrategy.ARBITRAGE.value
    }
    
    strategy_info = strategy_map.get(strategy_type)
    if not strategy_info:
        await update.callback_query.message.edit_text("❌ Invalid strategy selected.")
        return
    
    # Store strategy info
    context.user_data['selected_strategy'] = {
        'type': strategy_type,
        'info': strategy_info
    }
    context.user_data['awaiting_investment_amount'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Strategies", callback_data="crypto_strategies")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    max_amount_display = 'unlimited' if strategy_info['max_amount'] == float('inf') else f"{strategy_info['max_amount']:,}"
    
    text = f"""
🎯 {strategy_info['name'].upper()} SELECTED

💰 Investment Range: ${strategy_info['min_amount']:,} - ${max_amount_display}
📈 Daily Return: {strategy_info['expected_daily_return'] * 100:.2f}%

💵 Please enter your investment amount in USD:

Examples:
• 1000
• 5500.50  
• 25000

⚠️ Requirements:
• Minimum: ${strategy_info['min_amount']:,}
• Maximum: ${max_amount_display}

Enter amount below:
    """
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="invest_menu")]]
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def handle_crypto_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle cryptocurrency selection with QR code and converted amount"""
    parts = data.split("_")
    crypto = parts[1]
    amount = float(parts[2])  # Get amount from callback data
    
    strategy_data = context.user_data.get('selected_strategy')
    if not strategy_data:
        await update.callback_query.message.edit_text("❌ Strategy session expired. Please start over.")
        return
    
    strategy_info = strategy_data['info']
    
    # Get current crypto price
    crypto_amount, usd_rate = await get_crypto_conversion(crypto, amount)
    if not crypto_amount:
        await update.callback_query.message.edit_text("❌ Error fetching current prices. Please try again.")
        return
    
    wallet_address = get_random_wallet(crypto)
    if not wallet_address:
        await update.callback_query.message.edit_text("❌ Invalid cryptocurrency selected.")
        return
    
    # Generate QR code
    qr_code_url = await generate_qr_code(wallet_address, crypto, crypto_amount)
    
    # Store investment details
    context.user_data['awaiting_tx_details'] = {
        'strategy_type': strategy_data['type'],
        'strategy_info': strategy_info,
        'crypto': crypto,
        'wallet_address': wallet_address,
        'user_id': update.callback_query.from_user.id,
        'amount': amount,
        'crypto_amount': crypto_amount
    }
    
    keyboard = [
        [InlineKeyboardButton("✅ I've Sent Payment", callback_data="confirm_payment")],
        [InlineKeyboardButton("❌ Cancel", callback_data="invest_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🧾 𝗜𝗡𝗩𝗘𝗦𝗧𝗠𝗘𝗡𝗧 𝗜𝗡𝗩𝗢𝗜𝗖𝗘

🎯 Strategy: {strategy_info['name']}
💰 Amount: ${amount:,.2f} USD
💎 Payment: {crypto.upper()}
💵 Crypto Amount: {crypto_amount:.8f} {crypto.upper()}

📊 Rate: 1 {crypto.upper()} = ${usd_rate:,.2f} USD

🔐 PAYMENT DETAILS:

📱 Scan QR Code or Send To:

Wallet Address:
`{wallet_address}`

⚠️ IMPORTANT:
• Send EXACTLY {crypto_amount:.8f} {crypto.upper()}
• Network: {get_network_name(crypto)}
• Include sufficient network fees
• Payment will be verified & confirmed

⚡ Your investment activates once payment is confirmed!
    """
    
    # Send QR code image with invoice
    await update.callback_query.message.reply_photo(
        photo=qr_code_url,
        caption=text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def get_crypto_conversion(crypto: str, usd_amount: float) -> tuple:
    """Get current crypto price and convert USD amount to crypto"""
    try:
        # Map crypto symbols to API symbols
        symbol_map = {
            'btc': 'bitcoin',
            'eth': 'ethereum', 
            'usdt': 'tether',
            'sol': 'solana',
            'ton': 'toncoin'
        }
        
        api_symbol = symbol_map.get(crypto)
        if not api_symbol:
            return None, None
            
        # Use CoinGecko API for prices
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={api_symbol}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if api_symbol in data and 'usd' in data[api_symbol]:
            usd_rate = data[api_symbol]['usd']
            crypto_amount = usd_amount / usd_rate
            return crypto_amount, usd_rate
            
    except Exception as e:
        logging.error(f"Error fetching crypto price: {e}")
    
    return None, None

async def generate_qr_code(address: str, crypto: str, amount: float) -> str:
    """Generate QR code for crypto payment"""
    try:
        # Create payment URI based on cryptocurrency
        if crypto == 'btc':
            payment_uri = f"bitcoin:{address}?amount={amount}"
        elif crypto == 'eth':
            payment_uri = f"ethereum:{address}?value={amount}"
        elif crypto == 'usdt':
            payment_uri = f"tether:{address}?amount={amount}"
        elif crypto == 'sol':
            payment_uri = f"solana:{address}?amount={amount}"
        elif crypto == 'ton':
            payment_uri = f"ton:{address}?amount={amount}"
        else:
            payment_uri = address
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        return bio
        
    except Exception as e:
        logging.error(f"Error generating QR code: {e}")
        return None

def get_network_name(crypto: str) -> str:
    """Get network name for cryptocurrency"""
    networks = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum (ERC20)',
        'usdt': 'TRON (TRC20)',
        'sol': 'Solana',
        'ton': 'TON'
    }
    return networks.get(crypto, crypto.upper())

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment confirmation button"""

    if update.callback_query.data == "invest_menu":  # CANCEL CLICKED
        await show_invest_menu(update, context)
        return

    investment_data = context.user_data.get('awaiting_tx_details')

    if not investment_data:
        await update.callback_query.answer("Session expired. Please start over.", show_alert=True)
        await update.callback_query.message.reply_text(
            "❌ Investment session expired. Please start a new investment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]])
        )
        return
    
    # Store the investment data
    context.user_data['awaiting_payment_details'] = True
    context.user_data['investment_data'] = investment_data
    context.user_data.pop('awaiting_tx_details', None)
    
    strategy_info = investment_data['strategy_info']
    amount = investment_data['amount']
    crypto = investment_data['crypto']
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Invoice", callback_data=f"crypto_{crypto}_{amount}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
💸 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗔𝗧𝗜𝗢𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧

Please reply with your transaction details:

Format:
```
Amount: $X,XXX
Transaction ID: [your_tx_hash]
Network: [network_name]
```

Example:
```
Amount: $5,000
Transaction ID: 0x1234...abcd
Network: Bitcoin
```

⚠️ Important:
• Include the exact transaction hash/ID
• Use the correct network name
• Double-check all information

This helps us verify your payment quickly and activate your investment!
    """
    
    await update.callback_query.message.reply_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    await update.callback_query.answer()

       
async def show_withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show withdrawal options with stored wallet address"""
    user = update.callback_query.from_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.callback_query.message.edit_text("❌ You're not registered yet. Use /start first!")
        return
    
    current_balance = user_data[8] if len(user_data) > 8 else 0
    
    # Get user's stored wallet address
    from handlers.settings_handlers import get_user_wallet_address
    wallet_address = get_user_wallet_address(user.id)
    
    # Store withdrawal options
    context.user_data['withdraw_options'] = {
        '25%': current_balance * 0.25,
        '50%': current_balance * 0.50,
        '100%': current_balance
    }
    
    wallet_info = ""
    if wallet_address:
        wallet_info = f"\n💳 Your Wallet: `{wallet_address[:10]}...{wallet_address[-10:]}`"
    else:
        wallet_info = "\n⚠️ No wallet saved! Please add one in Settings first."
    
    keyboard = [
        [InlineKeyboardButton("💸 Withdraw 25%", callback_data="withdraw_25"),
         InlineKeyboardButton("💸 Withdraw 50%", callback_data="withdraw_50")],
        [InlineKeyboardButton("💸 Withdraw 100%", callback_data="withdraw_100"),
         InlineKeyboardButton("💰 Custom Amount", callback_data="withdraw_custom")],
        [InlineKeyboardButton("⚙️ Update Wallet", callback_data="settings_edit_wallet")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
💸 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗖𝗘𝗡𝗧𝗘𝗥

💰 Available Cash Balance: ${current_balance:,.2f}
{wallet_info}

Quick Cash Withdrawals:
- 25%: ${context.user_data['withdraw_options']['25%']:,.2f}
- 50%: ${context.user_data['withdraw_options']['50%']:,.2f}
- 100%: ${context.user_data['withdraw_options']['100%']:,.2f}

⚡ Process:
1. Select amount below
2. Confirm withdrawal (uses your saved wallet)
3. Admin processes within 24 hours

🔒 Security:
- All withdrawals verified
- Minimum: $10 USDT
- Network: TRC20 only

Select option below: 👇
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)


async def handle_withdrawal_options(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle withdrawal option selection with automatic wallet usage"""
    withdrawal_type = data.replace("withdraw_", "")
    user = update.callback_query.from_user
    
    # Get user's stored wallet address
    from handlers.settings_handlers import get_user_wallet_address
    wallet_address = get_user_wallet_address(user.id)
    
    # Check if wallet is set
    if not wallet_address:
        keyboard = [
            [InlineKeyboardButton("⚙️ Add Wallet in Settings", callback_data="settings_edit_wallet")],
            [InlineKeyboardButton("🔙 Back", callback_data="withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            "⚠️ NO WALLET ADDRESS SAVED\n\n"
            "Please add your USDT wallet address in Settings before withdrawing.\n\n"
            "This makes withdrawals faster and more secure!",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    if withdrawal_type == "custom":
        context.user_data['awaiting_withdraw_amount'] = True
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="withdraw")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(
            "💸 𝗖𝗨𝗦𝗧𝗢𝗠 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗔𝗠𝗢𝗨𝗡𝗧\n\n"
            "Please reply with the amount you want to withdraw:\n\n"
            "Examples:\n"
            "• 100\n"
            "• 500.50\n"
            "• 1000\n\n"
            "Note: Minimum $10, maximum is your available balance.\n"
            "Enter amount below:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Handle percentage withdrawals (25%, 50%, 100%)
    user_data = db.get_user(user.id)
    if not user_data:
        await update.callback_query.message.edit_text("❌ User data not found.")
        return
    
    current_balance = user_data[8] if len(user_data) > 8 else 0
    
    # Calculate withdrawal amounts
    withdrawal_amounts = {
        '25': current_balance * 0.25,
        '50': current_balance * 0.50,
        '100': current_balance
    }
    
    if withdrawal_type in withdrawal_amounts:
        amount = withdrawal_amounts[withdrawal_type]
        
        if amount < 10:
            await update.callback_query.message.edit_text(
                f"❌ Withdrawal amount ${amount:.2f} is below minimum $10.\n\n"
                f"Your current balance: ${current_balance:.2f}\n"
                f"Try a custom amount or invest more first.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="withdraw")]])
            )
            return
        
        # Confirm withdrawal with stored wallet
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Withdrawal", callback_data=f"confirm_withdraw_{withdrawal_type}")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.user_data['pending_withdrawal'] = {
            'amount': amount,
            'user_id': user.id,
            'wallet_address': wallet_address
        }
        
        await update.callback_query.message.edit_text(
            f"💸 𝗖𝗢𝗡𝗙𝗜𝗥𝗠 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟\n\n"
            f"Amount: ${amount:,.2f} ({withdrawal_type}% of balance)\n"
            f"To Wallet: `{wallet_address}`\n\n"
            f"⚡ Your request will be processed.\n\n"
            f"⚠️ Please verify your wallet address is correct!\n\n"
            f"Confirm withdrawal?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Unknown withdrawal type
    await update.callback_query.message.edit_text(
        "❌ Unknown withdrawal option selected.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Withdraw Menu", callback_data="withdraw")]])
    )

async def process_withdrawal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Process confirmed withdrawal with stored wallet"""
    withdrawal_data = context.user_data.get('pending_withdrawal')
    
    if not withdrawal_data:
        await update.callback_query.message.edit_text("❌ Withdrawal session expired. Please start again.")
        return
    
    amount = withdrawal_data['amount']
    user_id = withdrawal_data['user_id']
    wallet_address = withdrawal_data['wallet_address']
    
    # Save withdrawal request
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO withdrawals (user_id, amount, wallet_address)
                VALUES (?, ?, ?)
            ''', (user_id, amount, wallet_address))
            conn.commit()
            withdrawal_id = cursor.lastrowid  # ✅ CAPTURE THE ID!
        
        await update.callback_query.message.edit_text(
            "✅  𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗!\n\n"
            f"💰 Amount: ${amount:,.2f}\n"
            f"💳 To: `{wallet_address}`\n\n"
            "⏰ Your request is being processed .\n"
            "You'll receive a confirmation once the funds are sent!\n\n"
            "Thank you for using 𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 𝗔𝗶! 🚀",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]),
            parse_mode='HTML'
        )
        
        # Notify admins - ✅ NOW WE HAVE THE ID!
        await notify_admins_new_withdrawal(context, user_id, amount, wallet_address, withdrawal_id)
        
    except Exception as e:
        logging.error(f"Error saving withdrawal: {e}")
        await update.callback_query.message.edit_text(
            "❌ Failed to save withdrawal request. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Withdraw", callback_data="withdraw")]])
        )
    
    # Clean up
    context.user_data.pop('pending_withdrawal', None)

async def show_live_prices_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live prices menu"""
    keyboard = [
        [InlineKeyboardButton("💎 Crypto Prices", callback_data="live_crypto")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
📈 𝗟𝗜𝗩𝗘 𝗠𝗔𝗥𝗞𝗘𝗧 𝗣𝗥𝗜𝗖𝗘𝗦

Choose the market you want to view:

📊 Crypto Prices - Top 20+ cryptocurrencies by market cap

All prices are updated in real-time.

Select an option below: 👇
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)

async def show_live_crypto_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live crypto prices with pagination (10 per page, up to 50 total)"""
    data = update.callback_query.data
    
    # Extract page number from callback data
    if data == "live_crypto":
        page = 0
    else:
        try:
            # Extract page number from patterns like "live_crypto_1", "live_crypto_2", etc.
            page = int(data.split("_")[-1])
        except (ValueError, IndexError):
            page = 0
    
    try:
        crypto_data = market.get_top_crypto_prices(limit=50)  # Get 50 cryptos
        if not crypto_data:
            raise ValueError("No data received")
        
        crypto_list = sorted(crypto_data.items(), key=lambda x: x[1]['rank'])
        
        cryptos_per_page = 10  # 10 per page
        total_pages = (len(crypto_list) + cryptos_per_page - 1) // cryptos_per_page
        
        # Ensure page is within valid range
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * cryptos_per_page
        end_idx = start_idx + cryptos_per_page
        page_cryptos = crypto_list[start_idx:end_idx]
        
        text = f"📈 𝗟𝗜𝗩𝗘 𝗠𝗔𝗥𝗞𝗘𝗧 𝗣𝗥𝗜𝗖𝗘𝗦 (Page {page+1}/{total_pages}) 🚀\n\n"
        text += "<pre>Symbol    Price (USD)    1h%     24h%    7d%\n"
        text += "-" * 50 + "\n"
        
        for crypto_id, info in page_cryptos:
            change_1h = f"{info['change_1h']:+.2f}%" if info['change_1h'] else "N/A"
            change_24h = f"{info['change_24h']:+.2f}%" if info['change_24h'] else "N/A"
            change_7d = f"{info['change_7d']:+.2f}%" if info['change_7d'] else "N/A"
            text += f"{info['symbol']:<8}  ${info['price']:>10,.2f}  {change_1h:>6}  {change_24h:>6}  {change_7d:>6}\n"
        
        text += "</pre>\n\n💡 Prices from CoinGecko | Updated in real-time 📊"
        
        keyboard = []
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"live_crypto_{page-1}"))
        if end_idx < len(crypto_list):
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"live_crypto_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)

        # Utility buttons
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh 📈", callback_data=f"live_crypto"),
            InlineKeyboardButton("💰 Invest Now 🚀", callback_data="crypto_strategy")
        ])
        keyboard.append([InlineKeyboardButton("🔙 Live Prices Menu 📊", callback_data="live_prices")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.edit_text(
            text.strip(),
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    except Exception as e:
        logging.exception(f"Error showing crypto prices: {e}")
        await update.callback_query.message.edit_text(
            "❌ Error loading crypto prices. Please try again.\n\n"
            "This might be due to:\n"
            "• API rate limits\n"
            "• Network issues\n"
            "• Maintenance\n\nUsing fallback data...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again 📈", callback_data="live_crypto")],
                [InlineKeyboardButton("🔙 Live Prices 📊", callback_data="live_prices")]
            ])
        )

async def show_user_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show user's transaction history with pagination"""
    user = update.callback_query.from_user
    transactions_per_page = 10  # 10 per page
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT 'investment' as type, amount, investment_date as date, status, crypto_type as details FROM investments 
                WHERE user_id = ?
                UNION ALL
                SELECT 'withdrawal' as type, amount, withdrawal_date as date, status, wallet_address as details FROM withdrawals 
                WHERE user_id = ?
            )
        ''', (user.id, user.id))
        total_transactions = cursor.fetchone()[0]
        
        # Get paginated transactions
        cursor.execute('''
            SELECT type, amount, date, status, details FROM (
                SELECT 'investment' as type, amount, investment_date as date, status, crypto_type as details FROM investments 
                WHERE user_id = ?
                UNION ALL
                SELECT 'withdrawal' as type, amount, withdrawal_date as date, status, wallet_address as details FROM withdrawals 
                WHERE user_id = ?
            ) ORDER BY date DESC
            LIMIT ? OFFSET ?
        ''', (user.id, user.id, transactions_per_page, page * transactions_per_page))
        transactions = cursor.fetchall()
    
    total_pages = (total_transactions + transactions_per_page - 1) // transactions_per_page
    
    if not transactions:
        text = "📜 𝗧𝗥𝗔𝗡𝗦𝗔𝗖𝗧𝗜𝗢𝗡 𝗛𝗜𝗦𝗧𝗢𝗥𝗬 \n\nNo transactions yet. Start investing to see history! 📈"
    else:
        text = f"📜 𝗧𝗥𝗔𝗡𝗦𝗔𝗖𝗧𝗜𝗢𝗡 𝗛𝗜𝗦𝗧𝗢𝗥𝗬  (Page {page+1}/{total_pages}) 🚀\n\n"
        text += "<pre>Type         Amount     Status    Date         Details\n"
        text += "-" * 60 + "\n"
        
        for tx in transactions:
            tx_type, amount, date, status, details = tx
            display_type = tx_type.capitalize()[:10]
            display_amount = f"${amount:,.2f}"[:10]
            display_status = status.upper()[:8]
            display_date = (date[:10] if date else "N/A")[:10]
            display_details = (details or "N/A")[:15]
            text += f"{display_type:<12} {display_amount:<10} {display_status:<9} {display_date:<12} {display_details:<15}\n"
        
        text += "</pre>\n\n💡 Recent 20 transactions | Full history in portfolio 📊"
    
    keyboard = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"user_history_page_{page-1}"))
    if (page + 1) * transactions_per_page < total_transactions:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"user_history_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Utility buttons
    keyboard.append([
        InlineKeyboardButton("🔄 Refresh 📋", callback_data=f"user_history_page_{page}"),
        InlineKeyboardButton("📊 Portfolio 💼", callback_data="portfolio")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Profile 🏠", callback_data="profile")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's referrals with complete information"""
    user = update.callback_query.from_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.callback_query.message.edit_text("❌ User data not found.")
        return
    
    # Get referral code (handle 14 fields)
    referral_code = user_data[11] if len(user_data) > 11 else 'N/A'
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get referral count
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user.id,))
        referral_count = cursor.fetchone()[0]
        
        # Get total bonus earned
        cursor.execute('SELECT COALESCE(SUM(bonus_amount), 0) FROM referrals WHERE referrer_id = ?', (user.id,))
        total_bonus = cursor.fetchone()[0]
        
        # Get referred users with details
        cursor.execute('''
            SELECT u.user_id, u.username, u.full_name, u.total_invested, r.referral_date
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.referral_date DESC
        ''', (user.id,))
        referred_users = cursor.fetchall()
    
    # Build referral link
    bot_username = context.bot.username if hasattr(context.bot, 'username') else "your_bot"
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    text = f"""👥 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗣𝗥𝗢𝗚𝗥𝗔𝗠

🎁 Your Referral Code: `{referral_code}`

📊 Statistics:
• Total Referrals: {referral_count}
• Commission Earned: ${total_bonus:.2f}
• Conversion Rate: {(referral_count / max(referral_count, 1)) * 100:.1f}%

💰 Commission Structure:
• 5% of referred user's first investment
• Lifetime earnings from referrals
• Instant credit to your balance

🔗 Share Your Link:
{referral_link}

"""
    
    if referred_users:
        text += "📋 Your Referrals:\n"
        for ref_id, username, full_name, invested, ref_date in referred_users[:10]:
            date_str = ref_date[:10] if ref_date else "N/A"
            name_display = full_name or username or str(ref_id)
            invested_display = f"${invested:,.2f}" if invested > 0 else "Not invested yet"
            text += f"• @{username or ref_id} - {invested_display} (Joined: {date_str})\n"
        
        if len(referred_users) > 10:
            text += f"\n... and {len(referred_users) - 10} more\n"
    else:
        text += "📋 No referrals yet. Start sharing your code!\n"
    
    text += "\n💡 How to earn:\n"
    text += "1. Share your referral link\n"
    text += "2. Friends register using your link\n"
    text += "3. You earn 5% when they invest\n"
    text += "4. Commission added to your balance instantly"
    
    keyboard = [
        [InlineKeyboardButton("📊 View All Referrals", callback_data="referrals_full")],
        [InlineKeyboardButton("🔙 Profile 👤", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
    text.strip(), 
    reply_markup=reply_markup, 
    parse_mode='HTML'
)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show real leaderboard with top 5 users"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, profit_earned, strategy 
            FROM users 
            WHERE profit_earned > 0
            ORDER BY profit_earned DESC 
            LIMIT 5
        ''')
        leaderboard_data = cursor.fetchall()
    
    if not leaderboard_data:
        text = "🏆 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗\n\nNo active investors yet.\nStart investing to climb the ranks! 🚀"
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        return
    
    text = "🏆 𝗧𝗢𝗣 𝟱 𝗜𝗡𝗩𝗘𝗦𝗧𝗢𝗥𝗦\n\n🚀 Real earnings from active strategies:\n\n"
    
    rank_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, (username, profit_earned, strategy) in enumerate(leaderboard_data):
        display_name = username.replace('_', ' ')[:18] if username else 'Anonymous'
        emoji = rank_emojis[i]
        strategy_display = strategy.replace('_', ' ') if strategy else 'No Strategy'
        
        text += f"{emoji} {display_name}\n"
        text += f"   💰 Earnings: ${profit_earned:,.2f}\n"
        text += f"   🤖 Strategy: {strategy_display}\n\n"
    
    text += "💡 Invest now to join the top ranks!\n"
    text += "Your strategy could get you here! 🚀"
    
    keyboard = [
        [InlineKeyboardButton("💰 Start Investing", callback_data="invest_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile (Upgraded to display strategy)"""
    user = update.callback_query.from_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.callback_query.message.edit_text("❌ You're not registered yet. Use /start first!")
        return
    
    # Unpack user data (Upgraded: 'plan' -> 'strategy')
    user_id, username, first_name, full_name, email, reg_date, strategy, total_invested, current_balance, profit_earned, last_update, referral_code, referred_by, wallet_address = user_data
    
    # Get additional stats
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user.id,))
        referral_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM investments WHERE user_id = ? AND status = "confirmed"', (user.id,))
        investment_count = cursor.fetchone()[0]
        text = f"""
👤 𝗬𝗢𝗨𝗥 𝗣𝗥𝗢𝗙𝗜𝗟𝗘

📋 Personal Information:
• Full Name: {full_name or 'Not provided'}
• Email: {email or 'Not provided'}
• Telegram: @{username}
• Member Since: {reg_date[:10] if reg_date else 'Unknown'}

💼 Account Summary:
• Trading Strategy: {strategy if strategy else 'No active strategy'}
"""

    if strategy:
        strategy_map = {
            'TREND_FOLLOWING': TradingStrategy.TREND_FOLLOWING.value,
            'MOMENTUM_TRADING': TradingStrategy.MOMENTUM_TRADING.value,
            'MEAN_REVERSION': TradingStrategy.MEAN_REVERSION.value,
            'SCALPING': TradingStrategy.SCALPING.value,
            'ARBITRAGE': TradingStrategy.ARBITRAGE.value
        }
        strategy_info = strategy_map.get(strategy.upper())
        if strategy_info:
            text += f"  - {strategy_info['description']}\n"

    text += f"""• Total Invested: ${total_invested:,.2f}
    • Current Balance: ${current_balance:,.2f}
    • Total Profit: ${profit_earned:,.2f}

    📊 Activity Stats:
    • Investments Made: {investment_count}
    • Referrals Made: {referral_count}

    🎯 Referral Code: `{referral_code}`
    """    
    keyboard = [
        [InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")],
        [InlineKeyboardButton("📜 Transaction History", callback_data="user_history")],
        [InlineKeyboardButton("👥 Referrals", callback_data="referrals")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(), 
        reply_markup=reply_markup, 
        parse_mode='HTML'
    )
    clear_awaiting_states(context)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show concise help information"""
    text = """
📖 𝗤𝘂𝗶𝗰𝗸 𝗛𝗲𝗹𝗽 𝗚𝘂𝗶𝗱𝗲

🚀 𝗤𝘂𝗶𝗰𝗸 𝗦𝘁𝗮𝗿𝘁:
1. /start → Register
2. Complete profile  
3. Choose strategy
4. Send payment
5. Start earning!

💡 𝗞𝗲𝘆 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:
• AI Trading Bot
• Daily Returns
• Anytime Withdrawals
• 5% Referral Bonus

🔧 𝗕𝗮𝘀𝗶𝗰 𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻𝘀:
• Investing: Choose strategy → Send crypto
• Withdrawing: Set wallet → Confirm amount
• Tracking: Portfolio & Live Prices
• Referrals: Share code → Earn 5%

⚙️ 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:
• Update personal info
• Manage wallet addresses
• Account management

For detailed FAQs, check the ❓ FAQ section!
    """
    
    keyboard = [
        [InlineKeyboardButton("🆘 Support", url="https://t.me/Quanttradesupportbot")],
        [InlineKeyboardButton("❓ Read FAQ", callback_data="faq")],
        [InlineKeyboardButton("💰 Invest Now", callback_data="invest_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show concise FAQ"""
    text = """
❓ 𝗙𝗔𝗤 - 𝗙𝗿𝗲𝗾𝘂𝗲𝗻𝘁𝗹𝘆 𝗔𝘀𝗸𝗲𝗱 𝗤𝘂𝗲𝘀𝘁𝗶𝗼𝗻𝘀

🤖 𝗛𝗼𝘄 𝗜𝘁 𝗪𝗼𝗿𝗸𝘀:
All investors are connected to one centralized exchange where our AI trading bot strategically executes trades 24/7. 
The bot operates tirelessly using advanced algorithms to maximize profits for all users.

💰 𝗜𝗻𝘃𝗲𝘀𝘁𝗺𝗲𝗻𝘁:
• Start earning after admin confirmation
• Minimum: $500 (strategy-dependent)
• Withdraw anytime from available balance

💸 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹𝘀:
• Processed within 24 hours
• Minimum: $10 USDT (TRC20)
• No withdrawal fees

🔒 𝗦𝗲𝗰𝘂𝗿𝗶𝘁𝘆:
• Enterprise-grade protection
• Profit in all market conditions
• Upgrade strategies anytime

💡 𝗧𝗶𝗽𝘀:
• Start with Trend Following
• Reinvest for compound growth
• Use referrals to boost earnings

For detailed help, check the Help section!
    """
    
    keyboard = [
        [InlineKeyboardButton("🆘 Support", url="https://t.me/Quanttradesupportbot")],
        [InlineKeyboardButton("📖 Detailed Help", callback_data="help")],
        [InlineKeyboardButton("💰 Invest Now", callback_data="invest_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')


