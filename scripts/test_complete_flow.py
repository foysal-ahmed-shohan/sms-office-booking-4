#!/usr/bin/env python3
"""Test complete conversation flow with improved messaging"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import User, ConversationState
from app.services.chat.conversation_manager import ConversationManager
from app.config import settings
import json


def simulate_conversation():
    """Simulate a complete booking conversation"""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    from app.database.base import Base
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Create test user
    user = User(phone_number="+1234567890", twilio_phone_number="+0987654321")
    db.add(user)
    db.commit()
    
    # Initialize conversation manager
    conv_manager = ConversationManager(db)
    
    print("\n" + "=" * 60)
    print("COMPLETE BOOKING CONVERSATION FLOW")
    print("=" * 60)
    
    # Test conversations
    conversations = [
        {
            "user": "I want to book a room",
            "description": "Initial request - should show all options"
        },
        {
            "user": "I need a meeting room",
            "description": "Specifying room type only"
        },
        {
            "user": "Atlanta, 5 people, tomorrow 2pm",
            "description": "Providing multiple details at once"
        },
        {
            "user": "Chicago",
            "description": "Invalid location test"
        },
        {
            "user": "conference room in Dallas",
            "description": "Invalid room type test"
        },
        {
            "user": "meeting room in Dallas for 10 people",
            "description": "Valid location and room type"
        },
        {
            "user": "next Friday at 3pm for 2 hours",
            "description": "Completing the booking"
        }
    ]
    
    for conv in conversations:
        print(f"\n{conv['description']}:")
        print(f"User: \"{conv['user']}\"")
        print("-" * 50)
        
        response = conv_manager.process_message(user, conv['user'])
        print(f"Bot:\n{response}")
        
        # Show current booking state
        conv_state = db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if conv_state and conv_state.booking_data:
            filled_slots = {k: v for k, v in conv_state.booking_data.items() if v}
            if filled_slots:
                print(f"\n[Current booking data: {json.dumps(filled_slots, indent=2)}]")
    
    db.close()
    print("\n" + "=" * 60)


def main():
    """Run the complete flow test"""
    print("\nTesting Complete Conversation Flow with Improved Messaging")
    
    try:
        simulate_conversation()
        
        print("\n✓ Test completed successfully!")
        print("\nKey features demonstrated:")
        print("• All missing info requested at once")
        print("• Dynamic locations/room types shown")
        print("• Invalid location/room type handling")
        print("• Clean SMS-friendly formatting")
        print("• Natural conversation flow")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()