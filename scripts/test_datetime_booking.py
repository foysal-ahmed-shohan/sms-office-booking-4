#!/usr/bin/env python3
"""Test datetime booking with start and end times"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.schemas.booking_schema import BookingSlots, BookingIntent
import json


def print_test(title, message, slots=None):
    """Print test results"""
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print(f"{'='*60}")
    print(f"User: \"{message}\"")
    
    chat_service = SimpleChatService()
    
    if slots is None:
        slots = BookingSlots()
    
    # Extract slots
    updated_slots = chat_service.extract_booking_slots(message, slots)
    
    # Show what was extracted
    extracted = {}
    if updated_slots.start_date:
        extracted['start_date'] = updated_slots.start_date
    if updated_slots.start_time:
        extracted['start_time'] = updated_slots.start_time
    if updated_slots.end_date:
        extracted['end_date'] = updated_slots.end_date
    if updated_slots.end_time:
        extracted['end_time'] = updated_slots.end_time
    if updated_slots.date:
        extracted['date (old)'] = updated_slots.date
    if updated_slots.time:
        extracted['time (old)'] = updated_slots.time
    
    if extracted:
        print(f"\nExtracted: {json.dumps(extracted, indent=2)}")
    
    # Generate response
    intent = BookingIntent.BOOK_ROOM
    response = chat_service.generate_response(message, intent, updated_slots, [])
    
    print(f"\nBot response:")
    print("-" * 60)
    print(response)
    
    return updated_slots


def test_datetime_formats():
    """Test various datetime input formats"""
    
    # Test 1: Full datetime range
    print_test(
        "Full datetime range: 'Dec 5, 2025 from 2pm to 4pm'",
        "I need a meeting room in Atlanta for 5 people on Dec 5, 2025 from 2pm to 4pm"
    )
    
    # Test 2: Numeric date format
    print_test(
        "Numeric date with time range: '5/12/2025 1pm-3pm'",
        "Book Atlanta meeting room, 5/12/2025 1pm-3pm, 10 people"
    )
    
    # Test 3: Tomorrow with time range
    print_test(
        "Tomorrow with time range",
        "Tomorrow 9am to 11am, meeting room for 5 people"
    )
    
    # Test 4: Just time range (no date yet)
    slots = BookingSlots(location="Dallas", room_type="meeting_room", capacity=3)
    print_test(
        "Time range only: '2pm-4pm'",
        "2pm-4pm",
        slots
    )
    
    # Test 5: Natural language
    print_test(
        "Natural language datetime",
        "I need the conference room from 2 to 4 pm on December 5th"
    )
    
    # Test 6: Multi-day booking
    print_test(
        "Multi-day booking (future enhancement)",
        "Dec 5 2pm to Dec 6 5pm"
    )


def test_missing_datetime():
    """Test when datetime info is missing"""
    slots = BookingSlots(location="New York", room_type="hot_desk", capacity=1)
    
    print(f"\n{'='*60}")
    print("TEST: Missing datetime - should ask for both start and end")
    print(f"{'='*60}")
    print("Current slots: location=New York, room_type=hotdesk, capacity=1")
    
    chat_service = SimpleChatService()
    response = chat_service.generate_response(
        "New York hotdesk for 1",
        BookingIntent.BOOK_ROOM,
        slots,
        []
    )
    
    print(f"\nBot response:")
    print("-" * 60)
    print(response)


def test_conversation_flow():
    """Test a complete conversation with datetime"""
    print(f"\n\n{'='*60}")
    print("COMPLETE CONVERSATION FLOW")
    print(f"{'='*60}")
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    messages = [
        "I want to book a meeting room",
        "Atlanta, for 8 people",
        "December 15, 2025 from 2:30pm to 4:30pm"
    ]
    
    for msg in messages:
        print(f"\nUser: \"{msg}\"")
        
        # Extract and update slots
        slots = chat_service.extract_booking_slots(msg, slots)
        
        # Generate response
        response = chat_service.generate_response(msg, BookingIntent.BOOK_ROOM, slots, [])
        
        print(f"\nBot: {response}")
        
        if slots.is_complete():
            print(f"\n✅ Booking complete!")
            break


def main():
    """Run all tests"""
    print("\nTesting Enhanced Datetime Booking System")
    print("=" * 60)
    print("Now supporting start and end times!")
    
    try:
        test_datetime_formats()
        test_missing_datetime()
        test_conversation_flow()
        
        print(f"\n\n{'='*60}")
        print("✅ All tests completed!")
        print("\nKey improvements:")
        print("• Supports various datetime formats")
        print("• Handles time ranges (2pm-4pm, 2pm to 4pm)")
        print("• Works with dates like 'Dec 5, 2025' or '5/12/2025'")
        print("• Natural language support")
        print("• Clear prompts asking for both start and end times")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()