"""
Admin command handlers - Complete functionality
"""
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.utils import clear_awaiting_states

from .message_handlers import handle_broadcast_confirmation_callback
from handlers.message_handlers import confirm_balance_change

from .message_handlers import handle_balance_confirmation_callback
from config import ADMIN_USER_IDS
from database import db

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
        
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Main admin panel"""
    user = update.effective_user
    if user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("❌ You do not have permission to access the admin panel.")
        return
    
    keyboard = [
        [InlineKeyboardButton("💰 Pending Investments", callback_data="admin_investments"),
         InlineKeyboardButton("💸 Pending Withdrawals", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("👥 User Management", callback_data="admin_user_management"),
         InlineKeyboardButton("📊 Bot Statistics", callback_data="admin_user_stats")],
        [InlineKeyboardButton("💳 Edit User Balance", callback_data="admin_edit_balance"),
         InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"),
         InlineKeyboardButton("📋 Admin Logs", callback_data="admin_logs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    stats = db.get_user_stats()
    text = f"""
🛠️ ADMIN CONTROL PANEL

📊 Quick Stats:
• Total Users: {stats.get('total_users', 0)}
• Active Investors: {stats.get('active_investors', 0)}
• Pending Investments: {stats.get('pending_investments', 0)}
• Pending Withdrawals: {stats.get('pending_withdrawals', 0)}

Select an option below:
    """
    
    if update.message:
        await update.message.reply_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Complete admin callback handler with all new features"""
    user = update.callback_query.from_user
    if user.id not in ADMIN_USER_IDS:
        await update.callback_query.message.edit_text("❌ Access denied.")
        return
    
    logging.info(f"Admin callback received: {data}")

    # Parse callback data
    if data == "admin_panel":
        clear_awaiting_states(context)
        await admin_command(update, context)
    elif data == "admin_investments":
        await show_pending_investments(update, context)
   # SPECIFIC WITHDRAWAL BRANCHES FIRST
    elif data.startswith("admin_confirm_withdrawal_"):
        withdrawal_id = int(data.split("_")[-1])
        await handle_withdrawal_confirmation(update, context, withdrawal_id)
    elif data.startswith("admin_reject_withdrawal_"):
        withdrawal_id = int(data.split("_")[-1])
        await handle_withdrawal_rejection(update, context, withdrawal_id)

    # THEN GENERAL INVESTMENT BRANCHES
    elif data.startswith("admin_confirm_"):
        await handle_admin_confirmation(update, context, data)
    elif data.startswith("admin_reject_"):
        await handle_admin_rejection(update, context, data)
    elif data == "admin_user_management":
        await show_user_management(update, context)
    elif data == "admin_user_stats":
        await show_user_stats(update, context)
    elif data == "admin_edit_balance":
        await show_balance_edit_menu(update, context)
    elif data == "admin_search_user":
        await setup_user_search(update, context)
    elif data == "admin_broadcast":
        await setup_broadcast_message(update, context)
    elif data == "admin_logs":
        await show_admin_logs(update, context)
    elif data == "admin_user_list":
        await show_user_list(update, context, 0)
    elif data.startswith("admin_user_list_"):
        page = int(data.split("_")[-1])
        await show_user_list(update, context, page)
    elif data.startswith("admin_user_profile_"):
        user_id = int(data.split("_")[-1])
        await show_user_profile(update, context, user_id)
    elif data == "admin_confirm_balance_change":
        await handle_balance_confirmation_callback(update, context)
    elif data == "admin_confirm_broadcast":
        await handle_broadcast_confirmation_callback(update, context)

    elif data.startswith("admin_balance_"):
        await handle_balance_edit_callback(update, context, data)
    elif data.startswith("admin_edit_user_balance_"):
        user_id = int(data.split("_")[-1])
        await show_balance_edit_menu_for_user(update, context, user_id)

    elif data.startswith("admin_edit_profile_"):
        user_id = int(data.split("_")[-1])
        await show_user_edit_profile_menu(update, context, user_id)
    elif data.startswith("admin_edit_investments_"):
        user_id = int(data.split("_")[-1])
        await show_user_investments_edit(update, context, user_id)
    elif data.startswith("admin_user_history_"):
        user_id = int(data.split("_")[-1])
        await show_user_transaction_history_admin(update, context, user_id)
    elif data.startswith("admin_edit_name_"):
        user_id = int(data.split("_")[-1])
        await setup_name_edit(update, context, user_id)
    elif data.startswith("admin_edit_email_"):
        user_id = int(data.split("_")[-1])
        await setup_email_edit(update, context, user_id)
    elif data.startswith("admin_edit_regdate_"):
        user_id = int(data.split("_")[-1])
        await setup_regdate_edit(update, context, user_id)
    elif data.startswith("admin_edit_plan_"):
        user_id = int(data.split("_")[-1])
        await show_strategy_edit_menu(update, context, user_id)
    elif data.startswith("admin_set_strategy_"):  # Upgraded from "admin_set_plan_"
        parts = data.split("_")
        user_id = int(parts[3])
        strategy = "_".join(parts[4:])  # e.g., "TREND_FOLLOWING"
        
        if strategy == "NONE":
            strategy = None
        
        # Update user strategy in DB
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET strategy = ? WHERE user_id = ?', (strategy, user_id))
            conn.commit()
        
        await update.callback_query.message.edit_text(
            f"✅ User strategy updated to: {strategy if strategy else 'NONE'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"admin_edit_profile_{user_id}")]])
        )
    elif data.startswith("admin_reset_refcode_"):
        user_id = int(data.split("_")[-1])
        await reset_referral_code(update, context, user_id)
    elif data.startswith("admin_delete_user_"):
        user_id = int(data.split("_")[-1])
        await confirm_user_deletion(update, context, user_id)
    elif data.startswith("admin_edit_inv_"):
        inv_id = int(data.split("_")[-1])
        await show_investment_edit_menu(update, context, inv_id)
    elif data.startswith("admin_add_investment_"):
        user_id = int(data.split("_")[-1])
        await setup_add_investment(update, context, user_id)
    # --- NEW CASES FOR FIELD EDITS ---
    elif data.startswith("admin_edit_inv_amount_"):
        inv_id = int(data.split("_")[-1])
        await setup_investment_amount_edit(update, context, inv_id)
    elif data.startswith("admin_edit_inv_status_"):
        inv_id = int(data.split("_")[-1])
        await setup_investment_status_edit(update, context, inv_id)
    elif data.startswith("admin_edit_inv_plan_"):
        inv_id = int(data.split("_")[-1])
        await setup_investment_plan_edit(update, context, inv_id)

    else:
        await update.callback_query.message.edit_text(
            "❌ Unknown admin action.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )


async def show_balance_edit_menu_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show balance edit options for a specific user directly from their profile"""
    user_data = db.get_user(user_id)
    if not user_data:
        await update.callback_query.message.edit_text("❌ User not found.")
        return

    username = user_data[1]
    full_name = user_data[3]
    current_balance = user_data[8]

    keyboard = [
        [InlineKeyboardButton("➕ Add Balance", callback_data=f"admin_balance_add_{user_id}")],
        [InlineKeyboardButton("➖ Subtract Balance", callback_data=f"admin_balance_subtract_{user_id}")],
        [InlineKeyboardButton("🎯 Set Balance", callback_data=f"admin_balance_set_{user_id}")],
        [InlineKeyboardButton("🔄 Reset Balance", callback_data=f"admin_balance_reset_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"admin_user_profile_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text(
        f"💳 EDIT BALANCE — @{username}\n\n"
        f"Full Name: {full_name or 'N/A'}\n"
        f"Current Balance: ${current_balance:,.2f}\n\n"
        f"Choose an action below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )



async def setup_investment_status_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, inv_id: int):
    """Setup investment status editing"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, status FROM investments WHERE id = ?', (inv_id,))
        result = cursor.fetchone()
    
    if not result:
        await update.callback_query.message.edit_text("❌ Investment not found.")
        return
    
    user_id, current_status = result
    
    context.user_data['investment_edit_data'] = {
        'investment_id': inv_id,
        'user_id': user_id,
        'field': 'status'
    }
    context.user_data['awaiting_investment_edit'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_inv_{inv_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"📊 EDIT INVESTMENT STATUS\n\n"
        f"Current Status: {current_status.title()}\n\n"
        f"Enter the new status:\n\n"
        f"Possible values: pending, confirmed, rejected\n\n"
        f"Type the new status below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def setup_investment_plan_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, inv_id: int):
    """Setup investment plan editing"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, plan FROM investments WHERE id = ?', (inv_id,))
        result = cursor.fetchone()
    
    if not result:
        await update.callback_query.message.edit_text("❌ Investment not found.")
        return
    
    user_id, current_plan = result
    
    context.user_data['investment_edit_data'] = {
        'investment_id': inv_id,
        'user_id': user_id,
        'field': 'plan'
    }
    context.user_data['awaiting_investment_edit'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_inv_{inv_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"🎯 EDIT INVESTMENT PLAN\n\n"
        f"Current Plan: {current_plan or 'None'}\n\n"
        f"Enter the new plan name:\n\n"
        f"Examples:\n"
        f"• basic\n"
        f"• standard\n"
        f"• premium\n\n"
        f"Type the new plan below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def setup_regdate_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup registration date editing"""
    user_data = db.get_user(user_id)
    current_date = user_data[5][:10] if user_data and user_data[5] else 'N/A'
    
    context.user_data['edit_user_id'] = user_id
    context.user_data['edit_field'] = 'regdate'
    context.user_data['awaiting_user_edit'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_profile_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"📅 EDIT REGISTRATION DATE\n\n"
        f"Current Date: {current_date}\n\n"
        f"Enter the new registration date:\n\n"
        f"Format: YYYY-MM-DD\n"
        f"Examples:\n"
        f"• 2024-01-15\n"
        f"• 2023-12-25\n"
        f"• 2024-03-10\n\n"
        f"Type the new date below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def set_user_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, plan: str):
    """Set user's investment plan"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET plan = ? WHERE user_id = ?', (plan, user_id))
            conn.commit()
        
        # Log the action
        log_admin_action(
            admin_id=update.callback_query.from_user.id,
            action_type="plan_change",
            target_user_id=user_id,
            notes=f"Plan changed to: {plan or 'None'}"
        )
        
        plan_display = plan or "None"
        await update.callback_query.message.edit_text(
            f"✅ PLAN UPDATED\n\n"
            f"User's investment plan changed to: {plan_display}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Edit More", callback_data=f"admin_edit_profile_{user_id}")],
                [InlineKeyboardButton("👤 View Profile", callback_data=f"admin_user_profile_{user_id}")]
            ]),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error setting user plan: {e}")
        await update.callback_query.message.edit_text(f"❌ Error updating plan: {str(e)}")

async def confirm_user_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show confirmation for user deletion"""
    user_data = db.get_user(user_id)
    if not user_data:
        await update.callback_query.message.edit_text("❌ User not found.")
        return
    
    username = user_data[1]
    full_name = user_data[3]
    
    keyboard = [
        [InlineKeyboardButton("⚠️ YES, DELETE USER", callback_data=f"admin_confirm_delete_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"admin_user_profile_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"⚠️ CONFIRM USER DELETION\n\n"
        f"User: @{username} ({full_name or 'N/A'})\n"
        f"ID: {user_id}\n\n"
        f"⚠️ WARNING: This will permanently delete:\n"
        f"• User profile and account\n"
        f"• All investments and transactions\n"
        f"• Transaction history\n"
        f"• Referral data\n\n"
        f"THIS CANNOT BE UNDONE!\n\n"
        f"Are you absolutely sure?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_investment_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, inv_id: int):
    """Show investment editing menu"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.user_id, i.amount, i.crypto_type, i.status, i.plan, u.username
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.id = ?
        ''', (inv_id,))
        investment = cursor.fetchone()
    
    if not investment:
        await update.callback_query.message.edit_text("❌ Investment not found.")
        return
    
    user_id, amount, crypto, status, plan, username = investment
    
    keyboard = [
        [InlineKeyboardButton("💰 Edit Amount", callback_data=f"admin_edit_inv_amount_{inv_id}")],
        [InlineKeyboardButton("📊 Edit Status", callback_data=f"admin_edit_inv_status_{inv_id}")],
        [InlineKeyboardButton("🎯 Edit Plan", callback_data=f"admin_edit_inv_plan_{inv_id}")],
        [InlineKeyboardButton("🗑️ Delete Investment", callback_data=f"admin_delete_inv_{inv_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"admin_edit_investments_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"✏️ EDIT INVESTMENT {inv_id}\n\n"
        f"User: @{username}\n"
        f"Amount: ${amount:,.2f}\n"
        f"Crypto: {crypto.upper()}\n"
        f"Status: {status.title()}\n"
        f"Plan: {plan}\n\n"
        f"Select what to edit:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


# Add these handlers to process individual field edits
async def handle_individual_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle individual field edit callbacks"""
    parts = data.split("_")
    
    if "inv" in data and "amount" in data:
        inv_id = int(parts[-1])
        await setup_investment_amount_edit(update, context, inv_id)
    elif "inv" in data and "status" in data:
        inv_id = int(parts[-1])
        await setup_investment_status_edit(update, context, inv_id)
    elif "inv" in data and "plan" in data:
        inv_id = int(parts[-1])
        await setup_investment_plan_edit(update, context, inv_id)

# --- STUBS FOR MISSING FUNCTIONS ---
async def show_user_edit_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show menu for editing user profile fields"""
    user_data = db.get_user(user_id)
    if not user_data:
        await update.callback_query.message.edit_text("❌ User not found.")
        return
    
    # Safe unpacking of user data
    username = user_data[1] if len(user_data) > 1 else None
    full_name = user_data[3] if len(user_data) > 3 else None
    email = user_data[4] if len(user_data) > 4 else None
    reg_date = user_data[5] if len(user_data) > 5 else None
    plan = user_data[6] if len(user_data) > 6 else None
    referral_code = user_data[11] if len(user_data) > 11 else None
    wallet_address = user_data[13] if len(user_data) > 13 else None
    
    text = f"""
👤 EDIT USER PROFILE - @{username or 'N/A'}

Current Details:
• Name: {full_name or 'N/A'}
• Email: {email or 'N/A'}
• Reg Date: {reg_date[:10] if reg_date else 'N/A'}
• Plan: {plan or 'None'}
• Wallet: {wallet_address[:20] + '...' if wallet_address else 'Not set'}
• Ref Code: {referral_code or 'None'}

Choose field to edit:
    """
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"admin_edit_name_{user_id}"),
         InlineKeyboardButton("📧 Edit Email", callback_data=f"admin_edit_email_{user_id}")],
        [InlineKeyboardButton("📅 Edit Reg Date", callback_data=f"admin_edit_regdate_{user_id}"),
         InlineKeyboardButton("🎯 Edit Strategy", callback_data=f"admin_edit_plan_{user_id}")],
        [InlineKeyboardButton("💳 Edit Wallet", callback_data=f"admin_edit_wallet_{user_id}"),
         InlineKeyboardButton("🔄 Reset Ref Code", callback_data=f"admin_reset_refcode_{user_id}")],
        [InlineKeyboardButton("🗑️ Delete User", callback_data=f"admin_delete_user_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Profile", callback_data=f"admin_user_profile_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def setup_wallet_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup for editing user wallet address"""
    context.user_data['awaiting_user_edit'] = True
    context.user_data['edit_field'] = 'wallet'
    context.user_data['edit_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_profile_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "💳 EDIT WALLET ADDRESS\n\n"
        "Enter the new USDT TRC20 wallet address:\n\n"
        "Requirements:\n"
        "• Must start with 'T'\n"
        "• Must be exactly 34 characters\n"
        "• TRC20 network only\n\n"
        "Type the new wallet address below:",
        reply_markup=reply_markup
    )
    
async def show_user_investments_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show list of user's investments for editing"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, amount, plan, status, investment_date 
            FROM investments 
            WHERE user_id = ? 
            ORDER BY investment_date DESC
        ''', (user_id,))
        investments = cursor.fetchall()
    
    if not investments:
        text = "💰 USER INVESTMENTS\n\nNo investments found for this user."
        keyboard = [
            [InlineKeyboardButton("➕ Add New Investment", callback_data=f"admin_add_investment_{user_id}")],
            [InlineKeyboardButton("🔙 Back to Profile", callback_data=f"admin_user_profile_{user_id}")]
        ]
    else:
        text = "💰 EDIT USER INVESTMENTS\n\n"
        keyboard = []
        
        for inv_id, amount, plan, status, date in investments:
            text += f"ID: {inv_id}\n"
            text += f"Amount: ${amount:,.2f}\n"
            text += f"Plan: {plan or 'N/A'}\n"
            text += f"Status: {status.title()}\n"
            text += f"Date: {date[:10]}\n"
            text += "─────────────\n"
            
            keyboard.append([InlineKeyboardButton(f"✏️ Edit Inv {inv_id}", callback_data=f"admin_edit_inv_{inv_id}")])
        
        keyboard.append([InlineKeyboardButton("➕ Add New Investment", callback_data=f"admin_add_investment_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Profile", callback_data=f"admin_user_profile_{user_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')


async def show_user_transaction_history_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show detailed transaction history for admin"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 'Investment' as type, amount, investment_date as date, status, plan as details
            FROM investments WHERE user_id = ?
            UNION ALL
            SELECT 'Withdrawal' as type, amount, withdrawal_date as date, status, wallet_address as details
            FROM withdrawals WHERE user_id = ?
            UNION ALL
            ORDER BY date DESC LIMIT 50
        ''', (user_id, user_id, user_id, user_id))
        transactions = cursor.fetchall()
    
    if not transactions:
        text = "📜 USER TRANSACTION HISTORY\n\nNo transactions found."
    else:
        text = "📜 USER TRANSACTION HISTORY\n\n"
        for tx_type, amount, date, status, details in transactions:
            status_emoji = {"confirmed": "✅", "pending": "⏳", "rejected": "❌"}.get(status, "❓")
            type_emoji = {"Investment": "💰", "Withdrawal": "💸"}.get(tx_type, "📋")
            
            text += f"{type_emoji} {tx_type}\n"
            text += f"   Amount: ${amount:,.2f}\n"
            text += f"   Status: {status_emoji} {status.title()}\n"
            text += f"   Details: {details}\n"
            text += f"   Date: {date[:16] if date else 'N/A'}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"admin_user_history_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Profile", callback_data=f"admin_user_profile_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def setup_name_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup for editing user name"""
    context.user_data['awaiting_user_edit'] = True
    context.user_data['edit_field'] = 'name'
    context.user_data['edit_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_profile_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "✏️ EDIT NAME\n\n"
        "Enter the new full name (min 2 characters):",
        reply_markup=reply_markup
    )

async def setup_email_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup for editing user email"""
    context.user_data['awaiting_user_edit'] = True
    context.user_data['edit_field'] = 'email'
    context.user_data['edit_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_profile_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "📧 EDIT EMAIL\n\n"
        "Enter the new email address:",
        reply_markup=reply_markup
    )

async def setup_regdate_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup for editing registration date"""
    context.user_data['awaiting_user_edit'] = True
    context.user_data['edit_field'] = 'regdate'
    context.user_data['edit_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_profile_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "📅 EDIT REGISTRATION DATE\n\n"
        "Enter the new date in YYYY-MM-DD format\n"
        "Example: 2024-01-15",
        reply_markup=reply_markup
    )

async def show_strategy_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show menu for editing user strategy (Upgraded from plan edit)"""
    keyboard = [
        [InlineKeyboardButton("🥉 TREND FOLLOWING", callback_data=f"admin_set_strategy_{user_id}_TREND_FOLLOWING"),
         InlineKeyboardButton("🥈 MOMENTUM TRADING", callback_data=f"admin_set_strategy_{user_id}_MOMENTUM_TRADING")],
        [InlineKeyboardButton("🥇 MEAN REVERSION", callback_data=f"admin_set_strategy_{user_id}_MEAN_REVERSION"),
         InlineKeyboardButton("🏆 SCALPING", callback_data=f"admin_set_strategy_{user_id}_SCALPING")],
        [InlineKeyboardButton("💎 ARBITRAGE", callback_data=f"admin_set_strategy_{user_id}_ARBITRAGE"),
         InlineKeyboardButton("❌ NONE", callback_data=f"admin_set_strategy_{user_id}_NONE")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"admin_edit_profile_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "🎯 EDIT USER STRATEGY\n\n"
        "Select the new strategy:",
        reply_markup=reply_markup
    )
    
async def show_referral_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral system statistics for admin"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Total referrals
        cursor.execute('SELECT COUNT(*) FROM referrals')
        total_referrals = cursor.fetchone()[0]
        
        # Total bonus paid
        cursor.execute('SELECT COALESCE(SUM(bonus_amount), 0) FROM referrals')
        total_bonus = cursor.fetchone()[0]
        
        # Active referrers (users with referrals)
        cursor.execute('SELECT COUNT(DISTINCT referrer_id) FROM referrals')
        active_referrers = cursor.fetchone()[0]
        
        # Top referrers
        cursor.execute('''
            SELECT u.username, u.user_id, 
                   COUNT(r.id) as ref_count,
                   COALESCE(SUM(r.bonus_amount), 0) as total_earned
            FROM users u
            JOIN referrals r ON u.user_id = r.referrer_id
            GROUP BY u.user_id
            ORDER BY ref_count DESC
            LIMIT 10
        ''')
        top_referrers = cursor.fetchall()
    
    text = f"""📊 REFERRAL SYSTEM STATISTICS

📈 Overview:
- Total Referrals: {total_referrals}
- Total Bonus Paid: ${total_bonus:,.2f}
- Active Referrers: {active_referrers}
- Average per Referrer: {total_referrals/max(active_referrers, 1):.1f}

🏆 Top Referrers:
"""
    
    for i, (username, user_id, ref_count, earned) in enumerate(top_referrers, 1):
        text += f"{i}. @{username or user_id} - {ref_count} refs (${earned:,.2f})\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_referral_stats")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup)

# Add to admin panel keyboard:
# [InlineKeyboardButton("👥 Referral Stats", callback_data="admin_referral_stats")]

async def reset_referral_code(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Reset user's referral code"""
    import random
    import string
    
    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (new_code, user_id))
        conn.commit()
    
    log_admin_action(
        admin_id=update.effective_user.id,
        action_type="reset_referral_code",
        target_user_id=user_id,
        notes=f"New code: {new_code}"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 View Profile", callback_data=f"admin_user_profile_{user_id}"),
         InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"✅ REFERRAL CODE RESET\n\n"
        f"New Code: {new_code}",
        reply_markup=reply_markup
    )

async def setup_add_investment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Setup for adding new investment"""
    context.user_data['awaiting_investment_edit'] = True
    context.user_data['investment_edit_data'] = {
        'user_id': user_id,
        'field': 'add_investment'  # Special field for add
    }
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_investments_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "➕ ADD NEW INVESTMENT\n\n"
        "Enter details in format:\n"
        "Amount: 5000\n"
        "Strategy: jb\n"
        "Status: confirmed",
        reply_markup=reply_markup
    )



async def setup_investment_amount_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, inv_id: int):
    """Setup investment amount editing"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, amount FROM investments WHERE id = ?', (inv_id,))
        result = cursor.fetchone()
    
    if not result:
        await update.callback_query.message.edit_text("❌ Investment not found.")
        return
    
    user_id, current_amount = result
    
    context.user_data['investment_edit_data'] = {
        'investment_id': inv_id,
        'user_id': user_id,
        'field': 'amount'
    }
    context.user_data['awaiting_investment_edit'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_edit_inv_{inv_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"💰 EDIT INVESTMENT AMOUNT\n\n"
        f"Current Amount: ${current_amount:,.2f}\n\n"
        f"Enter the new investment amount:\n\n"
        f"Examples:\n"
        f"• 1000\n"
        f"• 5500.50\n"
        f"• 25000\n\n"
        f"Type the new amount below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# Similar setup functions for other fields would follow the same pattern...

def log_admin_action(admin_id: int, action_type: str, target_user_id: int = None, 
                          amount: float = None, old_balance: float = None, 
                          new_balance: float = None, notes: str = None):
    """Enhanced admin action logging"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_balance_logs 
                (admin_id, target_user_id, action_type, amount, old_balance, new_balance, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (admin_id, target_user_id, action_type, amount, old_balance, new_balance, notes))
            conn.commit()
    except Exception as e:
        logging.error(f"Failed to log admin action: {e}")

def get_price_direction_emoji(change_percent):
    """Get emoji based on price direction"""
    if change_percent > 0:
        return "📈"
    elif change_percent < 0:
        return "📉"
    else:
        return "➡️"
    
async def show_pending_investments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending crypto investments"""
    pending_investments = db.get_pending_investments()
    
    if not pending_investments:
        text = "✅ No pending investments at the moment."
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        return
    
    text = "💰 PENDING CRYPTO INVESTMENTS\n\n"
    keyboard = []
    
    for inv in pending_investments[:5]:  # Show max 5 at a time
        inv_id, user_id, username, full_name, email, amount, crypto_type, tx_id, date, notes = inv
        
        # Safe handling of None values
        username_display = username or 'N/A'
        full_name_display = full_name or 'N/A'
        crypto_display = (crypto_type or 'N/A').upper()
        tx_id_display = (tx_id or 'N/A')[:20] + '...' if tx_id else 'N/A'
        date_display = (date or 'N/A')[:16] if date else 'N/A'
        
        text += f"ID: {inv_id}\n"
        text += f"User: @{username_display} [{user_id}]\n"
        text += f"Name: {full_name_display}\n"
        text += f"Amount: ${amount:,.2f} ({crypto_display})\n"
        text += f"TX ID: `{tx_id_display}`\n"
        text += f"Date: {date_display}\n"
        if notes:
            text += f"Notes: {notes}\n"
        text += "─────────────────────\n"
        
        keyboard.append([
            InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_investment_{inv_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_investment_{inv_id}")
        ])
    
    if len(pending_investments) > 5:
        text += f"\n... and {len(pending_investments) - 5} more"
    
    keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)

async def show_pending_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending withdrawals"""
    pending_withdrawals = db.get_pending_withdrawals()
    
    logging.info(f"Pending withdrawals count: {len(pending_withdrawals)}")
    
    if not pending_withdrawals:
        text = "✅ No pending withdrawals at the moment."
        keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        return
    
    text = "💸 PENDING WITHDRAWALS\n\n"
    keyboard = []
    
    for wd in pending_withdrawals[:5]:
        logging.info(f"Processing withdrawal: {wd}")
        
        if len(wd) >= 8:
            wd_id, user_id, username, full_name, email, amount, wallet_address, date = wd[:8]
            
            # ✅ VALIDATE ID EXISTS
            if not wd_id:
                logging.error(f"❌ Withdrawal has no ID! Data: {wd}")
                text += f"⚠️ ERROR: Withdrawal for user {user_id} has no ID in database!\n"
                text += "───────────────────\n"
                continue
            
            # Safe handling of None values
            username_display = username or 'N/A'
            full_name_display = full_name or 'N/A'
            wallet_display = (wallet_address or 'N/A')[:20] + '...' if wallet_address else 'N/A'
            date_display = (date or 'N/A')[:16] if date else 'N/A'
            
            text += f"ID: {wd_id}\n"
            text += f"User: @{username_display} [{user_id}]\n"
            text += f"Name: {full_name_display}\n"
            text += f"Amount: ${amount:,.2f}\n"
            text += f"Wallet: `{wallet_display}`\n"
            text += f"Date: {date_display}\n"
            text += "───────────────────\n"
            
            keyboard.append([
                InlineKeyboardButton("✅ Confirm", callback_data=f"admin_confirm_withdrawal_{wd_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_withdrawal_{wd_id}")
            ])
        else:
            logging.error(f"Invalid withdrawal data format: {wd}")
            continue
    
    if len(pending_withdrawals) > 5:
        text += f"\n... and {len(pending_withdrawals) - 5} more"
    
    keyboard.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)
    
async def handle_withdrawal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, withdrawal_id: int):
    """Handle withdrawal confirmation"""
    try:
        logging.info(f"🚀 STARTING WITHDRAWAL CONFIRMATION FOR ID: {withdrawal_id}")
        
        # Update withdrawal status
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # First verify the withdrawal exists and is pending
            logging.info(f"🔍 Checking withdrawal {withdrawal_id} in database...")
            cursor.execute('''
                SELECT user_id, amount, wallet_address, status 
                FROM withdrawals WHERE id = ?
            ''', (withdrawal_id,))
            wd_data = cursor.fetchone()
            
            logging.info(f"📊 Withdrawal data from DB: {wd_data}")
            
            if not wd_data:
                error_msg = f"❌ Withdrawal {withdrawal_id} not found in database."
                logging.error(error_msg)
                await update.callback_query.message.edit_text(error_msg)
                return
                
            user_id, amount, wallet, status = wd_data
            logging.info(f"✅ Found withdrawal: User={user_id}, Amount=${amount}, Status={status}")
            
            if status != 'pending':
                error_msg = f"❌ Withdrawal {withdrawal_id} is already {status}."
                logging.error(error_msg)
                await update.callback_query.message.edit_text(error_msg)
                return
            
            # Update withdrawal status
            logging.info(f"🔄 Updating withdrawal status to 'confirmed'...")
            cursor.execute('''
                UPDATE withdrawals SET status = 'confirmed' WHERE id = ?
            ''', (withdrawal_id,))
            
            # Get user's current balance
            logging.info(f"💰 Getting current balance for user {user_id}...")
            cursor.execute('SELECT current_balance FROM users WHERE user_id = ?', (user_id,))
            balance_result = cursor.fetchone()
            
            logging.info(f"📊 Balance result: {balance_result}")
            
            if not balance_result:
                error_msg = f"❌ User {user_id} not found."
                logging.error(error_msg)
                await update.callback_query.message.edit_text(error_msg)
                return
                
            old_balance = balance_result[0]
            new_balance = old_balance - amount
            logging.info(f"💳 Balance update: ${old_balance} - ${amount} = ${new_balance}")
            
            # Update user balance
            logging.info(f"🔄 Updating user balance...")
            cursor.execute('UPDATE users SET current_balance = ? WHERE user_id = ?', (new_balance, user_id))
            
            # Log the action
            logging.info(f"📝 Logging admin action...")
            log_admin_action(
                admin_id=update.callback_query.from_user.id,
                action_type="withdrawal_confirmation",
                target_user_id=user_id,
                amount=amount,
                old_balance=old_balance,
                new_balance=new_balance,
                notes=f"Withdrawal ID {withdrawal_id} confirmed"
            )
            
            conn.commit()
            logging.info(f"✅ Database changes committed!")
            
            # Notify user
            try:
                logging.info(f"📨 Notifying user {user_id}...")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ WITHDRAWAL CONFIRMED!\n\n"
                         f"💰 Amount: ${amount:,.2f}\n"
                         f"💳 To: `{wallet}`\n\n"
                         f"Funds will be sent to your wallet shortly! 🚀",
                    parse_mode='HTML'
                )
                logging.info(f"✅ User {user_id} notified successfully")
            except Exception as e:
                logging.error(f"❌ Failed to notify user {user_id}: {e}")
        
        success_msg = f"✅ Withdrawal {withdrawal_id} confirmed. User notified and balance updated."
        logging.info(success_msg)
        await update.callback_query.message.edit_text(
            success_msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_withdrawals")]])
        )
        
    except Exception as e:
        error_msg = f"❌ Error confirming withdrawal {withdrawal_id}: {str(e)}"
        logging.error(error_msg, exc_info=True)  # This will log the full traceback
        await update.callback_query.message.edit_text(
            error_msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_withdrawals")]])
        )

async def handle_withdrawal_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, withdrawal_id: int):
    """Handle withdrawal rejection"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE withdrawals SET status = 'rejected' WHERE id = ?
            ''', (withdrawal_id,))
            
            # Get withdrawal details for notification
            cursor.execute('''
                SELECT user_id, amount FROM withdrawals WHERE id = ?
            ''', (withdrawal_id,))
            wd_data = cursor.fetchone()
            
            if wd_data:
                user_id, amount = wd_data
                
                # Log the action
                log_admin_action(
                    admin_id=update.callback_query.from_user.id,
                    action_type="withdrawal_rejection",
                    target_user_id=user_id,
                    amount=amount,
                    notes=f"Withdrawal ID {withdrawal_id} rejected"
                )
                
                conn.commit()
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ WITHDRAWAL REJECTED\n\n"
                             f"💰 Amount: ${amount:,.2f}\n"
                             f"📝 Status: Rejected\n\n"
                             f"Please contact support for more information.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logging.error(f"Failed to notify user {user_id}: {e}")
        
        await update.callback_query.message.edit_text(
            f"❌ Withdrawal {withdrawal_id} rejected. User notified.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_withdrawals")]])
        )
        
    except Exception as e:
        logging.error(f"Error rejecting withdrawal {withdrawal_id}: {e}")
        await update.callback_query.message.edit_text(f"❌ Error rejecting withdrawal: {str(e)}")

async def show_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user management options"""
    keyboard = [
        [InlineKeyboardButton("👤 View All Users", callback_data="admin_user_list"),
         InlineKeyboardButton("🔍 Find User", callback_data="admin_search_user")],
        [InlineKeyboardButton("💳 Edit Balances", callback_data="admin_edit_balance"),
         InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban_user")],
        [InlineKeyboardButton("📊 User Statistics", callback_data="admin_detailed_stats"),
         InlineKeyboardButton("💰 Top Investors", callback_data="admin_top_investors")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
👥 USER MANAGEMENT

Choose an action:

• View All Users - Browse all registered users
• Find User - Search by ID, username, or email
• Edit Balances - Modify user balances
• Ban/Unban User - User access control
• User Statistics - Detailed analytics
• Top Investors - View highest investors
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def show_balance_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show balance editing options"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Balance", callback_data="admin_balance_add"),
         InlineKeyboardButton("➖ Subtract Balance", callback_data="admin_balance_subtract")],
        [InlineKeyboardButton("🎯 Set Balance", callback_data="admin_balance_set"),
         InlineKeyboardButton("🔄 Reset Balance", callback_data="admin_balance_reset")],
        [InlineKeyboardButton("📊 View Balance History", callback_data="admin_balance_history")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
💳 BALANCE MANAGEMENT

Choose an action:

• Add Balance - Add funds to user account
• Subtract Balance - Remove funds from user account
• Set Balance - Set exact balance amount
• Reset Balance - Set balance to zero
• View Balance History - See all balance changes

⚠️ Warning: Balance changes are logged and irreversible.
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    clear_awaiting_states(context)
    
async def setup_user_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup user search"""
    keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
🔍 USER SEARCH

Send me the user information to search for:

Search by:
• User ID (e.g., 123456789)
• Username (e.g., @username or username)
• Email address
• Full name (partial match)

Examples:
- 123456789
- @johnsmith
- john.smith@email.com
- John Smith

Type your search term below:
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    context.user_data['awaiting_user_search'] = True

async def setup_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup broadcast message"""
    keyboard = [[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
📢 BROADCAST MESSAGE

Send me the message you want to broadcast to all users.

⚠️ Important:
• Maximum 2000 characters
• Supports HTML formatting
• Will be sent to all registered users
• Cannot be undone once sent

Example:
```
🚀 New Feature Alert!

Check it out in the Invest menu.

Happy trading! 💰
```

Type your broadcast message below:
    """
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    context.user_data['awaiting_broadcast_message'] = True

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed user statistics"""
    stats = db.get_user_stats()
    
    # Get additional stats
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get registration stats
        cursor.execute('''
            SELECT DATE(registration_date) as date, COUNT(*) as count
            FROM users 
            WHERE registration_date >= date('now', '-7 days')
            GROUP BY DATE(registration_date)
            ORDER BY date DESC
        ''')
        recent_registrations = cursor.fetchall()
        
        # Get investment stats
        cursor.execute('''
            SELECT strategy, COUNT(*) as count, SUM(total_invested) as total
            FROM users 
            WHERE strategy IS NOT NULL 
            GROUP BY strategy
        ''')
        strategy_stats = cursor.fetchall()
    
    text = f"""
📊 DETAILED BOT STATISTICS

👥 User Overview:
• Total Registered Users: {stats.get('total_users', 0):,}
• Active Investors: {stats.get('active_investors', 0):,}
• Inactive Users: {stats.get('total_users', 0) - stats.get('active_investors', 0):,}

💰 Investment Overview:
• Total Crypto Invested: ${stats.get('total_crypto_invested', 0):,.2f}
• Total User Balances: ${stats.get('total_balances', 0):,.2f}

📈 Investment Strategies:
    """
    
    for strategy, count, total in strategy_stats:
        text += f"• {strategy}: {count} users (${total:,.2f})\n"
    
    text += f"""

⏳ Pending Items:
• Pending Investments: {stats.get('pending_investments', 0)}
• Pending Withdrawals: {stats.get('pending_withdrawals', 0)}

📅 Recent Activity (Last 7 days):
    """
    
    for date, count in recent_registrations:
        text += f"• {date}: {count} new users\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_user_stats")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def show_admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent admin activity logs"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT abl.timestamp, abl.admin_id, u1.username as admin_username,
                   abl.target_user_id, u2.username as target_username, abl.action_type,
                   abl.amount, abl.old_balance, abl.new_balance, abl.notes
            FROM admin_balance_logs abl
            LEFT JOIN users u1 ON abl.admin_id = u1.user_id
            LEFT JOIN users u2 ON abl.target_user_id = u2.user_id
            ORDER BY abl.timestamp DESC
            LIMIT 10
        ''')
        logs = cursor.fetchall()
    
    if not logs:
        text = "📋 ADMIN LOGS\n\nNo admin activity logged yet."
    else:
        text = "📋 RECENT ADMIN ACTIVITY\n\n"
        
        for log in logs:
            timestamp, admin_id, admin_username, target_id, target_username, action, amount, old_bal, new_bal, notes = log
            
            text += f"{timestamp[:16]}\n"
            text += f"Admin: @{admin_username or admin_id}\n"
            text += f"Action: {action}\n"
            text += f"Target: @{target_username or target_id}\n"
            if amount:
                text += f"Amount: ${amount:,.2f}\n"
                text += f"Balance: ${old_bal:,.2f} → ${new_bal:,.2f}\n"
            if notes:
                text += f"Notes: {notes}\n"
            text += "─────────────\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_logs")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def handle_admin_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle admin confirmations"""
    parts = data.split("_")
    if len(parts) < 4:
        return
    
    action_type = parts[2]
    item_id = int(parts[3])
    admin_id = update.callback_query.from_user.id
    
    try:
        if action_type == "investment":
            success = db.confirm_investment(item_id, admin_id)
            if success:
                # Get investment details
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT user_id, amount FROM investments WHERE id = ?
                    ''', (item_id,))
                    inv_data = cursor.fetchone()
                    
                    if inv_data:
                        user_id, amount = inv_data
                        
                        # Check if referral bonus was triggered
                        cursor.execute('''
                            SELECT u1.username, u2.username as referrer_username, r.bonus_amount
                            FROM users u1
                            LEFT JOIN referrals r ON u1.user_id = r.referred_id
                            LEFT JOIN users u2 ON r.referrer_id = u2.user_id
                            WHERE u1.user_id = ? AND r.bonus_amount > 0
                        ''', (user_id,))
                        referral_info = cursor.fetchone()
                        
                        # Notify user
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"🎉 INVESTMENT CONFIRMED!\n\n"
                                     f"✅ Your investment of ${amount:,.2f} has been confirmed!\n"
                                     f"💰 Your portfolio has been updated\n"
                                     f"📈 Daily profits are now active\n\n"
                                     f"Check your portfolio to see your updated balance!",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            logging.error(f"Failed to notify user {user_id}: {e}")
                        
                        # Notify referrer if bonus triggered
                        if referral_info and referral_info[2]:
                            username, referrer_username, bonus = referral_info
                            try:
                                cursor.execute('SELECT user_id FROM users WHERE username = ?', (referrer_username,))
                                referrer = cursor.fetchone()
                                if referrer:
                                    await context.bot.send_message(
                                        chat_id=referrer[0],
                                        text=f"🎉 REFERRAL BONUS EARNED!\n\n"
                                             f"💰 Amount: ${bonus:.2f}\n"
                                             f"👤 From: @{username}\n\n"
                                             f"Your referral just made their first investment!\n"
                                             f"The bonus has been added to your balance.\n\n"
                                             f"Keep sharing your referral code to earn more! 🚀",
                                        parse_mode='HTML'
                                    )
                            except Exception as e:
                                logging.error(f"Failed to notify referrer: {e}")
                
                await update.callback_query.message.edit_text(
                    f"✅ Investment {item_id} confirmed successfully.\nUser has been notified.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_investments")]])
                )
            else:
                await update.callback_query.message.edit_text(f"❌ Failed to confirm investment {item_id}.")
        
    
    except Exception as e:
        logging.error(f"Error in admin confirmation: {e}")
        await update.callback_query.message.edit_text(f"❌ Error processing confirmation: {str(e)}")

async def handle_admin_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle admin rejections"""
    parts = data.split("_")
    if len(parts) < 4:
        return
    
    action_type = parts[2]
    item_id = int(parts[3])
    
    # Update status to rejected
    table_map = {
        'investment': 'investments',
        'withdrawal': 'withdrawals', 
    }
    
    table = table_map.get(action_type)
    if table:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE {table} SET status = 'rejected' WHERE id = ?
            ''', (item_id,))
            conn.commit()
    
    await update.callback_query.message.edit_text(
        f"❌ {action_type.title()} {item_id} rejected.",
    )

async def handle_balance_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle balance editing callbacks, supports both global and user-specific actions."""
    parts = data.split("_")
    # Format could be: admin_balance_add or admin_balance_add_<user_id>
    action = parts[2]
    user_id = int(parts[3]) if len(parts) > 3 else None

    if action in ["add", "subtract", "set", "reset"]:
        context.user_data['balance_action'] = action

        if user_id:
            # Directly open the amount prompt for this user
            user_data = db.get_user(user_id)
            if not user_data:
                await update.callback_query.message.edit_text("❌ User not found.")
                return

            context.user_data['balance_target_user'] = user_data
            current_balance = user_data[8]
            username = user_data[1]
            full_name = user_data[3]

            if action == "reset":
                await confirm_balance_change(update, context, 0, "RESET")
            else:
                context.user_data['awaiting_balance_amount'] = True
                keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"admin_user_profile_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                action_text = {
                    "add": "ADD to",
                    "subtract": "SUBTRACT from",
                    "set": "SET as new balance for"
                }

                await update.callback_query.message.edit_text(
                    f"✅ USER FOUND!\n\n"
                    f"💳 {action_text[action]} BALANCE\n\n"
                    f"User: @{username or 'N/A'} ({full_name or 'N/A'})\n"
                    f"ID: {user_id}\n"
                    f"Current Balance: ${current_balance:,.2f}\n\n"
                    f"Enter the amount to {action}:\n\n"
                    f"Examples:\n"
                    f"• 100\n• 500.50\n• 1000\n\n"
                    f"Type the amount below:",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            # Old global workflow
            context.user_data['awaiting_balance_user_id'] = True
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_edit_balance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.message.edit_text(
                f"💳 {action.upper()} BALANCE\n\n"
                f"Send me the User ID to modify:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    elif action == "history":
        await show_balance_history(update, context)

async def handle_balance_user_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id_str: str):
    """Handle user ID input for balance editing"""
    try:
        # Clean the input - remove any extra characters
        cleaned_input = user_id_str.strip().replace('@', '').replace('#', '')
        
        # Try to parse as integer
        user_id = int(cleaned_input)
        
        # Verify user exists
        user_data = db.get_user(user_id)
        if not user_data:
            # Also try searching by username if direct ID fails
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username LIKE ? OR user_id = ?', 
                             (f'%{cleaned_input}%', user_id))
                user_data = cursor.fetchone()
        
        if not user_data:
            keyboard = [
                [InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")],
                [InlineKeyboardButton("🔙 Balance Menu", callback_data="admin_edit_balance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ User with ID '{user_id_str}' not found.\n\n"
                "Tips:\n"
                "• Enter only numbers (e.g., 123456789)\n"
                "• Use Search User to find the correct ID\n"
                "• Check if user is registered with /start\n\n"
                f"Debug Info:\n"
                f"• Input received: '{user_id_str}'\n"
                f"• Parsed as: {user_id}\n"
                f"• Total users in database: {get_total_user_count()}",
                reply_markup=reply_markup
            )
            context.user_data.pop('awaiting_balance_user_id', None)
            return
        
        # Store user data for next step
        context.user_data['balance_target_user'] = user_data
        context.user_data.pop('awaiting_balance_user_id', None)
        
        action = context.user_data.get('balance_action')
        current_balance = user_data[8]  # current_balance field
        username = user_data[1]
        full_name = user_data[3]
        
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
            f"❌ Invalid User ID format: '{user_id_str}'\n\n"
            "Please enter:\n"
            "• Numbers only (e.g., 123456789)\n"
            "• No letters, symbols, or spaces\n\n"
            "Example: 652353552"
        )

def get_total_user_count():
    """Helper function to get total user count"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    except:
        return "unknown"

async def show_balance_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show balance change history"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT abl.timestamp, abl.admin_id, u1.username as admin_username,
                   abl.target_user_id, u2.username as target_username, u2.full_name,
                   abl.action_type, abl.amount, abl.old_balance, abl.new_balance, abl.notes
            FROM admin_balance_logs abl
            LEFT JOIN users u1 ON abl.admin_id = u1.user_id
            LEFT JOIN users u2 ON abl.target_user_id = u2.user_id
            WHERE abl.action_type LIKE '%balance%'
            ORDER BY abl.timestamp DESC
            LIMIT 15
        ''')
        history = cursor.fetchall()
    
    if not history:
        text = "📊 BALANCE HISTORY\n\nNo balance modifications found."
    else:
        text = "📊 BALANCE MODIFICATION HISTORY\n\n"
        
        for record in history:
            timestamp, admin_id, admin_username, target_id, target_username, target_name, action, amount, old_bal, new_bal, notes = record
            
            text += f"{timestamp[:16]}\n"
            text += f"Admin: @{admin_username or str(admin_id)}\n"
            text += f"User: @{target_username or str(target_id)} ({target_name or 'N/A'})\n"
            text += f"Action: {action}\n"
            text += f"Amount: ${amount:,.2f}\n"
            text += f"Balance: ${old_bal:,.2f} → ${new_bal:,.2f}\n"
            if notes:
                text += f"Notes: {notes}\n"
            text += "─────────────\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_balance_history")],
        [InlineKeyboardButton("🔙 Balance Menu", callback_data="admin_edit_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')

async def handle_user_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle user management callbacks"""
    action = data.replace("admin_user_", "")
    
    if action == "list":
        await show_user_list(update, context)
    elif action.startswith("profile_"):
        user_id = int(action.replace("profile_", ""))
        await show_user_profile(update, context, user_id)

async def show_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show paginated user list"""
    users_per_page = 5
    offset = page * users_per_page
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, full_name, total_invested, current_balance, registration_date
            FROM users 
            ORDER BY registration_date DESC 
            LIMIT ? OFFSET ?
        ''', (users_per_page, offset))
        users = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
    
    if not users:
        text = "👥 USER LIST\n\nNo users found."
        keyboard = [[InlineKeyboardButton("🔙 User Management", callback_data="admin_user_management")]]
    else:
        # Don't use HTML parse_mode to avoid escaping issues
        text = f"👥 USER LIST - Page {page + 1}\n\n"
        keyboard = []
        
        for user in users:
            user_id, username, full_name, invested, balance, reg_date = user
            
            # Build plain text without HTML formatting
            text += f"ID: {user_id}\n"
            text += f"Username: @{username or 'N/A'}\n"
            text += f"Name: {full_name or 'N/A'}\n"
            text += f"Invested: ${invested:,.2f}\n"
            text += f"Balance: ${balance:,.2f}\n"
            text += f"Joined: {reg_date[:10]}\n"
            text += "─────────────\n"
            
            keyboard.append([InlineKeyboardButton(f"View {username or user_id}", callback_data=f"admin_user_profile_{user_id}")])
        
        # Navigation
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_user_list_{page-1}"))
        if offset + users_per_page < total_users:
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"admin_user_list_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 User Management", callback_data="admin_user_management")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use None for parse_mode to send as plain text
    await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup)
    clear_awaiting_states(context)

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show detailed user profile for admin"""
    user_data = db.get_user(user_id)
    if not user_data:
        keyboard = [[InlineKeyboardButton("🔙 User List", callback_data="admin_user_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(
            "❌ User not found or data is corrupted.",
            reply_markup=reply_markup
        )
        return
    
    try:
        # Safe unpacking of user data - handle variable number of columns
        # Expected columns in order: user_id, username, first_name, full_name, email, registration_date, 
        # strategy, total_invested, current_balance, profit_earned, last_update, referral_code, referred_by, wallet_address
        user_id = user_data[0]
        username = user_data[1] if len(user_data) > 1 else None
        first_name = user_data[2] if len(user_data) > 2 else None
        full_name = user_data[3] if len(user_data) > 3 else None
        email = user_data[4] if len(user_data) > 4 else None
        reg_date = user_data[5] if len(user_data) > 5 else None
        strategy = user_data[6] if len(user_data) > 6 else None  # ✅ Changed from 'plan' to 'strategy'
        total_invested = user_data[7] if len(user_data) > 7 else 0.0
        current_balance = user_data[8] if len(user_data) > 8 else 0.0
        profit_earned = user_data[9] if len(user_data) > 9 else 0.0
        last_update = user_data[10] if len(user_data) > 10 else None
        referral_code = user_data[11] if len(user_data) > 11 else None
        referred_by = user_data[12] if len(user_data) > 12 else None
        wallet_address = user_data[13] if len(user_data) > 13 else None
        
        # Get additional data
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get investment count
            cursor.execute('SELECT COUNT(*) FROM investments WHERE user_id = ? AND status = "confirmed"', (user_id,))
            investment_result = cursor.fetchone()
            investment_count = investment_result[0] if investment_result else 0
            
            # Get referral count
            cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
            referral_result = cursor.fetchone()
            referral_count = referral_result[0] if referral_result else 0
            
            # Get recent activity
            cursor.execute('''
                SELECT 'investment' as type, amount, investment_date as date FROM investments 
                WHERE user_id = ? AND status = 'confirmed'
                UNION ALL
                SELECT 'withdrawal' as type, amount, withdrawal_date as date FROM withdrawals 
                WHERE user_id = ? AND status = 'confirmed'
                ORDER BY date DESC LIMIT 5
            ''', (user_id, user_id))
            recent_activity = cursor.fetchall() or []
        
        text = f"""
👤 USER PROFILE - {full_name or username or 'Unknown'}

📋 Personal Info:
- ID: {user_id}
- Username: @{username or 'N/A'}
- Full Name: {full_name or 'N/A'}
- Email: {email or 'N/A'}
- Member Since: {reg_date[:10] if reg_date else 'Unknown'}
- Wallet: {wallet_address[:20] + '...' if wallet_address else 'Not set'}

💼 Account Summary:
- Strategy: {strategy or 'No active strategy'}
- Total Invested: ${total_invested:,.2f}
- Current Balance: ${current_balance:,.2f}
- Total Profit: ${profit_earned:,.2f}

📊 Activity Stats:
- Confirmed Investments: {investment_count}
- Referrals Made: {referral_count}
- Referral Code: {referral_code or 'None'}
- Referred By: {referred_by or 'Organic'}

🔄 Recent Activity:
        """
        
        for activity in recent_activity:
            activity_type, amount, date = activity
            text += f"• {activity_type.title()}: ${amount:,.2f} ({date[:10] if date else 'N/A'})\n"
        
        if not recent_activity:
            text += "• No recent activity\n"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit Profile", callback_data=f"admin_edit_profile_{user_id}"),
             InlineKeyboardButton("💳 Edit Balance", callback_data=f"admin_edit_user_balance_{user_id}")],
            [InlineKeyboardButton("💰 Investments", callback_data=f"admin_edit_investments_{user_id}"),
             InlineKeyboardButton("📊 Full History", callback_data=f"admin_user_history_{user_id}")],
            [InlineKeyboardButton("💬 Send Message", callback_data=f"admin_message_user_{user_id}"),
             InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_user_{user_id}")],
            [InlineKeyboardButton("🔙 User List", callback_data="admin_user_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.edit_text(text.strip(), reply_markup=reply_markup, parse_mode='HTML')
    
    except Exception as e:
        logging.error(f"Error displaying user profile {user_id}: {e}")
        logging.error(f"User data structure: {user_data}")
        keyboard = [[InlineKeyboardButton("🔙 User List", callback_data="admin_user_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text(
            f"❌ Error loading user profile: {str(e)}\n\nDebug: User data has {len(user_data)} columns",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

# Command handlers for direct admin commands
async def confirm_investment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to confirm investment"""
    if update.effective_user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("❌ Admin access required.")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /confirm_investment <user_id> <amount>")
        return
    
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        
        # Find the investment to confirm
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM investments 
                WHERE user_id = ? AND amount = ? AND status = 'pending'
                ORDER BY investment_date DESC LIMIT 1
            ''', (user_id, amount))
            result = cursor.fetchone()
            
            if not result:
                await update.message.reply_text(f"❌ No pending investment found for user {user_id} with amount ${amount}")
                return
            
            investment_id = result[0]
        
            success = db.confirm_investment(investment_id, update.effective_user.id)
        
        if success:
            await update.message.reply_text(f"✅ Investment confirmed for user {user_id}: ${amount:,.2f}")
            
            # Notify user (Updated text for strategy)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 INVESTMENT CONFIRMED!\n\n"
                        f"✅ Your investment of ${amount:,.2f} has been confirmed!\n"
                        f"💰 Your portfolio has been updated\n"
                        f"📈 Daily profits are now active with your strategy\n\n"
                        f"Check your portfolio to see your updated balance!",
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.error(f"Failed to notify user {user_id}: {e}")
        else:
            await update.message.reply_text(f"❌ Failed to confirm investment for user {user_id}")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid command format. Use: /confirm_investment <user_id> <amount>")

async def confirm_withdrawal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to confirm withdrawal"""
    if update.effective_user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("❌ Admin access required.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /confirm_withdrawal <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get latest pending withdrawal
            cursor.execute('''
                SELECT id, amount, wallet_address FROM withdrawals 
                WHERE user_id = ? AND status = 'pending' 
                ORDER BY withdrawal_date DESC LIMIT 1
            ''', (user_id,))
            withdrawal = cursor.fetchone()
            
            if not withdrawal:
                await update.message.reply_text(f"❌ No pending withdrawal found for user {user_id}")
                return
            
            withdrawal_id, amount, wallet_address = withdrawal
            
            # Confirm withdrawal
            cursor.execute('''
                UPDATE withdrawals 
                SET status = 'confirmed', processed_by = ? 
                WHERE id = ?
            ''', (update.effective_user.id, withdrawal_id))
            
            # Deduct from user balance
            cursor.execute('''
                SELECT current_balance FROM users WHERE user_id = ?
            ''', (user_id,))
            old_balance = cursor.fetchone()[0]
            new_balance = old_balance - amount
            
            cursor.execute('''
                UPDATE users SET current_balance = ? WHERE user_id = ?
            ''', (new_balance, user_id))
            
            conn.commit()
            
            # Log the action
            log_admin_action(
                admin_id=update.effective_user.id,
                action_type="withdrawal_confirmation",
                target_user_id=user_id,
                amount=amount,
                old_balance=old_balance,
                new_balance=new_balance,
                notes=f"Withdrawal ID {withdrawal_id} confirmed via command"
            )
        
        await update.message.reply_text(f"✅ Withdrawal confirmed for user {user_id}: ${amount:,.2f}")
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ WITHDRAWAL CONFIRMED!\n\n"
                     f"💰 Amount: ${amount:,.2f}\n"
                     f"💳 To: `{wallet_address}`\n"
                     f"⏰ Processing: Within 24 hours\n\n"
                     f"Funds will be sent to your wallet shortly!",
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to notify user {user_id}: {e}")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid command format. Use: /confirm_withdrawal <user_id>")

async def debug_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug function to show all withdrawals"""
    all_withdrawals = db.debug_get_all_withdrawals()
    
    text = "🔧 DEBUG: ALL WITHDRAWALS\n\n"
    for wd in all_withdrawals:
        wd_id, user_id, amount, status, date = wd
        text += f"ID: {wd_id}, User: {user_id}, Amount: ${amount}, Status: {status}, Date: {date}\n"
    
    await update.message.reply_text(text)