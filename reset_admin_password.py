#!/usr/bin/env python3
"""
Script to reset the admin password in the SEU Tools database.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, User
from passlib.context import CryptContext

def reset_admin_password():
    """Reset the admin password to a known value."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # New password
    new_password = "admin123"
    
    db = SessionLocal()
    try:
        # Find the admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("Admin user not found!")
            return False
        
        # Update the password
        admin_user.hashed_password = pwd_context.hash(new_password)
        db.commit()
        
        print(f"✅ Admin password reset successfully!")
        print(f"Username: admin")
        print(f"Password: {new_password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password() 