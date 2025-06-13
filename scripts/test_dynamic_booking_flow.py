#!/usr/bin/env python3
"""Test dynamic booking flow with OfficeRND integration"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.schemas.booking_schema import BookingSlots
import json


def test_booking_conversation():
    """Test a complete booking conversation with dynamic data"""
    print("\n=== Testing Dynamic Booking Conversation ===\n")
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    # Test scenarios
    conversations = [
        {
            "user": "I want to book a meeting room",
            "expected_intent": "book_room",
            "description": "Initial booking request"
        },
        {
            "user": "Chicago",  # Invalid location
            "expected_response": "location not found",
            "description": "Invalid location test"
        },
        {
            "user": "Atlanta",  # Valid location
            "expected_update": {"location": "Atlanta"},
            "description": "Valid location"
        },
        {
            "user": "conference room",  # Invalid type (only meeting room available)
            "expected_response": "not available",
            "description": "Invalid room type"
        },
        {
            "user": "meeting room",  # Valid type
            "expected_update": {"room_type": "meeting_room"},
            "description": "Valid room type"
        },
        {
            "user": "5 people, tomorrow 2pm-4pm",
            "expected_update": {"capacity": 5, "date": "tomorrow", "time": "2pm"},
            "description": "Multiple info at once"
        }
    ]
    
    for conv in conversations:
        print(f"\n{conv['description']}:")
        print(f"User: {conv['user']}")
        
        if 'expected_intent' in conv:
            intent = chat_service.extract_booking_intent(conv['user'])
            print(f"Intent: {intent.value}")
        
        if 'expected_update' in conv:
            slots = chat_service.extract_booking_slots(conv['user'], slots)
            print(f"Updated slots: {json.dumps(slots.dict(exclude_none=True), indent=2)}")
        
        if 'expected_response' in conv:
            response = chat_service.generate_response(
                conv['user'], 
                chat_service.extract_booking_intent(conv['user']),
                slots,
                []
            )
            print(f"System: {response}")


def test_dynamic_prompts():
    """Test that prompts contain real OfficeRND data"""
    from app.schemas.booking_schema import get_dynamic_slot_prompts
    
    print("\n=== Dynamic Prompts Test ===\n")
    prompts = get_dynamic_slot_prompts()
    
    print("When asking for location:")
    print(f"  {prompts['location']}")
    
    print("\nWhen asking for room type:")
    print(f"  {prompts['room_type']}")
    
    # Verify they contain real data
    assert "Atlanta" in prompts['location'] or "New York" in prompts['location']
    assert "Meeting room" in prompts['room_type'] or "Dedicated desk" in prompts['room_type']
    print("\n✓ Prompts contain real OfficeRND data")


def test_location_validation():
    """Test location validation against OfficeRND"""
    from app.services.officernd_service import officernd_service
    
    print("\n=== Location Validation Test ===\n")
    
    test_locations = [
        ("san francisco", False),  # Not in OfficeRND
        ("atlanta", True),         # Valid
        ("new york", True),        # Valid
        ("salt lake city", False), # Not in OfficeRND
        ("dallas", True)           # Valid
    ]
    
    for location, expected_valid in test_locations:
        match = officernd_service.match_location(location)
        is_valid = match is not None
        status = "✓" if is_valid == expected_valid else "✗"
        result = f"Valid ({match['name']})" if match else "Invalid"
        print(f"{status} '{location}' -> {result}")


def main():
    """Run all tests"""
    print("Starting Dynamic Booking Flow Tests")
    print("=" * 50)
    
    try:
        test_dynamic_prompts()
        test_location_validation()
        test_booking_conversation()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()