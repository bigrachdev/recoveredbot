"""
Complete Referral System Audit and Fixes
Add this to test the referral system and apply necessary fixes
"""

import logging
from database import db

def audit_referral_system():
    """Audit the entire referral system"""
    print("\n" + "="*60)
    print("REFERRAL SYSTEM AUDIT")
    print("="*60)
    
    issues_found = []
    
    # 1. Check database schema
    print("\n1. Checking database schema...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("PRAGMA table_info(users)")
        users_columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        required_user_columns = ['referral_code', 'referred_by']
        for col in required_user_columns:
            if col in users_columns:
                print(f"   ✅ users.{col} exists ({users_columns[col]})")
            else:
                print(f"   ❌ users.{col} MISSING!")
                issues_found.append(f"Missing column: users.{col}")
        
        # Check referrals table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
        if cursor.fetchone():
            print("   ✅ referrals table exists")
            cursor.execute("PRAGMA table_info(referrals)")
            referrals_columns = {col[1]: col[2] for col in cursor.fetchall()}
            print(f"      Columns: {', '.join(referrals_columns.keys())}")
        else:
            print("   ❌ referrals table MISSING!")
            issues_found.append("Missing table: referrals")
    
    # 2. Check referral code generation
    print("\n2. Checking referral code generation...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, referral_code FROM users WHERE referral_code IS NOT NULL LIMIT 5")
        codes = cursor.fetchall()
        
        if codes:
            print(f"   ✅ Found {len(codes)} users with referral codes:")
            for user_id, code in codes:
                print(f"      User {user_id}: {code}")
            
            # Check for duplicates
            cursor.execute("""
                SELECT referral_code, COUNT(*) as count 
                FROM users 
                WHERE referral_code IS NOT NULL 
                GROUP BY referral_code 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"   ❌ Found {len(duplicates)} duplicate referral codes!")
                issues_found.append(f"Duplicate referral codes: {duplicates}")
            else:
                print("   ✅ No duplicate referral codes")
        else:
            print("   ⚠️  No users have referral codes yet")
    
    # 3. Check referral relationships
    print("\n3. Checking referral relationships...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check users.referred_by
        cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL")
        referred_users = cursor.fetchone()[0]
        print(f"   Users with referrer: {referred_users}")
        
        # Check referrals table
        cursor.execute("SELECT COUNT(*) FROM referrals")
        referral_records = cursor.fetchone()[0]
        print(f"   Referral records: {referral_records}")
        
        if referred_users != referral_records:
            print(f"   ⚠️  Mismatch: {referred_users} users with referrer, but {referral_records} referral records")
            issues_found.append("Referral count mismatch between users and referrals table")
        
        # Check for orphaned referrals
        cursor.execute("""
            SELECT r.id, r.referrer_id, r.referred_id 
            FROM referrals r
            LEFT JOIN users u1 ON r.referrer_id = u1.user_id
            LEFT JOIN users u2 ON r.referred_id = u2.user_id
            WHERE u1.user_id IS NULL OR u2.user_id IS NULL
        """)
        orphaned = cursor.fetchall()
        if orphaned:
            print(f"   ❌ Found {len(orphaned)} orphaned referral records!")
            issues_found.append(f"Orphaned referrals: {len(orphaned)}")
        else:
            print("   ✅ No orphaned referral records")
    
    # 4. Check referral display functionality
    print("\n4. Checking referral display...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.referral_code,
                   (SELECT COUNT(*) FROM referrals WHERE referrer_id = u.user_id) as referral_count
            FROM users u
            WHERE u.referral_code IS NOT NULL
            LIMIT 5
        """)
        users_with_referrals = cursor.fetchall()
        
        for user_id, username, ref_code, count in users_with_referrals:
            print(f"   User @{username or user_id}: Code={ref_code}, Referrals={count}")
    
    # 5. Test referral code lookup
    print("\n5. Testing referral code lookup...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referral_code FROM users WHERE referral_code IS NOT NULL LIMIT 1")
        test_code = cursor.fetchone()
        
        if test_code:
            test_code = test_code[0]
            cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (test_code,))
            result = cursor.fetchone()
            if result:
                print(f"   ✅ Lookup test passed: Code '{test_code}' -> User {result[0]}")
            else:
                print(f"   ❌ Lookup test FAILED for code '{test_code}'!")
                issues_found.append("Referral code lookup failed")
    
    # Summary
    print("\n" + "="*60)
    if issues_found:
        print(f"❌ AUDIT FAILED - {len(issues_found)} issues found:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ AUDIT PASSED - Referral system is working correctly!")
    print("="*60 + "\n")
    
    return len(issues_found) == 0


def fix_referral_system():
    """Apply fixes to the referral system"""
    print("\n" + "="*60)
    print("APPLYING REFERRAL SYSTEM FIXES")
    print("="*60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Fix 1: Ensure all users have referral codes
        print("\n1. Ensuring all users have referral codes...")
        cursor.execute("SELECT user_id FROM users WHERE referral_code IS NULL")
        users_without_codes = cursor.fetchall()
        
        if users_without_codes:
            print(f"   Found {len(users_without_codes)} users without referral codes")
            import random
            for (user_id,) in users_without_codes:
                ref_code = f"AV{user_id}{random.randint(100, 999)}"
                cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (ref_code, user_id))
                print(f"   Generated code {ref_code} for user {user_id}")
            conn.commit()
            print("   ✅ All users now have referral codes")
        else:
            print("   ✅ All users already have referral codes")
        
        # Fix 2: Sync referrals table with users.referred_by
        print("\n2. Syncing referrals table...")
        cursor.execute("""
            SELECT user_id, referred_by 
            FROM users 
            WHERE referred_by IS NOT NULL
        """)
        users_with_referrer = cursor.fetchall()
        
        for user_id, referrer_id in users_with_referrer:
            # Check if referral record exists
            cursor.execute("""
                SELECT id FROM referrals 
                WHERE referrer_id = ? AND referred_id = ?
            """, (referrer_id, user_id))
            
            if not cursor.fetchone():
                print(f"   Creating missing referral record: {referrer_id} -> {user_id}")
                cursor.execute("""
                    INSERT INTO referrals (referrer_id, referred_id, bonus_amount)
                    VALUES (?, ?, 0)
                """, (referrer_id, user_id))
        
        conn.commit()
        print("   ✅ Referrals table synced")
        
        # Fix 3: Remove orphaned referrals
        print("\n3. Cleaning orphaned referrals...")
        cursor.execute("""
            DELETE FROM referrals
            WHERE referrer_id NOT IN (SELECT user_id FROM users)
               OR referred_id NOT IN (SELECT user_id FROM users)
        """)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"   Removed {deleted} orphaned referral records")
        conn.commit()
        print("   ✅ Orphaned referrals cleaned")
    
    print("\n" + "="*60)
    print("✅ FIXES APPLIED SUCCESSFULLY")
    print("="*60 + "\n")


def test_referral_flow():
    """Test the complete referral flow"""
    print("\n" + "="*60)
    print("TESTING REFERRAL FLOW")
    print("="*60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get a test user with referral code
        cursor.execute("SELECT user_id, username, referral_code FROM users LIMIT 1")
        test_user = cursor.fetchone()
        
        if not test_user:
            print("❌ No users in database to test with")
            return False
        
        user_id, username, ref_code = test_user
        print(f"\n📋 Test Scenario:")
        print(f"   Referrer: @{username or user_id}")
        print(f"   Referral Code: {ref_code}")
        
        # Test 1: Code lookup
        print(f"\n1. Testing code lookup for '{ref_code}'...")
        cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (ref_code,))
        found = cursor.fetchone()
        if found and found[0] == user_id:
            print(f"   ✅ Code lookup successful")
        else:
            print(f"   ❌ Code lookup FAILED")
            return False
        
        # Test 2: Get referral count
        print(f"\n2. Testing referral count...")
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"   User has {count} referrals")
        
        # Test 3: Get referred users
        print(f"\n3. Testing referred users list...")
        cursor.execute("""
            SELECT u.user_id, u.username 
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
        """, (user_id,))
        referred = cursor.fetchall()
        if referred:
            print(f"   Found {len(referred)} referred users:")
            for ref_id, ref_username in referred:
                print(f"      - @{ref_username or ref_id}")
        else:
            print("   No referred users yet")
        
        print("\n✅ Referral flow test completed")
    
    return True


if __name__ == "__main__":
    print("\n🔍 Starting Referral System Diagnostics...\n")
    
    # Run audit
    audit_passed = audit_referral_system()
    
    # Apply fixes if needed
    if not audit_passed:
        print("\n🔧 Issues detected. Applying fixes...")
        fix_referral_system()
        
        # Re-run audit
        print("\n🔍 Re-running audit after fixes...")
        audit_referral_system()
    
    # Test the flow
    test_referral_flow()
    
    print("\n✅ Diagnostics complete!\n")
