#!/usr/bin/env python3
"""Clean up test data from database"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db_context
from app.database.models import User, ConversationState, SMSMessage

def cleanup_test_data():
    """Remove test phone numbers from database"""
    test_phones = ["+1234567890", "+12025551234", "+8801928413551"]
    
    with get_db_context() as db:
        # Find and delete test users
        for phone in test_phones:
            user = db.query(User).filter(User.phone_number == phone).first()
            if user:
                # Delete related data
                db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
                db.query(SMSMessage).filter(SMSMessage.user_id == user.id).delete()
                db.delete(user)
                print(f"Cleaned up test data for {phone}")
        
        db.commit()
        print("Test data cleanup complete.")

if __name__ == "__main__":
    cleanup_test_data()