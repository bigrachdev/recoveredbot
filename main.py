"""
Main bot application
"""
import logging
import os
from datetime import time
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.request import HTTPXRequest
from database import db 
from referral_system_audit import audit_referral_system, fix_referral_system
from config import BOT_TOKEN, ADMIN_USER_IDS
from handlers.user_handlers import start_command, portfolio_command, calculate_user_profits
from handlers.admin_handlers import admin_command, confirm_investment_command, confirm_withdrawal_command
from handlers.callback_handlers import handle_callback_query
from handlers.message_handlers import handle_text_message
import atexit
import signal
import sys

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def daily_profit_job(context):
    """Daily job to calculate user profits"""
    logger.info("Running daily profit calculation...")
    try:
        calculate_user_profits()
        logger.info("Daily profit calculation completed successfully")
    except Exception as e:
        logger.error(f"Error in daily profit calculation: {e}")

async def error_handler(update, context):
    """Log errors caused by updates"""
    logger.error(f"Exception while handling update: {context.error}")

async def unknown_command(update, context):
    """Handle unknown commands"""
    await update.message.reply_text(
        "❌ Unknown command. Use /start for the main menu or click a button from the keyboard."
    )

async def update_leaderboard_job(context):
    """Update real leaderboard with latest user profits"""
    try:
        from database import db
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear and repopulate leaderboard
            cursor.execute('DELETE FROM leaderboard')
            
            cursor.execute('''
                INSERT OR REPLACE INTO leaderboard (user_id, username, profit_earned, strategy, last_updated)
                SELECT 
                    u.user_id,
                    u.username,
                    u.profit_earned,
                    u.strategy,
                    CURRENT_TIMESTAMP
                FROM users u
                WHERE u.profit_earned > 0
                ORDER BY u.profit_earned DESC
            ''')
            conn.commit()
            
        logging.info("Leaderboard updated successfully")
    except Exception as e:
        logging.error(f"Error updating leaderboard: {e}")

async def hourly_profit_job(context):
    """Hourly job to calculate user profits with random variations"""
    logger.info("Running hourly profit calculation...")
    try:
        calculate_user_profits()  # This now uses the new hourly logic
        logger.info("Hourly profit calculation completed successfully")
    except Exception as e:
        logger.error(f"Error in hourly profit calculation: {e}")

async def clear_inactive_chats_job(context):
    """Clear all messages except main menu for inactive users"""
    try:
        inactive_users = db.get_inactive_users(1)  # 1 hour inactivity
        
        for user_id in inactive_users:
            try:
                # Get all non-main menu messages for this user
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT chat_id, message_id FROM message_log 
                        WHERE user_id = ? AND is_main_menu = 0 AND deleted = 0
                    ''', (user_id,))
                    messages = cursor.fetchall()
                
                # Delete each message
                for chat_id, message_id in messages:
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                        # Mark as deleted in DB
                        cursor.execute('UPDATE message_log SET deleted = 1 WHERE chat_id = ? AND message_id = ?', 
                                     (chat_id, message_id))
                    except Exception as e:
                        logging.debug(f"Could not delete message {message_id}: {e}")
                
                conn.commit()
                
            except Exception as e:
                logging.error(f"Error clearing chats for user {user_id}: {e}")
        
        logging.info(f"Cleared chats for {len(inactive_users)} inactive users")
        
    except Exception as e:
        logging.error(f"Error in clear_inactive_chats_job: {e}")


def main():
    """Start the bot"""
    from database import db
    print(f"Database path: {db.db_path}")
    print(f"Database file exists: {os.path.exists(db.db_path)}")
    try:
        from health_server import start_health_server
        start_health_server()
        logger.info("Health check server started for Render")
    except Exception as e:
        logger.warning(f"Could not start health server: {e}")

     # ✅ ADD THIS - Start keep-alive pinger
    try:
        from keep_alive import start_keep_alive
        start_keep_alive()
        logger.info("Keep-alive system started")
    except Exception as e:
        logger.warning(f"Could not start keep-alive: {e}")
    
    # Create custom request with timeout settings
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # application.add_handler(CallbackQueryHandler(handle_stock_purchase, pattern="^buy_stock_"))

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("portfolio", portfolio_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("confirm_investment", confirm_investment_command))
    application.add_handler(CommandHandler("confirm_withdrawal", confirm_withdrawal_command))
    
    # Add callback query handler - SINGLE HANDLER FOR ALL CALLBACKS
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Schedule daily profit calculation at midnight UTC
    job_queue = application.job_queue
    job_queue.run_daily(daily_profit_job, time=time(0, 0, 0))
    job_queue.run_daily(update_leaderboard_job, time=time(0, 5, 0))
    job_queue = application.job_queue
    job_queue.run_repeating(clear_inactive_chats_job, interval=3600, first=10)
    
    logger.info("Bot is starting...")
    logger.info(f"Admin IDs configured: {ADMIN_USER_IDS}")
    
    # Initialize database
    try:
        from database import db
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_balance_logs';")
        result = cursor.fetchone()
        print("Admin table exists:", result is not None)
        
    # Start bot
    application.run_polling(allowed_updates=["message", "callback_query"])

    print("🎉 Admin system integration complete!")
    print("📝 Follow the step-by-step guide above to integrate all components")
    print("🧪 Test each feature thoroughly before deploying to production")

if __name__ == '__main__':
    # Run referral system check
    logging.info("Checking referral system...")
    if not audit_referral_system():
        logging.info("Applying referral system fixes...")
        fix_referral_system()
    
    main()