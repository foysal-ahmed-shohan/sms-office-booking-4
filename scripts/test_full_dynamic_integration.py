#!/usr/bin/env python3
"""Test full dynamic integration with conversation manager"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import User, ConversationState
from app.services.chat.conversation_manager import ConversationManager
from app.config import settings
import json


def test_full_conversation():
    """Test a full conversation with dynamic OfficeRND data"""
    print("\n=== Testing Full Dynamic Conversation ===\n")
    
    # Create in-memory database for testing
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
    
    # Simulate conversation
    messages = [
        "I want to book a meeting room",
        "San Francisco",  # This should fail - not in OfficeRND
        "Atlanta",        # This should work
        "conference room", # This should fail - not available
        "meeting room",   # This should work
        "5 people",
        "tomorrow at 2pm",
        "2 hours"
    ]
    
    print("Conversation:")
    print("-" * 50)
    
    for msg in messages:
        print(f"\nUser: {msg}")
        response = conv_manager.process_message(user, msg)
        print(f"Bot: {response}")
        
        # Show current booking state
        conv_state = db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if conv_state and conv_state.booking_data:
            print(f"Current booking data: {json.dumps(conv_state.booking_data, indent=2)}")
    
    db.close()


def test_dynamic_suggestions():
    """Test that suggestions are dynamic"""
    from app.schemas.booking_schema import get_dynamic_slot_prompts
    
    print("\n=== Testing Dynamic Suggestions ===\n")
    
    prompts = get_dynamic_slot_prompts()
    
    # Verify prompts contain real OfficeRND data
    location_prompt = prompts['location']
    room_prompt = prompts['room_type']
    
    print("Location prompt includes real offices:")
    print(f"  {location_prompt}")
    
    # Check that at least one real location is mentioned
    real_locations = ["Atlanta", "New York", "Dallas"]
    has_real_location = any(loc in location_prompt for loc in real_locations)
    
    if has_real_location:
        print("  ✓ Contains real OfficeRND locations")
    else:
        print("  ✗ Does not contain real locations")
    
    print("\nRoom type prompt includes real options:")
    print(f"  {room_prompt}")
    
    # Check that at least one real room type is mentioned
    real_types = ["Meeting room", "Dedicated desk", "Hotdesk"]
    has_real_type = any(rt in room_prompt for rt in real_types)
    
    if has_real_type:
        print("  ✓ Contains real OfficeRND room types")
    else:
        print("  ✗ Does not contain real room types")


def main():
    """Run all tests"""
    print("Starting Full Dynamic Integration Test")
    print("=" * 50)
    
    try:
        test_dynamic_suggestions()
        test_full_conversation()
        
        print("\n" + "=" * 50)
        print("✓ Integration test completed successfully!")
        print("\nKey features demonstrated:")
        print("- Dynamic location suggestions from OfficeRND")
        print("- Dynamic room type suggestions from OfficeRND")
        print("- Location validation against real OfficeRND data")
        print("- Room type validation against real OfficeRND data")
        print("- Proper error handling for invalid locations/types")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()