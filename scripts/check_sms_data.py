#!/usr/bin/env python3
"""Check SMS data in database"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import engine
from app.database.models import User, SMSMessage
from app.database.connection import get_db_context
from datetime import datetime

def check_sms_data():
    """Display SMS data from database"""
    with get_db_context() as db:
        print("\n=== USERS ===")
        users = db.query(User).all()
        if not users:
            print("No users found")
        else:
            for user in users:
                print(f"\nUser ID: {user.id}")
                print(f"  Phone: {user.phone_number}")
                print(f"  Twilio Number: {user.twilio_phone_number}")
                print(f"  Created: {user.created_at}")
                print(f"  Active: {user.is_active}")
        
        print("\n=== SMS MESSAGES ===")
        messages = db.query(SMSMessage).order_by(SMSMessage.created_at.desc()).limit(20).all()
        if not messages:
            print("No messages found")
        else:
            for msg in messages:
                print(f"\nMessage ID: {msg.id}")
                print(f"  User ID: {msg.user_id}")
                print(f"  Direction: {msg.direction}")
                print(f"  From: {msg.from_number}")
                print(f"  To: {msg.to_number}")
                print(f"  Body: {msg.message_body[:100]}{'...' if len(msg.message_body) > 100 else ''}")
                print(f"  Status: {msg.status}")
                print(f"  Message SID: {msg.message_sid}")
                print(f"  Created: {msg.created_at}")
                if msg.error_message:
                    print(f"  Error: {msg.error_message}")
        
        # Show counts
        print("\n=== STATISTICS ===")
        total_users = db.query(User).count()
        total_messages = db.query(SMSMessage).count()
        inbound = db.query(SMSMessage).filter(SMSMessage.direction == 'inbound').count()
        outbound = db.query(SMSMessage).filter(SMSMessage.direction == 'outbound').count()
        
        print(f"Total Users: {total_users}")
        print(f"Total Messages: {total_messages}")
        print(f"  - Inbound: {inbound}")
        print(f"  - Outbound: {outbound}")
        
        # Show message pairs (inbound + reply)
        print("\n=== RECENT CONVERSATIONS ===")
        recent_inbound = db.query(SMSMessage).filter(
            SMSMessage.direction == 'inbound'
        ).order_by(SMSMessage.created_at.desc()).limit(5).all()
        
        for inbound_msg in recent_inbound:
            print(f"\n[{inbound_msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"USER → SYSTEM: {inbound_msg.message_body}")
            
            # Find corresponding reply
            reply = db.query(SMSMessage).filter(
                SMSMessage.user_id == inbound_msg.user_id,
                SMSMessage.direction == 'outbound',
                SMSMessage.created_at >= inbound_msg.created_at
            ).first()
            
            if reply:
                print(f"SYSTEM → USER: {reply.message_body}")
                print(f"  Status: {reply.status}")
            else:
                print("SYSTEM → USER: (No reply found)")

if __name__ == "__main__":
    check_sms_data()