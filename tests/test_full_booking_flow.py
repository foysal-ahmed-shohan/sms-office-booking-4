#!/usr/bin/env python3
"""Test complete booking flow to ensure context is maintained throughout"""
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db_context
from app.database.models import User, ConversationState
from app.repositories.user_repository import UserRepository
from app.services.chat.conversation_manager import ConversationManager

def test_full_booking_flow():
    """Test a complete booking conversation flow"""
    print("Testing full booking conversation flow...\n")
    
    # Test phone number
    test_phone = "+1234567890"
    
    with get_db_context() as db:
        # Create or get user
        user_repo = UserRepository(db)
        user = user_repo.create_or_update(
            phone_number=test_phone,
            twilio_phone_number="+18123591901"
        )
        print(f"User created/found: {user.id}")
        
        # Initialize conversation manager
        conv_manager = ConversationManager(db)
        
        # Simulate full conversation
        messages = [
            "I want to book a meeting room",
            "salt lake city",
            "5 people",
            "tomorrow at 2pm",
            "2 hours"
        ]
        
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"User: {msg}")
            
            response = conv_manager.process_message(user, msg)
            print(f"Bot: {response}")
            
            # Check state after each message
            db.commit()
            conv_state = db.query(ConversationState).filter(
                ConversationState.user_id == user.id
            ).first()
            
            if conv_state:
                print(f"\nCurrent booking data: {json.dumps(conv_state.booking_data, indent=2)}")
                print(f"History length: {len(conv_state.conversation_history) if conv_state.conversation_history else 0}")
                
                # Check if booking is complete
                if conv_state.state == 'completed':
                    print("\n✓ BOOKING COMPLETED!")
                    print(f"Final booking details: {json.dumps(conv_state.booking_data, indent=2)}")
        
        # Clean up test data
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        print("\nTest data cleaned up.")

if __name__ == "__main__":
    test_full_booking_flow()