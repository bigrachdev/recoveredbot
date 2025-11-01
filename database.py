"""
Database operations for the trading bot
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = 'trading_bot.db'):
        self.db_path = db_path
        self.init_database()
        self.ensure_admin_tables()
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    
        
        # In database.py (upgrade init_database to add real leaderboard table)
    def init_database(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    full_name TEXT,
                    email TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    strategy TEXT,
                    total_invested REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0,
                    profit_earned REAL DEFAULT 0,
                    last_profit_update TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    wallet_address TEXT,
                    FOREIGN KEY (referred_by) REFERENCES users (user_id)
                )
            ''')
            
            # Users table (Upgraded: 'plan' -> 'strategy')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    message_id INTEGER,
                    user_id INTEGER,
                    message_type TEXT DEFAULT 'bot_message',
                    is_main_menu BOOLEAN DEFAULT 0,
                    deleted BOOLEAN DEFAULT 0,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delete_after_hours INTEGER DEFAULT 2
                )
            ''')
            
            # Investments table (Upgraded: 'plan' -> 'strategy')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    crypto_type TEXT,
                    wallet_address TEXT,
                    transaction_id TEXT,
                    investment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    strategy TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Withdrawals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    wallet_address TEXT,
                    withdrawal_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    processed_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Referrals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bonus_amount REAL DEFAULT 0,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_id) REFERENCES users (user_id)
                )
            ''')
            
            # Admin logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_balance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    target_user_id INTEGER,
                    action_type TEXT,
                    amount REAL,
                    old_balance REAL,
                    new_balance REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (admin_id) REFERENCES users (user_id),
                    FOREIGN KEY (target_user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Real leaderboard table (materialized view-like, updated via job)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leaderboard (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    profit_earned REAL DEFAULT 0,
                    strategy TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    message_id INTEGER,
                    user_id INTEGER,
                    message_type TEXT,
                    is_main_menu INTEGER DEFAULT 0,
                    deleted INTEGER DEFAULT 0,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    message_id INTEGER,
                    user_id INTEGER,
                    message_type TEXT DEFAULT 'bot_message',
                    is_main_menu BOOLEAN DEFAULT 0,
                    deleted BOOLEAN DEFAULT 0,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delete_after_hours INTEGER DEFAULT 2
                )
            ''')
            conn.commit()
        
        # Add index for performance
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leaderboard_profit ON leaderboard(profit_earned DESC)')
            conn.commit()
            
                
    def ensure_admin_tables(self):
        """Ensure admin-related tables exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
    def get_user(self, user_id: int) -> Optional[Tuple]:
        """Get user data by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def create_or_update_user(self, user_id: int, username: str, first_name: str, 
                             full_name: str = None, email: str = None, referred_by_id: int = None) -> bool:
        """Create new user or update existing one"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
                user_exists = cursor.fetchone()
                
                if user_exists:
                    cursor.execute('''
                        UPDATE users SET username = ?, first_name = ?, full_name = ?, email = ? 
                        WHERE user_id = ?
                    ''', (username, first_name, full_name, email, user_id))
                else:
                    import random
                    referral_code = f"AV{user_id}{random.randint(100, 999)}"
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, full_name, email, referral_code, referred_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, username, first_name, full_name, email, referral_code, referred_by_id))
                    
                    # Add referral record if referred
                    if referred_by_id:
                        cursor.execute('''
                            INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)
                        ''', (referred_by_id, user_id))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating/updating user {user_id}: {e}")
            return False
    
    # BEFORE:
    def add_investment(self, user_id: int, amount: float, crypto_type: str, 
                  wallet_address: str, transaction_id: str, strategy: str, notes: str = None) -> bool:
        """Add new investment record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO investments (user_id, amount, crypto_type, wallet_address, transaction_id, strategy, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, amount, crypto_type, wallet_address, transaction_id, strategy, notes))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding investment: {e}")
            return False
    
    def confirm_investment(self, investment_id: int, admin_id: int) -> bool:
        """Confirm a pending investment and process referral bonus (Upgraded: 'plan' -> 'strategy')"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get investment details (Upgraded: 'plan' -> 'strategy')
                cursor.execute('''
                    SELECT user_id, amount, strategy FROM investments 
                    WHERE id = ? AND status = 'pending'
                ''', (investment_id,))
                investment = cursor.fetchone()
                
                if not investment:
                    return False
                
                user_id, amount, strategy = investment
                
                # Check if this is first confirmed investment
                cursor.execute('''
                    SELECT COUNT(*) FROM investments 
                    WHERE user_id = ? AND status = 'confirmed'
                ''', (user_id,))
                previous_investments = cursor.fetchone()[0]
                is_first_investment = (previous_investments == 0)
                
                # Update investment status
                cursor.execute('''
                    UPDATE investments SET status = 'confirmed' WHERE id = ?
                ''', (investment_id,))
                
                # Update user balance and strategy (Upgraded: 'plan' -> 'strategy')
                cursor.execute('''
                    UPDATE users 
                    SET total_invested = total_invested + ?, 
                        current_balance = current_balance + ?,
                        strategy = ?,
                        last_profit_update = ?
                    WHERE user_id = ?
                ''', (amount, amount, strategy, datetime.now().isoformat(), user_id))
                
                # Process referral bonus if first investment
                if is_first_investment:
                    # Check if user was referred
                    cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        referrer_id = result[0]
                        
                        # Calculate 5% bonus
                        bonus_amount = amount * 0.05
                        
                        # Update referral record
                        cursor.execute('''
                            UPDATE referrals 
                            SET bonus_amount = ?
                            WHERE referrer_id = ? AND referred_id = ?
                        ''', (bonus_amount, referrer_id, user_id))
                        
                        # Credit referrer's balance
                        cursor.execute('SELECT current_balance FROM users WHERE user_id = ?', (referrer_id,))
                        referrer_balance = cursor.fetchone()
                        
                        if referrer_balance:
                            old_balance = referrer_balance[0]
                            new_balance = old_balance + bonus_amount
                            
                            cursor.execute('''
                                UPDATE users 
                                SET current_balance = ?
                                WHERE user_id = ?
                            ''', (new_balance, referrer_id))
                            
                            # Log the bonus
                            cursor.execute('''
                                INSERT INTO admin_balance_logs 
                                (admin_id, target_user_id, action_type, amount, old_balance, new_balance, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                0,  # System action
                                referrer_id,
                                'referral_bonus',
                                bonus_amount,
                                old_balance,
                                new_balance,
                                f'5% referral bonus from user {user_id} investment of ${amount:.2f}'
                            ))
                            
                            logging.info(f"✅ Referral bonus paid: ${bonus_amount:.2f} to user {referrer_id}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error confirming investment {investment_id}: {e}")
            return False
    
    def get_pending_investments(self):
        """Get all pending investments with user details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.id, i.user_id, 
                        COALESCE(u.username, 'N/A') as username,
                        COALESCE(u.full_name, 'N/A') as full_name,
                        COALESCE(u.email, 'N/A') as email,
                        i.amount, 
                        COALESCE(i.crypto_type, 'N/A') as crypto_type,
                        COALESCE(i.transaction_id, 'N/A') as transaction_id,
                        i.investment_date,
                        i.notes
                    FROM investments i
                    LEFT JOIN users u ON i.user_id = u.user_id
                    WHERE i.status = 'pending'
                    ORDER BY i.investment_date DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting pending investments: {e}")
            return []
    
    def get_pending_withdrawals(self):
        """Get all pending withdrawals with user details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT w.id, w.user_id,   -- ✅ MAKE SURE w.id IS FIRST!
                        COALESCE(u.username, 'N/A') as username,
                        COALESCE(u.full_name, 'N/A') as full_name,
                        COALESCE(u.email, 'N/A') as email,
                        w.amount, 
                        COALESCE(w.wallet_address, 'N/A') as wallet_address,
                        w.withdrawal_date
                    FROM withdrawals w
                    LEFT JOIN users u ON w.user_id = u.user_id
                    WHERE w.status = 'pending'
                    ORDER BY w.withdrawal_date DESC
                ''')
                results = cursor.fetchall()
                
                # Debug: Log the results
                logging.info(f"Found {len(results)} pending withdrawals")
                for i, row in enumerate(results):
                    logging.info(f"Withdrawal {i}: ID={row[0]}, User={row[1]}, Amount={row[5]}")  # ✅ row[0] should be withdrawal ID
                
                return results
        except Exception as e:
            logging.error(f"Error getting pending withdrawals: {e}")
            return []
        
    def get_user_stats(self) -> Dict[str, Any]:
        """Get overall user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            # Active investors
            cursor.execute('SELECT COUNT(*) FROM users WHERE total_invested > 0')
            stats['active_investors'] = cursor.fetchone()[0]
            
            # Total investments
            cursor.execute('SELECT SUM(total_invested) FROM users')
            stats['total_crypto_invested'] = cursor.fetchone()[0] or 0
            
            
            # Total balances
            cursor.execute('SELECT SUM(current_balance) FROM users')
            stats['total_balances'] = cursor.fetchone()[0] or 0
            
            # Pending items
            cursor.execute('SELECT COUNT(*) FROM investments WHERE status = "pending"')
            stats['pending_investments'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "pending"')
            stats['pending_withdrawals'] = cursor.fetchone()[0]
            
            return stats
    
    
    def log_message(self, chat_id, message_id, user_id=None, message_type='bot_message', is_main_menu=False):
        """Log a message for auto-deletion"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO message_log 
                    (chat_id, message_id, user_id, message_type, is_main_menu, sent_date)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (chat_id, message_id, user_id, message_type, 1 if is_main_menu else 0))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error logging message: {e}")
            return False
    
    def get_messages_to_delete(self, hours_old: int = 2) -> List[Tuple]:
        """Get messages that should be deleted"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, chat_id, message_id
                FROM message_log
                WHERE deleted = 0 
                  AND is_main_menu = 0
                  AND datetime(sent_date, '+' || delete_after_hours || ' hours') <= datetime('now')
                LIMIT 100
            ''', ())
            return cursor.fetchall()
    
    def mark_message_deleted(self, log_id: int) -> bool:
        """Mark a message as deleted"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE message_log SET deleted = 1 WHERE id = ?
                ''', (log_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error marking message deleted: {e}")
            return False

def get_inactive_users(self, hours=1):
        """Get users with no activity in specified hours"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT user_id FROM message_log 
                WHERE datetime(sent_date, '+' || ? || ' hours') <= datetime('now')
                AND is_main_menu = 0
            ''', (hours,))
            return [row[0] for row in cursor.fetchall()]

# Temporary debug function - add this to your database.py
def debug_get_all_withdrawals(self):
    """Debug function to see all withdrawals"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, amount, status, withdrawal_date 
                FROM withdrawals 
                ORDER BY withdrawal_date DESC
            ''')
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error getting all withdrawals: {e}")
        return []
# Global database instance
db = DatabaseManager()