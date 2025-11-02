import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.ext.filters import BaseFilter
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import json
from collections import defaultdict


# Configuration
SUPPORT_BOT_TOKEN = "8244283171:AAGKtCbqtcCx-Ly0iPhyqeug4rKBNwZevCU"
SUPPORT_ADMIN_IDS = [6417609151]

# Enhanced ticket storage with dataclass
@dataclass
class SupportTicket:
    user_id: int
    username: Optional[str]
    first_name: str
    start_time: datetime
    message_count: int = 0
    urgent: bool = False
    notified: bool = False
    last_message: Optional[datetime] = None
    category: Optional[str] = None
    status: str = "open"  # open, waiting_response, resolved
    assigned_admin: Optional[int] = None
    notes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

# Storage
active_tickets: Dict[int, SupportTicket] = {}
admin_reply_sessions: Dict[int, int] = {}
ticket_history: List[Dict] = []  # Store closed tickets
admin_stats = defaultdict(lambda: {"resolved": 0, "total_messages": 0})

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdminFilter(BaseFilter):
    def filter(self, message):
        if message.from_user:
            return message.from_user.id in SUPPORT_ADMIN_IDS
        return False

# Ticket categories
CATEGORIES = {
    "account": "👤 Account Issues",
    "investment": "💰 Investment Questions",
    "withdrawal": "💸 Withdrawal Problems",
    "technical": "🔧 Technical Support",
    "referral": "🤝 Referral System",
    "other": "❓ Other Issues"
}

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with better UI"""
    user = update.effective_user
    
    if user.id in SUPPORT_ADMIN_IDS:
        await show_admin_dashboard(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("💬 New Support Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("📊 My Active Tickets", callback_data="my_tickets")],
            [InlineKeyboardButton("❓ FAQ & Help Center", callback_data="support_faq")],
            [InlineKeyboardButton("📞 Urgent Priority Support", callback_data="urgent_help")],
            [InlineKeyboardButton("🔗 Return to Main Bot", url="https://t.me/Quanttradeai_bot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🎯 <b>𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 Support Center</b>

Hello {user.first_name}! 👋

<b>We're here to help you 24/7 with:</b>
✅ Account & Security Issues
✅ Investment & Trading Support
✅ Withdrawals & Payments
✅ Technical Problems
✅ General Inquiries

<i>Average Response Time: &lt; 5 minutes</i>

Choose an option below to get started! 👇
        """
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                welcome_text.strip(), 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                welcome_text.strip(), 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )

async def create_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category selection for new ticket"""
    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"category_{key}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="support_main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
🎫 <b>Create New Support Ticket</b>

Please select the category that best describes your issue:

This helps us route your request to the right specialist! 🎯
    """
    
    await update.callback_query.message.edit_text(
        text.strip(), 
        reply_markup=reply_markup, 
        parse_mode='HTML'
    )

async def start_ticket_with_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Start a support conversation with selected category"""
    user = update.callback_query.from_user
    
    ticket = SupportTicket(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        start_time=datetime.now(),
        category=category
    )
    active_tickets[user.id] = ticket
    
    logger.info(f"Ticket created for user {user.id}. Active tickets: {len(active_tickets)}")
    logger.info(f"Admin IDs configured: {SUPPORT_ADMIN_IDS}")
    
    # Notify admins that a new ticket was created
    for admin_id in SUPPORT_ADMIN_IDS:
        try:
            logger.info(f"Attempting to notify admin {admin_id}")
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🎫 <b>NEW TICKET CREATED</b>\n\n"
                     f"<b>User Information:</b>\n"
                     f"• Name: {user.first_name}\n"
                     f"• Username: @{user.username or 'N/A'}\n"
                     f"• ID: <code>{user.id}</code>\n"
                     f"• Category: {CATEGORIES.get(category, 'N/A')}\n"
                     f"• Time: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                     f"<i>Waiting for user's first message...</i>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👁️ View Ticket", callback_data=f"admin_view_{user.id}"),
                    InlineKeyboardButton("💬 Reply", callback_data=f"admin_reply_{user.id}")
                ]]),
                parse_mode='HTML'
            )
            logger.info(f"Successfully notified admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}", exc_info=True)
    
    keyboard = [
        [InlineKeyboardButton("⚠️ Mark as Urgent", callback_data="mark_urgent")],
        [InlineKeyboardButton("❌ Close Ticket", callback_data="end_conversation")],
        [InlineKeyboardButton("🔗 Main Bot", url="https://t.me/Quanttradeai_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    category_name = CATEGORIES.get(category, "General Support")
    
    await update.callback_query.message.edit_text(
        f"🎫 <b>Support Ticket Created</b>\n\n"
        f"📋 Category: {category_name}\n"
        f"🆔 Ticket ID: #{user.id}\n"
        f"⏰ Created: {datetime.now().strftime('%H:%M')}\n\n"
        f"<b>Please describe your issue in detail:</b>\n"
        f"The more information you provide, the faster we can help! 🚀\n\n"

        f"⚠️Note: after issue is resolved close the ticket!\n\n"
        f"<i>Type your message below...</i>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced admin dashboard with statistics"""
    if update.callback_query:
        user = update.callback_query.from_user
    else:
        user = update.effective_user
    
    if user.id not in SUPPORT_ADMIN_IDS:
        return
    
    # Calculate stats
    total_tickets = len(active_tickets)
    urgent_tickets = sum(1 for t in active_tickets.values() if t.urgent)
    unassigned = sum(1 for t in active_tickets.values() if not t.assigned_admin)
    
    # Sort by urgency and time
    sorted_tickets = sorted(
        active_tickets.items(),
        key=lambda x: (not x[1].urgent, x[1].start_time)
    )
    
    keyboard = []
    for user_id, ticket in sorted_tickets:
        urgency = "🚨" if ticket.urgent else "💬"
        assigned = "✅" if ticket.assigned_admin else "⚪"
        category_emoji = {
            "account": "👤", "investment": "💰", "withdrawal": "💸",
            "technical": "🔧", "referral": "🤝", "other": "❓"
        }.get(ticket.category, "💬")
        
        btn_text = f"{urgency}{assigned} @{ticket.username or 'N/A'} - {category_emoji} {ticket.message_count}msg"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_view_{user_id}")])
    
    keyboard.extend([
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
        ],
        [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
    ])
    
    text = f"""
📊 <b>ADMIN SUPPORT DASHBOARD</b>

<b>📈 Overview:</b>
• Active Tickets: {total_tickets}
• 🚨 Urgent: {urgent_tickets}
• ⚪ Unassigned: {unassigned}
• 👥 Total Admins: {len(SUPPORT_ADMIN_IDS)}

<b>🎫 Active Tickets:</b>
{f"Select a ticket below to view details" if total_tickets > 0 else "✅ No active tickets - All clear!"}
    """
    
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

async def show_ticket_details(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show detailed ticket information to admin"""
    ticket = active_tickets.get(user_id)
    if not ticket:
        await update.callback_query.answer("Ticket not found!", show_alert=True)
        return
    
    duration = datetime.now() - ticket.start_time
    duration_str = str(duration).split('.')[0]
    
    assigned_name = "Unassigned"
    if ticket.assigned_admin:
        assigned_name = f"Admin {ticket.assigned_admin}"
    
    text = f"""
🎫 <b>Ticket Details</b>

<b>User Information:</b>
• Name: {ticket.first_name}
• Username: @{ticket.username or 'N/A'}
• User ID: <code>{ticket.user_id}</code>

<b>Ticket Information:</b>
• Category: {CATEGORIES.get(ticket.category, 'N/A')}
• Status: {ticket.status.upper()}
• Priority: {"🚨 URGENT" if ticket.urgent else "📩 Normal"}
• Assigned to: {assigned_name}
• Messages: {ticket.message_count}

<b>Timeline:</b>
• Created: {ticket.start_time.strftime('%H:%M %d/%m/%Y')}
• Duration: {duration_str}
• Last Message: {ticket.last_message.strftime('%H:%M') if ticket.last_message else 'N/A'}

<b>Notes:</b> {len(ticket.notes)} notes added
    """
    
    keyboard = [
        [
            InlineKeyboardButton("💬 Reply", callback_data=f"admin_reply_{user_id}"),
            InlineKeyboardButton("✅ Assign to Me", callback_data=f"admin_assign_{user_id}")
        ],
        [
            InlineKeyboardButton("📝 Add Note", callback_data=f"admin_note_{user_id}"),
            InlineKeyboardButton("🏷️ Add Tag", callback_data=f"admin_tag_{user_id}")
        ],
        [
            InlineKeyboardButton("✔️ Resolve", callback_data=f"admin_resolve_{user_id}"),
            InlineKeyboardButton("❌ Close", callback_data=f"admin_end_{user_id}")
        ],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="support_main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_my_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's active tickets"""
    user = update.callback_query.from_user
    
    ticket = active_tickets.get(user.id)
    
    if not ticket:
        text = """
📋 <b>My Tickets</b>

You don't have any active support tickets.

Need help? Create a new ticket below! 👇
        """
        keyboard = [
            [InlineKeyboardButton("💬 New Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")]
        ]
    else:
        duration = datetime.now() - ticket.start_time
        status_emoji = {"open": "🟢", "waiting_response": "🟡", "resolved": "✅"}
        
        text = f"""
📋 <b>My Active Ticket</b>

<b>Ticket #</b>{ticket.user_id}
<b>Category:</b> {CATEGORIES.get(ticket.category, 'N/A')}
<b>Status:</b> {status_emoji.get(ticket.status, '⚪')} {ticket.status.upper()}
<b>Priority:</b> {"🚨 Urgent" if ticket.urgent else "📩 Normal"}
<b>Messages:</b> {ticket.message_count}
<b>Duration:</b> {str(duration).split('.')[0]}

<i>We're working on your request!</i>
        """
        keyboard = [
            [InlineKeyboardButton("💬 Send Message", callback_data="start_conversation")],
            [InlineKeyboardButton("❌ Close Ticket", callback_data="end_conversation")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin statistics"""
    total_resolved = sum(stats["resolved"] for stats in admin_stats.values())
    total_history = len(ticket_history)
    
    # Calculate average resolution time
    total_seconds = 0
    valid_tickets = 0
    for ticket in ticket_history:
        if 'end_time' in ticket and 'start_time' in ticket:
            duration = (ticket['end_time'] - ticket['start_time']).total_seconds()
            total_seconds += duration
            valid_tickets += 1
    
    avg_resolution = (total_seconds / max(valid_tickets, 1)) / 60  # Convert to minutes
    
    text = f"""
📊 <b>Support Statistics</b>

<b>Overall Performance:</b>
• Total Resolved: {total_resolved}
• Tickets in History: {total_history}
• Avg. Resolution Time: {avg_resolution:.1f} min
• Active Now: {len(active_tickets)}

<b>Active Tickets by Category:</b>
"""
    
    category_counts = defaultdict(int)
    for ticket in active_tickets.values():
        category_counts[ticket.category] += 1
    
    if category_counts:
        for cat, count in category_counts.items():
            text += f"• {CATEGORIES.get(cat, cat)}: {count}\n"
    else:
        text += "• No active tickets\n"
    
    text += "\n<b>Admin Performance:</b>\n"
    if admin_stats:
        for admin_id, stats in admin_stats.items():
            text += f"• Admin {admin_id}: {stats['resolved']} resolved, {stats['total_messages']} msgs sent\n"
    else:
        text += "• No admin activity yet\n"
    
    # Today's statistics
    today = datetime.now().date()
    today_tickets = [t for t in ticket_history if t.get('end_time', datetime.now()).date() == today]
    text += f"\n<b>Today's Activity:</b>\n• Tickets Closed: {len(today_tickets)}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Dashboard", callback_data="support_main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin settings menu"""
    text = """
⚙️ <b>ADMIN SETTINGS</b>

<b>Bot Configuration:</b>
• Auto-close: ✅ Enabled (24h)
• Daily Reports: ✅ Enabled (23:00)
• Admin Count: {admin_count}

<b>Notification Settings:</b>
• New Tickets: ✅ Enabled
• Urgent Alerts: ✅ Enabled
• User Messages: ✅ Enabled

<b>Statistics:</b>
• Total Tickets Today: {today_count}
• Active Tickets: {active_count}
• Tickets in History: {history_count}

<i>More settings coming soon!</i>
    """.format(
        admin_count=len(SUPPORT_ADMIN_IDS),
        today_count=len([t for t in ticket_history if t.get('end_time', datetime.now()).date() == datetime.now().date()]),
        active_count=len(active_tickets),
        history_count=len(ticket_history)
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🗑️ Clear History", callback_data="admin_clear_history"),
            InlineKeyboardButton("📊 Export Stats", callback_data="admin_export_stats")
        ],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="support_main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def clear_ticket_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear ticket history"""
    global ticket_history
    count = len(ticket_history)
    ticket_history = []
    
    await update.callback_query.answer(f"✅ Cleared {count} tickets from history!", show_alert=True)
    await show_admin_settings(update, context)

async def export_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export statistics as a message"""
    stats_text = """
📊 <b>EXPORTED STATISTICS</b>

<b>Current Status:</b>
• Active Tickets: {active}
• Total History: {history}

<b>Category Breakdown:</b>
""".format(active=len(active_tickets), history=len(ticket_history))
    
    category_counts = defaultdict(int)
    for ticket in list(active_tickets.values()) + ticket_history:
        cat = ticket.category if isinstance(ticket, SupportTicket) else ticket.get('category', 'other')
        category_counts[cat] += 1
    
    for cat, count in category_counts.items():
        stats_text += f"• {CATEGORIES.get(cat, cat)}: {count}\n"
    
    stats_text += """
<b>Admin Performance:</b>
"""
    for admin_id, stats in admin_stats.items():
        stats_text += f"• Admin {admin_id}: {stats['resolved']} resolved, {stats['total_messages']} msgs\n"
    
    stats_text += f"\n<i>Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    
    await update.callback_query.answer("✅ Statistics exported!", show_alert=True)
    await update.callback_query.message.reply_text(
        stats_text.strip(),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Settings", callback_data="admin_settings")
        ]])
    )
    """Show admin statistics"""
    total_resolved = sum(stats["resolved"] for stats in admin_stats.values())
    total_history = len(ticket_history)
    avg_resolution = sum((t.get('end_time', datetime.now()) - t.get('start_time', datetime.now())).seconds 
                          for t in ticket_history) / max(len(ticket_history), 1) / 60
    
    text = f"""
📊 <b>Support Statistics</b>

<b>Overall:</b>
• Total Resolved: {total_resolved}
• Tickets in History: {total_history}
• Avg. Resolution Time: {avg_resolution:.1f} min
• Active Now: {len(active_tickets)}

<b>By Category:</b>
"""
    
    category_counts = defaultdict(int)
    for ticket in active_tickets.values():
        category_counts[ticket.category] += 1
    
    for cat, count in category_counts.items():
        text += f"• {CATEGORIES.get(cat, cat)}: {count}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Dashboard", callback_data="support_main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        text.strip(),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced callback handler"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user

    try:
        if data == "create_ticket":
            await create_ticket(update, context)
        elif data.startswith("category_"):
            category = data.split("_")[1]
            await start_ticket_with_category(update, context, category)
        elif data == "start_conversation":
            if user.id in active_tickets:
                # User already has a ticket, just acknowledge
                keyboard = [
                    [InlineKeyboardButton("❌ Close Ticket", callback_data="end_conversation")],
                    [InlineKeyboardButton("🔗 Main Bot", url="https://t.me/Quanttradeai_bot")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    "💬 <b>Your ticket is active!</b>\n\n"
                    "You can send messages now and our support team will respond.\n\n"
                    "Type your message below... 👇",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await create_ticket(update, context)
        elif data == "my_tickets":
            await show_my_tickets(update, context)
        elif data == "mark_urgent":
            if user.id in active_tickets:
                ticket = active_tickets[user.id]
                ticket.urgent = True
                
                # Notify all admins about urgent flag
                for admin_id in SUPPORT_ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=f"🚨🚨🚨 <b>TICKET MARKED URGENT</b> 🚨🚨🚨\n\n"
                                 f"User: @{user.username or 'N/A'} ({user.first_name})\n"
                                 f"ID: <code>{user.id}</code>\n"
                                 f"Category: {CATEGORIES.get(ticket.category, 'N/A')}\n\n"
                                 f"<b>This ticket now requires URGENT attention!</b>",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("👁️ View Ticket", callback_data=f"admin_view_{user.id}"),
                                InlineKeyboardButton("💬 Reply Now", callback_data=f"admin_reply_{user.id}")
                            ]]),
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin_id}: {e}")
                
                await query.answer("🚨 Ticket marked as URGENT! Priority support activated.", show_alert=True)
                
                # Update the message
                keyboard = [
                    [InlineKeyboardButton("❌ Close Ticket", callback_data="end_conversation")],
                    [InlineKeyboardButton("🔗 Main Bot", url="https://t.me/Quanttradeai_bot")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.edit_text(
                    f"🚨 <b>URGENT SUPPORT TICKET</b>\n\n"
                    f"📋 Category: {CATEGORIES.get(ticket.category, 'N/A')}\n"
                    f"🆔 Ticket ID: #{user.id}\n"
                    f"⏰ Created: {ticket.start_time.strftime('%H:%M')}\n\n"
                    f"<b>Your ticket is now marked as URGENT!</b>\n"
                    f"Our team has been notified and will prioritize your request.\n\n"
                    f"<i>You can continue sending messages below.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.answer("No active ticket found!", show_alert=True)
        elif data == "support_faq":
            await show_support_faq(update, context)
        elif data == "urgent_help":
            await urgent_help(update, context)
        elif data == "end_conversation":
            await end_support_conversation(update, context)
        elif data.startswith("admin_view_"):
            user_id = int(data.split("_")[2])
            await show_ticket_details(update, context, user_id)
        elif data.startswith("admin_reply_"):
            user_id = int(data.split("_")[2])
            await setup_admin_reply(update, context, user_id)
        elif data.startswith("admin_assign_"):
            user_id = int(data.split("_")[2])
            await assign_ticket(update, context, user_id)
        elif data.startswith("admin_resolve_"):
            user_id = int(data.split("_")[2])
            await resolve_ticket(update, context, user_id)
        elif data.startswith("admin_end_"):
            user_id = int(data.split("_")[2])
            await admin_end_conversation(update, context, user_id)
        elif data == "admin_cancel_reply":
            await cancel_admin_reply(update, context)
        elif data == "admin_stats":
            await show_admin_stats(update, context)
        elif data == "admin_settings":
            await show_admin_settings(update, context)
        elif data == "admin_clear_history":
            await clear_ticket_history(update, context)
        elif data == "admin_export_stats":
            await export_stats(update, context)
        elif data == "support_main_menu":
            await support_start(update, context)
        elif data == "admin_refresh":
            await show_admin_dashboard(update, context)
            
    except Exception as e:
        logger.error(f"Error in support callback: {e}")
        await query.message.edit_text("❌ An error occurred. Please try again.")

async def assign_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Assign ticket to admin"""
    admin = update.callback_query.from_user
    ticket = active_tickets.get(user_id)
    
    if ticket:
        ticket.assigned_admin = admin.id
        await update.callback_query.answer(f"✅ Ticket assigned to you!", show_alert=True)
        await show_ticket_details(update, context, user_id)

async def resolve_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Mark ticket as resolved"""
    ticket = active_tickets.get(user_id)
    admin = update.callback_query.from_user
    
    if ticket:
        ticket.status = "resolved"
        admin_stats[admin.id]["resolved"] += 1
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ <b>Ticket Resolved</b>\n\n"
                     "Your support ticket has been marked as resolved.\n\n"
                     "If you need further assistance, feel free to create a new ticket!\n\n"
                     "Thank you for using CoreX Support! 🚀",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        
        await update.callback_query.answer("✅ Ticket marked as resolved!", show_alert=True)
        await show_ticket_details(update, context, user_id)

async def show_support_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced FAQ"""
    faq_text = """
❓ <b>FAQ - Frequently Asked Questions</b>

<b>🤖 Getting Started</b>
• Use /start in the main bot
• Complete registration
• Choose investment strategy
• Send crypto payment

<b>💸 Withdrawals</b>
• Processing: 24-48 hours
• Network: TRC20 USDT only
• Minimum: $10
• Fee: Network fees apply

<b>📈 Investments</b>
• Admin confirmation: Up to 24h
• Check transaction ID
• Contact us if pending &gt; 24h

<b>🔐 Security</b>
• Enterprise-grade encryption
• Funds are protected
• Regular security audits
• 2FA recommended

<b>💰 Referrals</b>
• Share your code
• Earn 5% of referrals
• Instant bonus credit
• Unlimited referrals

<b>Need more help?</b>
Create a support ticket below! 👇
    """
    
    keyboard = [
        [InlineKeyboardButton("💬 Create Ticket", callback_data="create_ticket")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        faq_text.strip(), 
        reply_markup=reply_markup, 
        parse_mode='HTML'
    )

async def urgent_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle urgent help with priority"""
    user = update.callback_query.from_user
    
    ticket = SupportTicket(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        start_time=datetime.now(),
        urgent=True,
        category="urgent"
    )
    active_tickets[user.id] = ticket
    
    logger.info(f"URGENT ticket created for user {user.id}. Active tickets: {len(active_tickets)}")
    
    # Immediately notify all admins about urgent ticket
    for admin_id in SUPPORT_ADMIN_IDS:
        try:
            logger.info(f"Sending URGENT notification to admin {admin_id}")
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🚨🚨🚨 <b>URGENT PRIORITY TICKET CREATED</b> 🚨🚨🚨\n\n"
                     f"<b>User Information:</b>\n"
                     f"• Name: {user.first_name}\n"
                     f"• Username: @{user.username or 'N/A'}\n"
                     f"• ID: <code>{user.id}</code>\n"
                     f"• Category: URGENT\n"
                     f"• Time: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                     f"<b>⚠️ User is waiting for urgent assistance!</b>\n"
                     f"<i>Waiting for user's first message...</i>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👁️ View Ticket", callback_data=f"admin_view_{user.id}"),
                    InlineKeyboardButton("💬 Reply Now", callback_data=f"admin_reply_{user.id}")
                ]]),
                parse_mode='HTML'
            )
            logger.info(f"URGENT notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}", exc_info=True)
    
    keyboard = [
        [InlineKeyboardButton("❌ Close Ticket", callback_data="end_conversation")],
        [InlineKeyboardButton("🔗 Main Bot", url="https://t.me/Quanttradeai_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        "🚨 <b>URGENT PRIORITY SUPPORT</b>\n\n"
        "⚡ Your request has been flagged as URGENT\n"
        "👥 All support admins have been notified\n"
        "⏱️ Expected response: &lt; 2 minutes\n\n"
        f"🆔 Ticket ID: #{user.id}\n"
        f"⏰ Created: {datetime.now().strftime('%H:%M')}\n\n"
        "<b>Please describe your urgent issue:</b>\n"
        "Type your message below and we'll respond immediately! 🚀",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handler with better notifications"""
    user = update.effective_user
    message_text = update.message.text
    
    if user.id in active_tickets:
        ticket = active_tickets[user.id]
        
        # First message notification
        if ticket.message_count == 0 and not ticket.notified:
            urgency_tag = "🚨🚨🚨 URGENT SUPPORT REQUEST 🚨🚨🚨" if ticket.urgent else "🎫 NEW SUPPORT TICKET"
            
            for admin_id in SUPPORT_ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"{urgency_tag}\n\n"
                             f"<b>User Information:</b>\n"
                             f"• Name: {user.first_name}\n"
                             f"• Username: @{user.username or 'N/A'}\n"
                             f"• ID: <code>{user.id}</code>\n"
                             f"• Category: {CATEGORIES.get(ticket.category, 'N/A')}\n"
                             f"• Time: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                             f"<b>Message:</b>\n{message_text}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("👁️ View Details", callback_data=f"admin_view_{user.id}"),
                            InlineKeyboardButton("💬 Reply Now", callback_data=f"admin_reply_{user.id}")
                        ]]),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            ticket.notified = True
        else:
            # Subsequent messages
            for admin_id in SUPPORT_ADMIN_IDS:
                try:
                    urgency = "🚨" if ticket.urgent else "💬"
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"{urgency} <b>Message from User</b>\n\n"
                             f"User: @{user.username or user.first_name}\n"
                             f"ID: <code>{user.id}</code>\n"
                             f"Message #{ticket.message_count + 1}\n\n"
                             f"{message_text}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("💬 Reply", callback_data=f"admin_reply_{user.id}")
                        ]]),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Failed to forward to admin {admin_id}: {e}")
        
        ticket.message_count += 1
        ticket.last_message = datetime.now()
        ticket.status = "waiting_response"
        
    else:
        keyboard = [
            [InlineKeyboardButton("💬 Create Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("❓ FAQ", callback_data="support_faq")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        

async def setup_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
    """Setup admin reply session"""
    admin = update.callback_query.from_user
    admin_reply_sessions[admin.id] = target_user_id
    
    ticket = active_tickets.get(target_user_id)
    if not ticket:
        await update.callback_query.answer("Ticket not found!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel_reply")],
        [InlineKeyboardButton("🔙 Back to Ticket", callback_data=f"admin_view_{target_user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        f"💬 <b>REPLY MODE ACTIVE</b>\n\n"
        f"<b>Replying to:</b>\n"
        f"• User: @{ticket.username or 'N/A'} ({ticket.first_name})\n"
        f"• ID: <code>{target_user_id}</code>\n"
        f"• Category: {CATEGORIES.get(ticket.category, 'N/A')}\n\n"
        f"<b>Type your message below:</b>\n"
        f"Your reply will be sent directly to the user.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_admin_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin replies to users"""
    admin = update.effective_user
    message_text = update.message.text
    
    if admin.id in admin_reply_sessions:
        target_user_id = admin_reply_sessions[admin.id]
        ticket = active_tickets.get(target_user_id)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 <b>Support Team Response</b>\n\n"
                     f"{message_text}\n\n"
                     f"━━━━━━━━━━━━━━━\n"
                     f"<i>𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲 Support Team</i>",
                parse_mode='HTML'
            )
            
            if ticket:
                ticket.status = "open"
                admin_stats[admin.id]["total_messages"] += 1
            
            await update.message.reply_text(
                f"✅ <b>Message Delivered!</b>\n\n"
                f"Your reply has been sent to user {target_user_id}.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👁️ View Ticket", callback_data=f"admin_view_{target_user_id}"),
                    InlineKeyboardButton("📊 Dashboard", callback_data="support_main_menu")
                ]]),
                parse_mode='HTML'
            )
            
            logger.info(f"Admin {admin.id} replied to user {target_user_id}")
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Delivery Failed</b>\n\n"
                f"Could not send message: {str(e)}\n"
                f"User may have blocked the bot.",
                parse_mode='HTML'
            )
            logger.error(f"Failed to send admin reply: {e}")
        
        admin_reply_sessions.pop(admin.id, None)
        

async def cancel_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin reply session"""
    admin = update.callback_query.from_user
    admin_reply_sessions.pop(admin.id, None)
    
    await update.callback_query.message.edit_text(
        "❌ Reply session cancelled.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Dashboard", callback_data="support_main_menu")
        ]])
    )

async def admin_end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
    """End conversation from admin side"""
    admin = update.callback_query.from_user
    ticket = active_tickets.get(target_user_id)
    
    if ticket:
        # Save to history
        ticket_data = {
            'user_id': target_user_id,
            'username': ticket.username,
            'first_name': ticket.first_name,
            'category': ticket.category,
            'start_time': ticket.start_time,
            'end_time': datetime.now(),
            'message_count': ticket.message_count,
            'urgent': ticket.urgent,
            'resolved_by': admin.id
        }
        ticket_history.append(ticket_data)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="✅ <b>Support Ticket Closed</b>\n\n"
                     "Your support conversation has been closed by our team.\n\n"
                     "We hope we were able to help! 🎉\n\n"
                     "If you need further assistance, feel free to create a new ticket anytime.\n\n"
                     "<i>Thank you for using CoreX Support!</i>",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        # Notify other admins
        for other_admin_id in SUPPORT_ADMIN_IDS:
            if other_admin_id != admin.id:
                try:
                    await context.bot.send_message(
                        chat_id=other_admin_id,
                        text=f"✅ <b>Ticket Closed</b>\n\n"
                             f"Admin @{admin.username or admin.first_name} closed ticket #{target_user_id}\n"
                             f"User: @{ticket.username or 'N/A'}\n"
                             f"Duration: {ticket.message_count} messages",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {other_admin_id}: {e}")
        
        del active_tickets[target_user_id]
    
    # Clean up reply session
    admin_reply_sessions.pop(admin.id, None)
    
    await update.callback_query.message.edit_text(
        "✅ <b>Ticket Closed Successfully</b>\n\n"
        "The conversation has been ended and the user has been notified.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Dashboard", callback_data="support_main_menu")
        ]]),
        parse_mode='HTML'
    )

async def end_support_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End support conversation (user side)"""
    user = update.callback_query.from_user if update.callback_query else update.effective_user
    ticket = active_tickets.get(user.id)
    
    if ticket:
        # Save to history
        ticket_data = {
            'user_id': user.id,
            'username': ticket.username,
            'first_name': ticket.first_name,
            'category': ticket.category,
            'start_time': ticket.start_time,
            'end_time': datetime.now(),
            'message_count': ticket.message_count,
            'urgent': ticket.urgent,
            'closed_by_user': True
        }
        ticket_history.append(ticket_data)
        
        # Notify admins
        for admin_id in SUPPORT_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"❌ <b>Ticket Closed by User</b>\n\n"
                         f"User: @{user.username or 'N/A'} ({user.first_name})\n"
                         f"ID: <code>{user.id}</code>\n"
                         f"Messages: {ticket.message_count}\n"
                         f"Category: {CATEGORIES.get(ticket.category, 'N/A')}",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        del active_tickets[user.id]
    
    text = """
✅ <b>Support Ticket Closed</b>

Thank you for contacting CoreX Support! 🎉

We hope we were able to help you today.

<i>Your feedback helps us improve!</i>

Need help again? Create a new ticket anytime! 👇
    """
    
    keyboard = [
        [InlineKeyboardButton("💬 New Ticket", callback_data="create_ticket")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")],
        [InlineKeyboardButton("🔗 Main Bot", url="https://t.me/Quanttradeai_bot")]
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

async def handle_end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /end command for both users and admins"""
    user = update.effective_user
    
    if user.id in SUPPORT_ADMIN_IDS:
        if user.id in admin_reply_sessions:
            target_user_id = admin_reply_sessions[user.id]
            # Create a mock update for the callback
            query = type('obj', (object,), {
                'message': update.message,
                'from_user': user
            })()
            mock_update = type('obj', (object,), {
                'callback_query': query,
                'effective_user': user
            })()
            await admin_end_conversation(mock_update, context, target_user_id)
        else:
            await update.message.reply_text(
                "You are not in a reply session. Use the dashboard to manage tickets.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", callback_data="support_main_menu")
                ]])
            )
    else:
        # Create a mock update for user
        query = type('obj', (object,), {
            'message': update.message,
            'from_user': user
        })()
        mock_update = type('obj', (object,), {
            'callback_query': query,
            'effective_user': user
        })()
        await end_support_conversation(mock_update, context)

async def auto_close_inactive_tickets(context: ContextTypes.DEFAULT_TYPE):
    """Auto-close tickets that have been inactive for too long"""
    current_time = datetime.now()
    inactive_timeout = timedelta(hours=24)  # Close after 24 hours of inactivity
    
    to_close = []
    for user_id, ticket in active_tickets.items():
        last_activity = ticket.last_message or ticket.start_time
        if current_time - last_activity > inactive_timeout:
            to_close.append(user_id)
    
    for user_id in to_close:
        ticket = active_tickets[user_id]
        
        # Save to history
        ticket_data = {
            'user_id': user_id,
            'username': ticket.username,
            'first_name': ticket.first_name,
            'category': ticket.category,
            'start_time': ticket.start_time,
            'end_time': current_time,
            'message_count': ticket.message_count,
            'urgent': ticket.urgent,
            'auto_closed': True
        }
        ticket_history.append(ticket_data)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="⏰ <b>Ticket Auto-Closed</b>\n\n"
                     "Your support ticket has been automatically closed due to inactivity.\n\n"
                     "If you still need help, please create a new ticket!\n\n"
                     "<i>𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲  Support Team</i>",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about auto-close: {e}")
        
        # Notify admins
        for admin_id in SUPPORT_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⏰ <b>Ticket Auto-Closed</b>\n\n"
                         f"User: @{ticket.username or 'N/A'}\n"
                         f"ID: {user_id}\n"
                         f"Reason: 24h inactivity",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        del active_tickets[user_id]
        logger.info(f"Auto-closed inactive ticket for user {user_id}")

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily statistics report to admins"""
    today = datetime.now().date()
    tickets_today = [t for t in ticket_history if t.get('end_time', datetime.now()).date() == today]
    
    total_today = len(tickets_today)
    urgent_today = sum(1 for t in tickets_today if t.get('urgent', False))
    avg_messages = sum(t.get('message_count', 0) for t in tickets_today) / max(total_today, 1)
    
    category_breakdown = defaultdict(int)
    for ticket in tickets_today:
        category_breakdown[ticket.get('category', 'other')] += 1
    
    report = f"""
📊 <b>Daily Support Report</b>
📅 Date: {today.strftime('%d/%m/%Y')}

<b>Overview:</b>
• Total Tickets: {total_today}
• Urgent Tickets: {urgent_today}
• Active Now: {len(active_tickets)}
• Avg Messages/Ticket: {avg_messages:.1f}

<b>By Category:</b>
"""
    
    for cat, count in category_breakdown.items():
        report += f"• {CATEGORIES.get(cat, cat)}: {count}\n"
    
    report += f"\n<b>Admin Performance:</b>\n"
    for admin_id, stats in admin_stats.items():
        report += f"• Admin {admin_id}: {stats['resolved']} resolved\n"
    
    # Send to all admins
    for admin_id in SUPPORT_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=report.strip(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send daily report to admin {admin_id}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the support bot"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    try:
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again or contact an administrator.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="support_main_menu")
                ]])
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

def main():
    """Start the enhanced support bot"""

    try:
        from health_server import start_health_server
        start_health_server()
        logger.info("Health check server started for Render")
    except Exception as e:
        logger.warning(f"Could not start health server: {e}")
    # Create custom request with timeout settings
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    
    if not SUPPORT_BOT_TOKEN:
        print("❌ Error: SUPPORT_BOT_TOKEN is not set!")
        return
    
    if not SUPPORT_ADMIN_IDS:
        print("⚠️  Warning: SUPPORT_ADMIN_IDS is empty. Add admin IDs to manage tickets.")
    
    # Create application
    application = Application.builder().token(SUPPORT_BOT_TOKEN).build()
    
    # Job queue for automated tasks
    job_queue = application.job_queue
    
    # Auto-close inactive tickets every hour
    job_queue.run_repeating(auto_close_inactive_tickets, interval=3600, first=10)
    
    # Send daily report at 23:00
    job_queue.run_daily(send_daily_report, time=datetime.strptime("23:00", "%H:%M").time())
    
    # Add handlers in STRICT ORDER
    application.add_handler(CommandHandler("start", support_start))
    application.add_handler(CommandHandler("end", handle_end_command))
    application.add_handler(CallbackQueryHandler(handle_support_callback))
    
    # CRITICAL: Admin messages MUST be handled first with highest priority
    admin_filter = AdminFilter()
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & admin_filter, 
        handle_admin_replies
    ), group=0)
    
    # User messages handled second, with explicit admin exclusion
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_user_messages
    ), group=1)
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("=" * 60)
    print("🚀 𝗤𝘂𝗮𝗻𝘁 𝗧𝗿𝗮𝗱𝗲  Enhanced Support Bot Starting...")
    print("=" * 60)
    print(f"✅ Bot Token: {'*' * 20}{SUPPORT_BOT_TOKEN[-10:] if SUPPORT_BOT_TOKEN else 'NOT SET'}")
    print(f"👮 Admin IDs: {SUPPORT_ADMIN_IDS}")
    print(f"👮 Admin Count: {len(SUPPORT_ADMIN_IDS)}")
    print(f"🔧 Features Enabled:")
    print("   • Ticket Categories")
    print("   • Priority System")
    print("   • Auto-close Inactive Tickets")
    print("   • Daily Reports")
    print("   • Ticket History")
    print("   • Admin Statistics")
    print("=" * 60)
    print("🟢 Bot is now running and ready to handle support requests!")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()