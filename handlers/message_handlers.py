"""
Text message handlers
"""
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import yfinance as yf 
from .utils import log_admin_action
from config import ADMIN_USER_IDS
from database import db
from handlers.user_handlers import show_main_menu
import asyncio

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
    

# Add these functions to your handlers/message_handlers.py

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced text message handler with complete admin support"""
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # Check if settings system should handle this message FIRST (for all users)
    if context.user_data.get('awaiting_settings_edit'):
        from handlers.settings_handlers import handle_settings_text_input
        handled = await handle_settings_text_input(update, context, message_text)
        if handled:
            return
    
    if context.user_data.get('awaiting_investment_amount'):
        await handle_investment_amount(update, context, message_text)
        return
    
    if message_text.lower() in ['/cancel', 'cancel', '❌ cancel']:
        # Clear ALL awaiting states
        for key in ['awaiting_settings_edit', 'awaiting_investment_amount', 
                   'awaiting_payment_details', 'awaiting_withdraw_amount']:
            context.user_data.pop(key, None)
        
        await update.message.reply_text("✅ Action cancelled.")
        await show_main_menu(update, context, user)
        return

    # Check if admin system should handle this message
    if user.id in ADMIN_USER_IDS:
        # Handle admin balance editing
        if context.user_data.get('awaiting_balance_user_id'):
            await handle_balance_user_id_input(update, context, message_text)
            return
        elif context.user_data.get('awaiting_balance_amount'):
            await handle_balance_amount_input(update, context, message_text)
            return
        
        # Handle admin user editing
        elif context.user_data.get('awaiting_user_edit'):
            await handle_user_edit_input(update, context, message_text)
            return
        elif context.user_data.get('awaiting_investment_edit'):
            await handle_investment_edit_input(update, context, message_text)
            return
        
        # Handle admin search and broadcast
        elif context.user_data.get('awaiting_user_search'):
            await handle_user_search_input(update, context, message_text)
            return
        elif context.user_data.get('awaiting_broadcast_message'):
            await handle_broadcast_message_admin(update, context, message_text)
            return
    
    # Continue with regular user message handling...
    
    # Registration flow
    if context.user_data.get('registration_step') == 'name':
        await handle_registration_name(update, context, message_text)
        return
    
    elif context.user_data.get('registration_step') == 'email':
        await handle_registration_email(update, context, message_text)
        return
    
    # Investment payment details
    elif context.user_data.get('awaiting_payment_details'):
        await handle_payment_details(update, context, message_text)
        return
    
    # Withdrawal amount
    elif context.user_data.get('awaiting_withdraw_amount'):
        await handle_withdrawal_amount(update, context, message_text)
        return
    
    # Withdrawal address (legacy - now uses stored wallet)
    elif context.user_data.get('pending_withdrawal') and not context.user_data['pending_withdrawal'].get('wallet_address'):
        await handle_withdrawal_address(update, context, message_text)
        return
    
    # Default response for unhandled messages
    await update.message.reply_text(
        "❌ I didn't understand that. Use /start for the main menu or click a button from the keyboard."
    )


async def handle_investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_text: str):
    """Handle investment amount input and show crypto options"""
    try:
        amount = float(amount_text.replace('$', '').replace(',', '').strip())
        
        strategy_data = context.user_data.get('selected_strategy')
        if not strategy_data:
            await update.message.reply_text("❌ Please select a strategy first.")
            return
            
        strategy_info = strategy_data['info']
        min_amount = strategy_info['min_amount']
        max_amount = strategy_info['max_amount']
        
        # Validate amount range
        if amount < min_amount:
            await update.message.reply_text(
                f"❌ Amount too low. Minimum for {strategy_info['name']} is ${min_amount:,}.\n\nPlease enter a valid amount:"
            )
            return
            
        if max_amount != float('inf') and amount > max_amount:
            await update.message.reply_text(
                f"❌ Amount too high. Maximum for {strategy_info['name']} is ${max_amount:,}.\n\nPlease enter a valid amount:"
            )
            return
        
        # Store validated amount
        context.user_data['investment_amount'] = amount
        context.user_data.pop('awaiting_investment_amount', None)
        
        # Show only USDT option
        keyboard = [
            [InlineKeyboardButton("💵 USDT (TRC20)", callback_data=f"crypto_usdt_{amount}")],
            [InlineKeyboardButton("🔙 Change Amount", callback_data=f"strategy_select_{strategy_data['type']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
💰 𝗜𝗡𝗩𝗘𝗦𝗧𝗠𝗘𝗡𝗧 𝗔𝗠𝗢𝗨𝗡𝗧 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗

🎯 Strategy: {strategy_info['name']}
💵 Amount: ${amount:,.2f} USD
📈 Daily Return: {strategy_info['expected_daily_return'] * 100:.2f}%

💎 Payment Method: USDT (TRC20)

• Exact amount in USDT
• QR code for easy payment
• Wallet address for manual transfer

Click below to get payment details: 👇
        """
        
        await update.message.reply_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
        
    except ValueError:
        await update.message.reply_text("❌ Invalid amount format. Please enter a valid number (e.g., 1000 or 500.50):")


async def handle_user_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, input_text: str):
    """Handle user profile edit input from admin"""
    edit_field = context.user_data.get('edit_field')
    user_id = context.user_data.get('edit_user_id')
    
    if not edit_field or not user_id:
        await update.message.reply_text("❌ Edit session expired. Please start over.")
        context.user_data.pop('awaiting_user_edit', None)
        return
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if edit_field == 'name':
                if len(input_text) < 2:
                    await update.message.reply_text("❌ Name must be at least 2 characters long.")
                    return
                
                cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (input_text, user_id))
                conn.commit()
                
                success_msg = f"✅ NAME UPDATED\n\nUser's full name changed to: {input_text}"
                
            elif edit_field == 'email':
                if '@' not in input_text or '.' not in input_text:
                    await update.message.reply_text("❌ Please enter a valid email address.")
                    return
                
                cursor.execute('UPDATE users SET email = ? WHERE user_id = ?', (input_text, user_id))
                conn.commit()
                
                success_msg = f"✅ EMAIL UPDATED\n\nUser's email changed to: {input_text}"
                
            elif edit_field == 'regdate':
                # Validate date format
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(input_text, '%Y-%m-%d')
                    formatted_date = parsed_date.isoformat()
                except ValueError:
                    await update.message.reply_text(
                        "❌ Invalid date format. Please use YYYY-MM-DD format.\n\n"
                        "Example: 2024-01-15"
                    )
                    return
                
                cursor.execute('UPDATE users SET registration_date = ? WHERE user_id = ?', (formatted_date, user_id))
                conn.commit()
                
                success_msg = f"✅ REGISTRATION DATE UPDATED\n\nUser's registration date changed to: {input_text}"
        
        # Log the action
        log_admin_action(
            admin_id=update.effective_user.id,
            action_type=f"profile_edit_{edit_field}",
            target_user_id=user_id,
            notes=f"Changed {edit_field} to: {input_text}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit More", callback_data=f"admin_edit_profile_{user_id}")],
            [InlineKeyboardButton("👤 View Profile", callback_data=f"admin_user_profile_{user_id}")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_msg, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Error updating user {edit_field}: {e}")
        await update.message.reply_text(f"❌ Error updating {edit_field}: {str(e)}")
    
    # Clean up
    context.user_data.pop('awaiting_user_edit', None)
    context.user_data.pop('edit_field', None)
    context.user_data.pop('edit_user_id', None)

async def handle_investment_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, input_text: str):
    """Handle investment editing input (Upgraded: 'plan' -> 'strategy')"""
    edit_data = context.user_data.get('investment_edit_data')
    if not edit_data:
        await update.message.reply_text("❌ Edit session expired.")
        return
    field = edit_data.get('field')
    investment_id = edit_data.get('investment_id')

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if field == 'amount':
                amount = float(input_text.replace(',', ''))
                cursor.execute('UPDATE investments SET amount = ? WHERE id = ?', (amount, investment_id))
                success_msg = f"✅ Investment amount updated to ${amount:,.2f}"
            elif field == 'status':
                if input_text.lower() not in ['confirmed', 'pending', 'rejected']:
                    await update.message.reply_text("❌ Status must be: confirmed, pending, or rejected")
                    return
                cursor.execute('UPDATE investments SET status = ? WHERE id = ?', (input_text.lower(), investment_id))
                success_msg = f"✅ Investment status updated to {input_text.title()}"
            elif field == 'strategy':  # Updated from 'plan'
                if input_text.upper() not in ['TREND_FOLLOWING', 'MOMENTUM_TRADING', 'MEAN_REVERSION', 'SCALPING', 'ARBITRAGE']:
                    await update.message.reply_text("❌ Strategy must be: TREND_FOLLOWING, MOMENTUM_TRADING, MEAN_REVERSION, SCALPING, or ARBITRAGE")
                    return
                cursor.execute('UPDATE investments SET strategy = ? WHERE id = ?', (input_text.upper(), investment_id))
                success_msg = f"✅ Investment strategy updated to {input_text.upper()}"
            conn.commit()
        
        # Log the action (Upgraded: 'investment_edit_{field}')
        log_admin_action(
            admin_id=update.effective_user.id,
            action_type=f"investment_edit_{field}",
            target_user_id=edit_data.get('user_id'),
            notes=f"Investment {investment_id} {field} changed to: {input_text}"
        )
        
        user_id = edit_data.get('user_id')
        keyboard = [
            [InlineKeyboardButton("💰 Edit More Investments", callback_data=f"admin_edit_investments_{user_id}")],
            [InlineKeyboardButton("👤 Back to Profile", callback_data=f"admin_user_profile_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(success_msg, reply_markup=reply_markup)
    
    except ValueError:
        await update.message.reply_text("❌ Invalid input format. Please try again.")
    except Exception as e:
        logging.error(f"Error updating investment: {e}")
        await update.message.reply_text(f"❌ Error updating investment: {str(e)}")

    # Clean up
    context.user_data.pop('awaiting_investment_edit', None)
    context.user_data.pop('investment_edit_data', None)    

async def handle_registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE, full_name: str):
    """Handle full name input during registration"""
    if len(full_name) < 2:
        await update.message.reply_text("Please provide a valid full name (at least 2 characters):")
        return
    
    context.user_data['full_name'] = full_name
    context.user_data['registration_step'] = 'email'
    await update.message.reply_text("Great! Now please provide a valid email address (e.g., user@example.com):")

async def handle_registration_email(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str):
    """Handle email input during registration"""
    email = email.strip()
    
    # Validate email: Must contain '@' and at least one '.' after '@'
    if '@' not in email or '.' not in email.split('@')[-1]:
        await update.message.reply_text("❌ Invalid email format. Please provide a valid email address (e.g., user@example.com):")
        return  # Re-prompt without advancing
    
    user = update.effective_user
    referred_by_id = context.user_data.get('referred_by_id')
    full_name = context.user_data.get('full_name')
    
    success = db.create_or_update_user(
        user.id, user.username, user.first_name, full_name, email, referred_by_id
    )
    
    if success:
        # Clean up registration data
        context.user_data.pop('registration_step', None)
        context.user_data.pop('full_name', None)
        context.user_data.pop('referred_by_id', None)
        
        # Send welcome message
        await send_welcome_message(update, context, user)
        
    else:
        await update.message.reply_text(
            "❌ Registration failed. Please try again or contact support."
        )

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Send concise welcome message to new users"""
    welcome_text = f"""
🎉 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗔𝗯𝗼𝗮𝗿𝗱, {user.first_name}!

🤖 𝗖𝗼𝗿𝗲𝗫 𝗔𝗜 𝗧𝗿𝗮𝗱𝗶𝗻𝗴 𝗕𝗼𝘁

Your automated trading journey starts now! 

🚀 𝗪𝗵𝗮𝘁 𝗡𝗲𝘅𝘁:
• Choose from 5 AI-powered strategies
• Earn 1.38% - 3.14% daily returns
• Withdraw profits anytime
• Grow with compound interest

💡 𝗤𝘂𝗶𝗰𝗸 𝗦𝘁𝗮𝗿𝘁:
1. Pick your strategy in 'Invest'
2. Send crypto payment
3. Start earning daily!

🌟 𝗕𝗼𝗻𝘂𝘀: Refer friends & earn 5% commission

Ready to begin? Explore strategies below! ⬇️
"""

    keyboard = [
        [InlineKeyboardButton("🚀 Start Investing", callback_data="invest_menu")],
        [InlineKeyboardButton("⚙️ Setup Wallet", callback_data="settings_edit_wallet")],
        [InlineKeyboardButton("❓ How It Works", callback_data="faq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    await show_main_menu(update, context, user)

async def handle_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Handle payment details input with verification animation - Enhanced version"""
    user = update.effective_user
    investment_data = context.user_data.get('investment_data')
    
    if not investment_data:
        await update.message.reply_text("❌ Investment session expired. Please start a new investment.")
        context.user_data.pop('awaiting_payment_details', None)
        return
    
    try:
        # Enhanced parsing with better error handling
        lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
        
        # Extract values with flexible parsing
        amount_str = None
        tx_id = None
        network = None
        
        for line in lines:
            if line.lower().startswith('amount:'):
                amount_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '')
            elif 'transaction' in line.lower():
                tx_id = line.split(':', 1)[1].strip() if ':' in line else line
            elif line.lower().startswith('network:'):
                network = line.split(':', 1)[1].strip()
        
        # Validate all required fields
        if not amount_str:
            await update.message.reply_text("❌ Amount is required. Please include 'Amount: $X,XXX'")
            return
        if not tx_id:
            await update.message.reply_text("❌ Transaction ID is required. Please include transaction ID")
            return
        if not network:
            await update.message.reply_text("❌ Network is required. Please include 'Network: [name]'")
            return
        
        amount = float(amount_str)
        strategy = investment_data.get('strategy', 'TREND_FOLLOWING')
        
        # Validate amount matches expected (with tolerance for small differences)
        if 'amount' in investment_data:
            expected_amount = investment_data['amount']
            if abs(amount - expected_amount) > 0.01:  # Allow small rounding differences
                await update.message.reply_text(
                    f"❌ Amount (${amount:,.2f}) does not match your selected investment (${expected_amount:,.2f}). "
                    f"Please check and try again."
                )
                return
        
        # Validate minimum investment
        if amount < 10:
            await update.message.reply_text("❌ Minimum investment amount is $10.")
            return
        
        # Add investment to DB as pending
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investments (user_id, amount, crypto_type, wallet_address, transaction_id, strategy, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id, amount, investment_data.get('crypto_type'), 
                investment_data.get('wallet_address'), tx_id, strategy, 
                f"Network: {network}", 'pending'
            ))
            conn.commit()
            investment_id = cursor.lastrowid
        
        # Clear session data
        context.user_data.pop('awaiting_payment_details', None)
        context.user_data.pop('investment_data', None)
        
        # Animation frames
        animation_frames = [
            "🔄 Verifying your transaction ▰▱▱▱▱▱▱▱▱",
            "🔄 Verifying your transaction ▰▰▱▱▱▱▱▱▱", 
            "🔄 Verifying your transaction ▰▰▰▱▱▱▱▱▱",
            "🔄 Verifying your transaction ▰▰▰▰▱▱▱▱▱",
            "🔄 Verifying your transaction ▰▰▰▰▰▱▱▱▱",
            "🔄 Verifying your transaction ▰▰▰▰▰▰▱▱▱",
            "🔄 Verifying your transaction ▰▰▰▰▰▰▰▱▱",
            "🔄 Verifying your transaction ▰▰▰▰▰▰▰▰▱",
            "🔄 Verifying your transaction ▰▰▰▰▰▰▰▰▰"
        ]
        
        # Send initial frame
        sent_message = await update.message.reply_text(animation_frames[0])
        
        # Animate by editing the message
        for frame in animation_frames[1:]:
            await asyncio.sleep(0.3)  # Slightly faster animation
            try:
                await sent_message.edit_text(frame)
            except Exception as e:
                logging.warning(f"Animation frame update failed: {e}")
                continue
        
        # Final confirmation message
        await asyncio.sleep(0.5)
        await sent_message.edit_text(
            f"✅ 𝗜𝗡𝗩𝗘𝗦𝗧𝗠𝗘𝗡𝗧 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗!\n\n"
            f"💰 Amount: ${amount:,.2f}\n"
            f"🎯 Strategy: {strategy.replace('_', ' ').title()}\n"
            f"📝 Transaction: {tx_id[:20]}...\n"
            f"🌐 Network: {network}\n\n"
            f"Your investment is now pending verification.\n"
            f"You'll receive a confirmation once it's approved!\n\n"
            f"Thank you for investing! 🎉"
        )
        
        # Notify admins
        await notify_admins_new_investment(context, user.id, amount, tx_id, network, strategy, investment_id)
        
    except ValueError as e:
        logging.error(f"Value error in payment details: {e}")
        await update.message.reply_text("❌ Invalid amount format. Please enter a valid number (e.g., 1000 or 500.50).")
    except Exception as e:
        logging.error(f"Error handling payment details: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your details. Please try again or contact support.\n\n"
            "Make sure your message follows this format:\n"
            "Amount: $1,000\n"
            "Transaction ID: abc123...\n"
            "Network: TRC20"
        )

async def handle_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Handle custom withdrawal amount input with stored wallet"""
    try:
        amount = float(message_text.replace('$', '').replace(',', ''))
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User data not found.")
            return
        
        current_balance = user_data[8] if len(user_data) > 8 else 0
        
        # Get user's stored wallet address
        from handlers.settings_handlers import get_user_wallet_address
        wallet_address = get_user_wallet_address(user.id)
        
        if not wallet_address:
            keyboard = [
                [InlineKeyboardButton("⚙️ Add Wallet in Settings", callback_data="settings_edit_wallet")],
                [InlineKeyboardButton("🔙 Back", callback_data="withdraw")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ NO WALLET ADDRESS SAVED\n\n"
                "Please add your USDT wallet address in Settings before withdrawing.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            context.user_data.pop('awaiting_withdraw_amount', None)
            return
        
        if amount < 10:
            await update.message.reply_text("❌ Minimum withdrawal amount is $10.")
            return
        
        if amount > current_balance:
            await update.message.reply_text(f"❌ Insufficient balance. Available: ${current_balance:,.2f}")
            return
        
        # Store withdrawal data with all required information
        context.user_data['pending_withdrawal'] = {
            'amount': amount,
            'user_id': user.id,
            'wallet_address': wallet_address
        }
        context.user_data.pop('awaiting_withdraw_amount', None)
        
        # Show confirmation with stored wallet
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Withdrawal", callback_data="confirm_withdraw_custom")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💸 CONFIRM WITHDRAWAL\n\n"
            f"Amount: ${amount:,.2f}\n"
            f"To Wallet: `{wallet_address}`\n\n"
            f"⚡ Your request will be processed within 24 hours.\n\n"
            f"⚠️ Please verify your wallet address is correct!\n\n"
            f"Confirm withdrawal?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")

async def handle_withdrawal_address(update: Update, context: ContextTypes.DEFAULT_TYPE, wallet_address: str):
    """Handle withdrawal wallet address input"""
    withdrawal_data = context.user_data.get('pending_withdrawal')
    if not withdrawal_data:
        await update.message.reply_text("❌ Withdrawal session expired. Please start again.")
        return
    
    amount = withdrawal_data['amount']
    user_id = withdrawal_data['user_id']
    
    # Basic validation for USDT TRC20 address
    if not wallet_address.startswith('T') or len(wallet_address) != 34:
        await update.message.reply_text(
            "❌ Invalid USDT TRC20 address format.\n\n"
            "TRC20 addresses should:\n"
            "• Start with 'T'\n"
            "• Be exactly 34 characters long\n\n"
            "Please provide a valid address:"
        )
        return
    
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
        
        await send_temporary_message(
            update, context,
            "✅ 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗!\n\n"
            f"💰 Amount: ${amount:,.2f}\n"
            f"💳 Address: `{wallet_address}`\n\n"
            "⏰ Your request is being processed.\n"
            "You'll receive a confirmation once the funds are sent!",
            parse_mode='HTML',
            delete_after=120
        )
        
        # Notify admins - ✅ NOW WE HAVE THE ID!
        await notify_admins_new_withdrawal(context, user_id, amount, wallet_address, withdrawal_id)
        
    except Exception as e:
        logging.error(f"Error saving withdrawal: {e}")
        await update.message.reply_text("❌ Failed to save withdrawal request. Please try again.")
    
    # Clean up
    context.user_data.pop('pending_withdrawal', None)
    
async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Handle admin broadcast message"""
    if len(message_text) > 2000:
        await update.message.reply_text("❌ Message too long. Maximum 2000 characters.")
        return
    
    # Get all users
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
    
    success_count = 0
    total_users = len(users)
    
    # Send broadcast message
    for user_tuple in users:
        try:
            await context.bot.send_message(
                chat_id=user_tuple[0],
                text=f"📢 𝗔𝗡𝗡𝗢𝗨𝗡𝗖𝗘𝗠𝗘𝗡𝗧\n\n{message_text}",
                parse_mode='HTML'
            )
            success_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send broadcast to {user_tuple[0]}: {e}")
    
    await update.message.reply_text(
        f"✅ Broadcast Complete!\n\n"
        f"📊 Sent to: {success_count}/{total_users} users\n"
        f"📈 Success Rate: {(success_count/total_users)*100:.1f}%"
    )
    
    context.user_data.pop('awaiting_broadcast_message', None)
    

# Notification helper functions
async def notify_admins_new_investment(context, user_id, amount, tx_id, network, strategy, investment_id):
    """Notify admins about new crypto investment with balance info"""
    
    # Get user details and current balance
    user_data = db.get_user(user_id)
    if user_data:
        full_name = user_data[3] or 'N/A'
        email = user_data[4] or 'N/A'
        username = user_data[1] or 'N/A'
        current_balance = user_data[8] if len(user_data) > 8 else 0.0
        total_invested = user_data[7] if len(user_data) > 7 else 0.0
    else:
        full_name = email = username = 'N/A'
        current_balance = 0.0
        total_invested = 0.0
    
    # Get user's stored wallet address
    from handlers.settings_handlers import get_user_wallet_address
    wallet_address = get_user_wallet_address(user_id)
    
    notification = f"""
🚨 NEW CRYPTO INVESTMENT 🚨

👤 User Details:
• Name: {full_name}
• Email: {email}
• Username: @{username}
• User ID: {user_id}
• Investment ID: {investment_id}

💰 Account Status:
• Current Balance: ${current_balance:,.2f}
• Total Invested: ${total_invested:,.2f}
• New Investment: ${amount:,.2f}

🎯 Investment Details:
• Strategy: {strategy.replace('_', ' ').title()}
• Transaction ID: `{tx_id}`
• Network: {network}
• Wallet: `{wallet_address or 'Not set'}`

⚠️ Action Required: Verify transaction before confirming.

Command: `/confirm_investment {user_id} {amount}`
    """
    
    for admin_id in ADMIN_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification.strip(),
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

async def notify_admins_new_withdrawal(context, user_id, amount, wallet_address, withdrawal_id=None):
    """Notify admins about new withdrawal request with balance info"""
    user_data = db.get_user(user_id)
    if user_data:
        full_name = user_data[3] or 'N/A'
        email = user_data[4] or 'N/A'
        username = user_data[1] or 'N/A'
        current_balance = user_data[8] if len(user_data) > 8 else 0.0
        total_invested = user_data[7] if len(user_data) > 7 else 0.0
    else:
        full_name = email = username = 'N/A'
        current_balance = 0.0
        total_invested = 0.0
    
    # Calculate new balance after withdrawal
    new_balance = current_balance - amount
    
    withdrawal_id_info = f"Withdrawal ID: {withdrawal_id}\n" if withdrawal_id else ""
    
    notification = f"""
🚨 NEW WITHDRAWAL REQUEST 🚨

👤 User Details:
• Name: {full_name}
• Email: {email}
• Username: @{username}
• User ID: {user_id}
{withdrawal_id_info}
💰 Account Status:
• Current Balance: ${current_balance:,.2f}
• Withdrawal Amount: ${amount:,.2f}
• New Balance After: ${new_balance:,.2f}
• Total Invested: ${total_invested:,.2f}

💸 Withdrawal Details:
• Wallet: `{wallet_address}`
• Network: TRC20 (USDT)
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

⚠️ Action Required: 
• Verify user identity and wallet address
• Check if balance is sufficient
• Process within 24 hours

Command: `/confirm_withdrawal {user_id}`
    """
    
    for admin_id in ADMIN_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification.strip(),
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

async def handle_admin_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Handle admin-specific text message inputs"""
    user = update.effective_user
    
    # Only process for admin users
    if user.id not in ADMIN_USER_IDS:
        return False  # Not handled by admin system
    
    # Handle user search
    if context.user_data.get('awaiting_user_search'):
        await handle_user_search_input(update, context, message_text)
        return True
    
    # Handle balance editing - user ID input
    elif context.user_data.get('awaiting_balance_user_id'):
        await handle_balance_user_id_input(update, context, message_text)
        return True
    
    # Handle balance editing - amount input
    elif context.user_data.get('awaiting_balance_amount'):
        await handle_balance_amount_input(update, context, message_text)
        return True
    
    # Handle broadcast message
    elif context.user_data.get('awaiting_broadcast_message'):
        await handle_broadcast_message_admin(update, context, message_text)
        return True
    
    return False  # Not handled by admin system

async def handle_user_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str):
    """Handle user search input from admin"""
    search_term = search_term.strip()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try different search methods
            users = []
            
            # Search by user ID
            if search_term.isdigit():
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (int(search_term),))
                user = cursor.fetchone()
                if user:
                    users.append(user)
            
            # Search by username
            if not users:
                username = search_term.replace('@', '')
                cursor.execute('SELECT * FROM users WHERE username LIKE ?', (f'%{username}%',))
                users = cursor.fetchall()
            
            # Search by email
            if not users and '@' in search_term:
                cursor.execute('SELECT * FROM users WHERE email LIKE ?', (f'%{search_term}%',))
                users = cursor.fetchall()
            
            # Search by name
            if not users:
                cursor.execute('SELECT * FROM users WHERE full_name LIKE ?', (f'%{search_term}%',))
                users = cursor.fetchall()
    
    except Exception as e:
        logging.error(f"Error in user search: {e}")
        await update.message.reply_text("❌ Error performing search. Please try again.")
        context.user_data.pop('awaiting_user_search', None)
        return
    
    if not users:
        keyboard = [
            [InlineKeyboardButton("🔍 Try Again", callback_data="admin_search_user")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ No users found matching '{search_term}'\n\n"
            "Try searching by:\n"
            "• User ID (numbers only)\n"
            "• Username (with or without @)\n"
            "• Email address\n"
            "• Full name",
            reply_markup=reply_markup
        )
    else:
        text = f"🔍 SEARCH RESULTS ({len(users)} found)\n\n"
        keyboard = []
        
        for user in users[:10]:  # Limit to 10 results
            user_id, username, first_name, full_name, email, reg_date, plan, invested, balance, profit, last_update, referral_code, referred_by, wallet_address = user
            
            # Use plain text without HTML
            text += f"ID: {user_id}\n"
            text += f"Username: @{username or 'N/A'}\n"
            text += f"Name: {full_name or 'N/A'}\n"
            text += f"Email: {email or 'N/A'}\n"
            text += f"Balance: ${balance:,.2f}\n"
            text += f"Invested: ${invested:,.2f}\n"
            text += "─────────────\n"
            
            keyboard.append([InlineKeyboardButton(f"View {username or user_id}", callback_data=f"admin_user_profile_{user_id}")])
        
        if len(users) > 10:
            text += f"\n... and {len(users) - 10} more results"
        
        keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Remove parse_mode parameter
        await update.message.reply_text(text.strip(), reply_markup=reply_markup)
    
    context.user_data.pop('awaiting_user_search', None)

async def handle_balance_user_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id_str: str):
    """Handle user ID input for balance editing"""
    try:
        # Clean the input - remove any extra characters
        cleaned_input = user_id_str.strip().replace('@', '').replace('#', '')
        
        # Try to parse as integer
        user_id = int(cleaned_input)
        
        # Debug logging
        logging.info(f"Admin balance edit: searching for user ID {user_id}")
        
        # Verify user exists
        user_data = db.get_user(user_id)
        
        if not user_data:
            # Get total user count for debugging
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                
                # Show some example user IDs
                cursor.execute('SELECT user_id FROM users ORDER BY registration_date DESC LIMIT 3')
                example_ids = [str(row[0]) for row in cursor.fetchall()]
            
            keyboard = [
                [InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")],
                [InlineKeyboardButton("👥 View All Users", callback_data="admin_user_list")],
                [InlineKeyboardButton("🔙 Balance Menu", callback_data="admin_edit_balance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ USER NOT FOUND\n\n"
                f"User ID '{user_id}' does not exist in the database.\n\n"
                f"Database Info:\n"
                f"• Total users: {total_users}\n"
                f"• Recent user IDs: {', '.join(example_ids)}\n\n"
                f"What to try:\n"
                f"• Use 'Search User' to find by username\n"
                f"• Use 'View All Users' to browse\n"
                f"• Double-check the user ID number\n"
                f"• Make sure user has used /start",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            context.user_data.pop('awaiting_balance_user_id', None)
            return
        
        # User found - store data for next step
        context.user_data['balance_target_user'] = user_data
        context.user_data.pop('awaiting_balance_user_id', None)
        
        action = context.user_data.get('balance_action')
        current_balance = user_data[8]  # current_balance field
        username = user_data[1]
        full_name = user_data[3]
        
        logging.info(f"User found: {username} (ID: {user_id}) - Balance: ${current_balance}")
        
        if action == "reset":
            # Direct reset, no amount needed
            await confirm_balance_change(update, context, 0, "RESET")
        else:
            context.user_data['awaiting_balance_amount'] = True
            
            action_text = {
                "add": "ADD to",
                "subtract": "SUBTRACT from", 
                "set": "SET as new balance for"
            }
            
            keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_edit_balance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ USER FOUND!\n\n"
                f"💳 {action_text[action].upper()} USER BALANCE\n\n"
                f"User: @{username} ({full_name or 'N/A'})\n"
                f"User ID: {user_data[0]}\n"
                f"Current Balance: ${current_balance:,.2f}\n\n"
                f"Enter the amount to {action}:\n\n"
                f"Examples:\n"
                f"• 100\n"
                f"• 500.50\n"
                f"• 1000\n\n"
                f"Type the amount below:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    except ValueError:
        await update.message.reply_text(
            f"❌ INVALID FORMAT\n\n"
            f"'{user_id_str}' is not a valid user ID.\n\n"
            f"Please enter:\n"
            f"• Numbers only (e.g., 123456789)\n"
            f"• No letters, symbols, or spaces\n\n"
            f"Example: 652353552"
        )

async def handle_balance_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_str: str):
    """Handle amount input for balance editing"""
    try:
        amount = float(amount_str.strip().replace('$', '').replace(',', ''))
        
        if amount < 0:
            await update.message.reply_text("❌ Amount cannot be negative. Please enter a positive number.")
            return
        
        action = context.user_data.get('balance_action')
        if action == 'subtract' and amount <= 0:
            await update.message.reply_text("❌ Subtraction amount must be greater than 0.")
            return
        
        await confirm_balance_change(update, context, amount, action.upper())
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount format.\n\n"
            "Please enter a valid number:\n"
            "• 100\n"
            "• 500.50\n"
            "• 1000"
        )

async def confirm_balance_change(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float, action: str):
    """Show confirmation for balance change"""
    user_data = context.user_data.get('balance_target_user')
    if not user_data:
        await update.message.reply_text("❌ Session expired. Please start over.")
        return
    
    target_user_id = user_data[0]
    username = user_data[1]
    full_name = user_data[3]
    current_balance = user_data[8]
    
    # Calculate new balance
    if action == "ADD":
        new_balance = current_balance + amount
    elif action == "SUBTRACT":
        new_balance = max(0, current_balance - amount)  # Don't go negative
    elif action == "SET":
        new_balance = amount
    elif action == "RESET":
        new_balance = 0
        amount = current_balance  # For logging purposes
    
    # Store confirmation data
    context.user_data['balance_confirmation'] = {
        'target_user_id': target_user_id,
        'username': username,
        'full_name': full_name,
        'action': action,
        'amount': amount,
        'old_balance': current_balance,
        'new_balance': new_balance
    }
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="admin_confirm_balance_change")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_edit_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    warning = ""
    if action == "SUBTRACT" and amount > current_balance:
        warning = "\n⚠️ Warning: Amount exceeds current balance. Balance will be set to $0.00"
    
    await update.message.reply_text(
        f"⚠️ CONFIRM BALANCE CHANGE\n\n"
        f"User: @{username} ({full_name or 'N/A'})\n"
        f"Action: {action}\n"
        f"Amount: ${amount:,.2f}\n"
        f"Current Balance: ${current_balance:,.2f}\n"
        f"New Balance: ${new_balance:,.2f}\n"
        f"{warning}\n\n"
        f"⚠️ This action cannot be undone!\n"
        f"Are you sure you want to proceed?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Clean up temporary states
    context.user_data.pop('awaiting_balance_amount', None)
    context.user_data.pop('balance_action', None)
    context.user_data.pop('balance_target_user', None)


async def handle_broadcast_message_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Handle broadcast message from admin"""
    if len(message_text) > 2000:
        await update.message.reply_text("❌ Message too long. Maximum 2000 characters allowed.")
        return
    
    # Store message for confirmation
    context.user_data['broadcast_message'] = message_text
    context.user_data.pop('awaiting_broadcast_message', None)
    
    keyboard = [
        [InlineKeyboardButton("✅ Send Broadcast", callback_data="admin_confirm_broadcast")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get user count
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
    
    await update.message.reply_text(
        f"📢 BROADCAST PREVIEW\n\n"
        f"Message:\n{message_text}\n\n"
        f"Recipients: {user_count} users\n\n"
        f"⚠️ Warning: This will send the message to all users immediately and cannot be undone!\n\n"
        f"Are you sure you want to send this broadcast?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# Add these callback handlers to your existing admin_handlers.py

async def handle_balance_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle balance change confirmation callback"""
    confirmation_data = context.user_data.get('balance_confirmation')
    if not confirmation_data:
        await update.callback_query.message.edit_text("❌ Session expired. Please start over.")
        return
    
    target_user_id = confirmation_data['target_user_id']
    username = confirmation_data['username']
    full_name = confirmation_data['full_name']
    action = confirmation_data['action']
    amount = confirmation_data['amount']
    old_balance = confirmation_data['old_balance']
    new_balance = confirmation_data['new_balance']
    
    admin_id = update.callback_query.from_user.id
    
    try:
        # Update user balance in database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET current_balance = ? WHERE user_id = ?
            ''', (new_balance, target_user_id))
            conn.commit()
        
        # Log the admin action
        log_admin_action(
            admin_id=admin_id,
            action_type=f"balance_{action.lower()}",
            target_user_id=target_user_id,
            amount=amount,
            old_balance=old_balance,
            new_balance=new_balance,
            notes=f"Admin balance modification: {action}"
        )
        
        # Send confirmation
        await update.callback_query.message.edit_text(
            f"✅ BALANCE UPDATED SUCCESSFULLY\n\n"
            f"User: @{username} ({full_name or 'N/A'})\n"
            f"Action: {action}\n"
            f"Amount: ${amount:,.2f}\n"
            f"Previous Balance: ${old_balance:,.2f}\n"
            f"New Balance: ${new_balance:,.2f}\n\n"
            f"✅ Change has been logged in admin records.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Edit Another Balance", callback_data="admin_edit_balance")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
            ]),
            parse_mode='HTML'
        )
        
        # Notify the user about balance change
        try:
            if action == "ADD":
                notification = f"🎉 BALANCE UPDATED!\n\n💰 ${amount:,.2f} has been added to your account!\n\nNew Balance: ${new_balance:,.2f}"
            elif action == "SUBTRACT":
                notification = f"ℹ️ BALANCE UPDATED\n\n💸 ${amount:,.2f} has been deducted from your account.\n\nNew Balance: ${new_balance:,.2f}"
            elif action == "SET":
                notification = f"ℹ️ BALANCE UPDATED\n\n💳 Your balance has been set to ${new_balance:,.2f}"
            elif action == "RESET":
                notification = f"ℹ️ BALANCE RESET\n\n💳 Your account balance has been reset to $0.00"
            
            await context.bot.send_message(
                chat_id=target_user_id,
                text=notification,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to notify user {target_user_id} about balance change: {e}")
    
    except Exception as e:
        logging.error(f"Error updating user balance: {e}")
        await update.callback_query.message.edit_text(
            f"❌ ERROR UPDATING BALANCE\n\n{str(e)}\n\nPlease try again or contact technical support.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
    
    # Clean up
    context.user_data.pop('balance_confirmation', None)

async def handle_broadcast_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast confirmation callback"""
    broadcast_message = context.user_data.get('broadcast_message')
    if not broadcast_message:
        await update.callback_query.message.edit_text("❌ Session expired. Please start over.")
        return
    
    # Get all users
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
    
    success_count = 0
    total_users = len(users)
    admin_id = update.callback_query.from_user.id
    
    # Update message to show progress
    await update.callback_query.message.edit_text(
        f"📢 SENDING BROADCAST...\n\n"
        f"📤 Sending to {total_users} users...\n"
        f"⏳ Please wait...",
        parse_mode='HTML'
    )
    
    # Send broadcast message
    for user_tuple in users:
        try:
            await context.bot.send_message(
                chat_id=user_tuple[0],
                text=f"📢 ANNOUNCEMENT\n\n{broadcast_message}",
                parse_mode='HTML'
            )
            success_count += 1
            await asyncio.sleep(0.05)  # Rate limiting to avoid hitting limits
        except Exception as e:
            logging.error(f"Failed to send broadcast to {user_tuple[0]}: {e}")
    
    # Log the broadcast
    log_admin_action(
        admin_id=admin_id,
        action_type="broadcast_message",
        notes=f"Broadcast sent to {success_count}/{total_users} users"
    )
    
    # Send completion message
    await update.callback_query.message.edit_text(
        f"✅ BROADCAST COMPLETE!\n\n"
        f"📊 Results:\n"
        f"• Total Users: {total_users}\n"
        f"• Successfully Sent: {success_count}\n"
        f"• Failed: {total_users - success_count}\n"
        f"• Success Rate: {(success_count/total_users)*100:.1f}%\n\n"
        f"✅ Broadcast has been logged in admin records.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Send Another", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
        ]),
        parse_mode='HTML'
    )
    
    # Clean up
    context.user_data.pop('broadcast_message', None)

# Update the main handle_admin_callback function to include new callbacks
def update_admin_callback_handler():
    """Add these cases to your existing handle_admin_callback function"""
    # Add these cases to the existing function:
    
    # elif data == "admin_confirm_balance_change":
    #     await handle_balance_confirmation_callback(update, context)
    # elif data == "admin_confirm_broadcast":
    #     await handle_broadcast_confirmation_callback(update, context)
    
    pass

