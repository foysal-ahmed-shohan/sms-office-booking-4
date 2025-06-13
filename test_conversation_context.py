#!/usr/bin/env python3
"""Test script to verify conversation context issue"""
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db_context
from app.database.models import User, ConversationState
from app.repositories.user_repository import UserRepository
from app.services.chat.conversation_manager import ConversationManager

def test_conversation_flow():
    """Test that conversation context is maintained"""
    print("Testing conversation context flow...")
    
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
        
        # First message: "I want to book a meeting room"
        print("\n--- First Message ---")
        msg1 = "I want to book a meeting room for tomorrow"
        response1 = conv_manager.process_message(user, msg1)
        print(f"User: {msg1}")
        print(f"Bot: {response1}")
        
        # Refresh session to get latest data
        db.commit()
        db.refresh(user)
        
        # Check conversation state
        conv_state = db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if conv_state:
            print(f"\nConversation state after first message:")
            print(f"- Intent: {conv_state.current_intent}")
            print(f"- Booking data: {json.dumps(conv_state.booking_data, indent=2)}")
            print(f"- History length: {len(conv_state.conversation_history) if conv_state.conversation_history else 0}")
            if conv_state.conversation_history:
                print(f"- History: {json.dumps(conv_state.conversation_history, indent=2)}")
            else:
                print("- History: None or empty")
        
        # Second message: "salt lake city"
        print("\n--- Second Message ---")
        msg2 = "salt lake city"
        response2 = conv_manager.process_message(user, msg2)
        print(f"User: {msg2}")
        print(f"Bot: {response2}")
        
        # Refresh session to get latest data
        db.commit()
        
        # Check conversation state again
        conv_state = db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if conv_state:
            print(f"\nConversation state after second message:")
            print(f"- Intent: {conv_state.current_intent}")
            print(f"- Booking data: {json.dumps(conv_state.booking_data, indent=2)}")
            print(f"- History length: {len(conv_state.conversation_history) if conv_state.conversation_history else 0}")
            
            # Check if location was captured
            if 'location' in conv_state.booking_data:
                print(f"✓ Location captured: {conv_state.booking_data['location']}")
            else:
                print("✗ Location NOT captured!")
        
        # Clean up test data
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        print("\nTest data cleaned up.")

if __name__ == "__main__":
    test_conversation_flow()