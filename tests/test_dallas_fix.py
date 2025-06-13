#!/usr/bin/env python3
"""Test Dallas location and resource display"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState

def test_dallas_flow():
    """Test Dallas location booking flow"""
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
        print("DALLAS LOCATION TEST")
        print("="*70)
        
        # Test Atlanta request (known to have resources)
        print("\n1. User requests Atlanta location:")
        message = "location atlanta, 4 people, meeting room, 23 dec 2025 1pm to 2pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"System:\n{response}")
        
        # Check if resources are shown
        if "please choose a specific" in response.lower():
            print("\n✅ Resources shown correctly!")
        elif "noted down" in response.lower():
            print("\n❌ ERROR: System just noted down info instead of showing resources!")
        elif "don't have an office" in response.lower():
            print("\n❌ ERROR: Dallas not recognized as valid location!")
        else:
            print("\n❓ Unexpected response")
            
        # Test invalid location
        print("\n\n2. Testing invalid location:")
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        
        message = "location chicago, 2 people, meeting room, 25 dec 2025 2pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"System:\n{response}")
        
        if "don't have an office" in response.lower():
            print("\n✅ Invalid location handled correctly!")
        else:
            print("\n❌ ERROR: Invalid location not caught!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_dallas_flow()