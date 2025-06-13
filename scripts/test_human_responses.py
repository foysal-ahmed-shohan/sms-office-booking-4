#!/usr/bin/env python3
"""Test human-like conversational responses"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.schemas.booking_schema import BookingSlots, BookingIntent
import json


def print_response(title, user_msg, response):
    """Pretty print a conversation exchange"""
    print(f"\n{title}")
    print("=" * 60)
    print(f"User: \"{user_msg}\"")
    print("-" * 60)
    print("Bot:")
    print(response)
    print("=" * 60)


def test_human_responses():
    """Test various scenarios with human-like responses"""
    chat_service = SimpleChatService()
    
    # Test 1: Initial request
    print_response(
        "TEST 1: User says 'I want to book a room'",
        "I want to book a room",
        chat_service.generate_response(
            "I want to book a room",
            BookingIntent.BOOK_ROOM,
            BookingSlots(),
            []
        )
    )
    
    # Test 2: Partial info - just room type
    slots = BookingSlots(room_type="meeting_room")
    print_response(
        "TEST 2: User specified room type only",
        "I need a meeting room",
        chat_service.generate_response(
            "I need a meeting room",
            BookingIntent.BOOK_ROOM,
            slots,
            []
        )
    )
    
    # Test 3: More info provided
    slots = BookingSlots(room_type="meeting_room", location="Atlanta", capacity=5)
    print_response(
        "TEST 3: User provided location, room type, and capacity",
        "Meeting room in Atlanta for 5 people",
        chat_service.generate_response(
            "Meeting room in Atlanta for 5 people",
            BookingIntent.BOOK_ROOM,
            slots,
            []
        )
    )
    
    # Test 4: Almost complete
    slots = BookingSlots(
        room_type="meeting_room",
        location="Atlanta",
        capacity=5,
        date="tomorrow"
    )
    print_response(
        "TEST 4: Only missing time",
        "Tomorrow",
        chat_service.generate_response(
            "Tomorrow",
            BookingIntent.BOOK_ROOM,
            slots,
            []
        )
    )
    
    # Test 5: Complete booking
    slots = BookingSlots(
        room_type="meeting_room",
        location="Dallas",
        capacity=8,
        date="next Monday",
        time="2:00 PM",
        duration="2 hours"
    )
    print_response(
        "TEST 5: All information complete",
        "2pm for 2 hours",
        chat_service.generate_response(
            "2pm for 2 hours",
            BookingIntent.BOOK_ROOM,
            slots,
            []
        )
    )
    
    # Test 6: Unknown intent
    print_response(
        "TEST 6: Unclear request",
        "Hello",
        chat_service.generate_response(
            "Hello",
            BookingIntent.UNKNOWN,
            BookingSlots(),
            []
        )
    )


def compare_old_vs_new():
    """Show comparison of old robotic vs new human responses"""
    print("\n\n" + "=" * 60)
    print("COMPARISON: OLD vs NEW RESPONSES")
    print("=" * 60)
    
    print("\n📱 When user says: 'I want to book a room'")
    print("\n❌ OLD ROBOTIC RESPONSE:")
    print("-" * 40)
    print("Please provide the following details:\n")
    print("Location: Atlanta, New York, or Dallas")
    print("Room type: Dedicated desk, Hotdesk, or Meeting room")
    print("Number of people")
    print("Date (e.g., tomorrow, Monday, Dec 15)")
    print("Time (e.g., 2pm, 14:00)")
    print("\nExample: Atlanta, meeting room, 5 people, tomorrow 2pm")
    
    print("\n✅ NEW HUMAN RESPONSE:")
    print("-" * 40)
    print("I'd be happy to help you book a space! To find the perfect spot for you, could you tell me:")
    print("")
    print("- Which office location works best for you? We have spaces in Atlanta, Dallas, or New York")
    print("- What type of space do you need? We offer Dedicated desk, Hotdesk, or Meeting room")
    print("- How many people will be joining?")
    print("- When would you like to book? (You can say things like 'tomorrow' or 'next Monday')")
    print("- What time works best for you?")
    print("")
    print("Feel free to tell me everything at once, like 'Atlanta, meeting room for 5 people tomorrow at 2pm'")


def main():
    """Run all tests"""
    print("\nDemonstrating Human-like Conversational Responses")
    print("=" * 60)
    
    try:
        test_human_responses()
        compare_old_vs_new()
        
        print("\n\n✅ Test completed successfully!")
        print("\nKey improvements:")
        print("• Friendly, conversational tone")
        print("• Natural language that feels human")
        print("• Clear but not robotic")
        print("• Helpful without being mechanical")
        print("• Appropriate for SMS communication")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()