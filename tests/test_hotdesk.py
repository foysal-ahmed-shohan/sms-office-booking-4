#!/usr/bin/env python3
"""Test hot desk booking flow"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
import logging

# Show INFO level logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_hotdesk_flow():
    """Test hot desk booking flow"""
    db = next(get_db())
    
    try:
        # Setup user
        user = db.query(User).filter(User.phone_number == "+1234567890").first()
        if not user:
            user = User(phone_number="+1234567890", twilio_phone_number="+10987654321", is_active=True)
            db.add(user)
            db.commit()
        
        # Clear conversation
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        
        conv_manager = ConversationManager(db)
        
        print("\n" + "="*70)
        print("HOT DESK BOOKING TEST")
        print("="*70)
        
        # Test hot desk request
        print("\n1. User requests hot desk:")
        message = "need space for atlanta, 2 people, hot desk, 6 dec 2025 1pm to 2pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        response = conv_manager.process_message(user, message)
        print(f"System:\n{response}")
        
        # Check response
        if "hot desk" in response.lower():
            print("\n✅ Correctly showing hot desk options!")
        else:
            print("\n❌ ERROR: Not showing hot desk options!")
            
        # Check for wrong resources
        if "booth" in response.lower() or "phone booth" in response.lower():
            print("\n❌ ERROR: Showing phone booths instead of hot desks!")
        else:
            print("\n✅ Not showing incorrect resource types!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_hotdesk_flow()