#!/usr/bin/env python3
"""Test improved messaging with all info asked at once"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.schemas.booking_schema import BookingSlots, BookingIntent
import json


def test_initial_booking_request():
    """Test response when user says 'I want to book a room'"""
    print("\n=== Test 1: Initial Booking Request ===")
    print("User: 'I want to book a room'\n")
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    # Extract intent
    intent = chat_service.extract_booking_intent("I want to book a room")
    print(f"Detected intent: {intent.value}")
    
    # Generate response - should ask for ALL missing info
    response = chat_service.generate_response(
        "I want to book a room",
        intent,
        slots,
        []
    )
    
    print("\nSystem response:")
    print("-" * 40)
    print(response)
    print("-" * 40)


def test_partial_info_provided():
    """Test response when user provides some info"""
    print("\n\n=== Test 2: Partial Information Provided ===")
    print("User: 'I need a meeting room for 5 people'\n")
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    # Extract booking info
    slots = chat_service.extract_booking_slots("I need a meeting room for 5 people", slots)
    print(f"Extracted info: {json.dumps(slots.dict(exclude_none=True), indent=2)}")
    
    # Generate response - should ask for remaining info
    response = chat_service.generate_response(
        "I need a meeting room for 5 people",
        BookingIntent.BOOK_ROOM,
        slots,
        []
    )
    
    print("\nSystem response:")
    print("-" * 40)
    print(response)
    print("-" * 40)


def test_location_and_type_provided():
    """Test when location and room type are provided"""
    print("\n\n=== Test 3: Location and Room Type Provided ===")
    print("User: 'Atlanta meeting room'\n")
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    # Extract booking info
    slots = chat_service.extract_booking_slots("Atlanta meeting room", slots)
    print(f"Extracted info: {json.dumps(slots.dict(exclude_none=True), indent=2)}")
    
    # Generate response - should only ask for capacity, date, time
    response = chat_service.generate_response(
        "Atlanta meeting room",
        BookingIntent.BOOK_ROOM,
        slots,
        []
    )
    
    print("\nSystem response:")
    print("-" * 40)
    print(response)
    print("-" * 40)


def test_sms_formatting():
    """Test that messages are properly formatted for SMS"""
    print("\n\n=== Test 4: SMS Formatting ===")
    
    chat_service = SimpleChatService()
    slots = BookingSlots(room_type="meeting_room", capacity=5)
    
    response = chat_service.generate_response(
        "meeting room for 5 people",
        BookingIntent.BOOK_ROOM,
        slots,
        []
    )
    
    print("SMS Preview:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    
    # Check message length
    print(f"\nMessage length: {len(response)} characters")
    print(f"SMS segments needed: {(len(response) - 1) // 160 + 1}")


def main():
    """Run all tests"""
    print("Testing Improved Messaging System")
    print("=" * 50)
    
    try:
        test_initial_booking_request()
        test_partial_info_provided()
        test_location_and_type_provided()
        test_sms_formatting()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed!")
        print("\nKey improvements:")
        print("1. All missing information is asked at once")
        print("2. Dynamic locations and room types from OfficeRND")
        print("3. Clear formatting for SMS readability")
        print("4. Helpful examples included")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()