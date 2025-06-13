#!/usr/bin/env python3
"""Test meeting room booking flow"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState

def test_meeting_room_flow():
    """Test meeting room booking flow"""
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
        print("MEETING ROOM BOOKING TEST")
        print("="*70)
        
        # Test meeting room request
        print("\n1. User requests meeting room:")
        message = "need meeting room for 4 people in atlanta on dec 10 2025 2pm to 4pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        response = conv_manager.process_message(user, message)
        print(f"System:\n{response}")
        
        # Check response
        if "meeting room" in response.lower() and "board room" in response.lower():
            print("\n✅ Correctly showing meeting room options including Board Room!")
        else:
            print("\n❌ ERROR: Not showing proper meeting room options!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_meeting_room_flow()