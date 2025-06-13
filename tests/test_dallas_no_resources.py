#!/usr/bin/env python3
"""Test Dallas location with no resources"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState

def test_dallas_no_resources():
    """Test Dallas location that has no resources"""
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
        print("DALLAS (NO RESOURCES) TEST")
        print("="*70)
        
        # Test Dallas request
        print("\n1. User requests Dallas location (which has no meeting rooms):")
        message = "need meeting room in dallas for 4 people on 23 dec 2025 1pm to 2pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"System:\n{response}")
        
        # Check response
        if "don't have any meeting room available at Dallas" in response:
            print("\n✅ Correctly handled location with no resources!")
        elif "noted down" in response.lower():
            print("\n❓ System noted down info - Dallas has no meeting rooms to show")
        else:
            print("\n❓ Unexpected response")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_dallas_no_resources()