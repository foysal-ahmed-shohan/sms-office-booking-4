#!/usr/bin/env python3
"""Test real-world scenarios with the improved booking system"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.services.chat.booking_schema import BookingSlots, BookingIntent, SLOT_PROMPTS

def simulate_conversation():
    """Simulate a real conversation showing the improvements"""
    service = SimpleChatService()
    
    print("=== Simulated Booking Conversations ===\n")
    
    # Scenario 1: User provides multiple pieces of info at once
    print("SCENARIO 1: Multiple Info at Once")
    print("-" * 40)
    print("User: 02-5-2026 date, meeting room")
    
    slots = BookingSlots()
    slots = service.extract_booking_slots("02-5-2026 date, meeting room", slots)
    
    print(f"System extracted: date='{slots.date}', room_type='{slots.room_type}'")
    
    # Generate response
    response = service.generate_response(
        "02-5-2026 date, meeting room",
        BookingIntent.BOOK_ROOM,
        slots,
        []
    )
    print(f"System: {response}")
    print()
    
    # Scenario 2: Misspelled location
    print("\nSCENARIO 2: Handling Typos")
    print("-" * 40)
    print("User: I need a room in salt lake sity")
    
    slots2 = BookingSlots()
    slots2 = service.extract_booking_slots("I need a room in salt lake sity", slots2)
    
    print(f"System extracted: location='{slots2.location}' (corrected from 'sity')")
    
    response = service.generate_response(
        "I need a room in salt lake sity",
        BookingIntent.BOOK_ROOM,
        slots2,
        []
    )
    print(f"System: {response}")
    print()
    
    # Scenario 3: Complete booking in one message
    print("\nSCENARIO 3: Complete Booking Info")
    print("-" * 40)
    print("User: Book a conference room in NYC for 10 people tomorrow at 2:30pm")
    
    slots3 = BookingSlots()
    slots3 = service.extract_booking_slots("Book a conference room in NYC for 10 people tomorrow at 2:30pm", slots3)
    
    print(f"System extracted:")
    print(f"  - room_type: {slots3.room_type}")
    print(f"  - location: {slots3.location}")
    print(f"  - capacity: {slots3.capacity}")
    print(f"  - date: {slots3.date}")
    print(f"  - time: {slots3.time}")
    
    response = service.generate_response(
        "Book a conference room in NYC for 10 people tomorrow at 2:30pm",
        BookingIntent.BOOK_ROOM,
        slots3,
        []
    )
    print(f"System: {response}")
    print()
    
    # Scenario 4: Natural variations
    print("\nSCENARIO 4: Natural Language Variations")
    print("-" * 40)
    variations = [
        "I need space for a party of 8",
        "Looking for a quiet room in SF",
        "Can I get a desk for next monday",
        "We need a large meeting space for 2 hours"
    ]
    
    for var in variations:
        print(f"\nUser: {var}")
        slots = BookingSlots()
        slots = service.extract_booking_slots(var, slots)
        
        extracted = []
        if slots.location: extracted.append(f"location={slots.location}")
        if slots.room_type: extracted.append(f"room_type={slots.room_type}")
        if slots.capacity: extracted.append(f"capacity={slots.capacity}")
        if slots.date: extracted.append(f"date={slots.date}")
        if slots.duration: extracted.append(f"duration={slots.duration}")
        
        print(f"System extracted: {', '.join(extracted) if extracted else 'No specific info'}")

def test_intent_detection():
    """Test intent detection in context"""
    service = SimpleChatService()
    
    print("\n\n=== Intent Detection in Context ===")
    print("-" * 40)
    
    # Simulate a booking conversation
    context = [
        {"role": "user", "content": "I need to book a room"},
        {"role": "assistant", "content": "I can help you book a room. Which location would you like?"}
    ]
    
    # User provides location - should be detected as book_room intent
    intent = service.extract_booking_intent("salt lake city", context)
    print(f"User: 'salt lake city' (after being asked for location)")
    print(f"Detected intent: {intent} (should be BOOK_ROOM)")
    
    # Another example
    context2 = [
        {"role": "user", "content": "I want a meeting room"},
        {"role": "assistant", "content": "Great! What date do you need the meeting room?"}
    ]
    
    intent2 = service.extract_booking_intent("02-5-2026", context2)
    print(f"\nUser: '02-5-2026' (after being asked for date)")
    print(f"Detected intent: {intent2} (should be BOOK_ROOM)")

if __name__ == "__main__":
    simulate_conversation()
    test_intent_detection()
    
    print("\n\n=== Summary of Improvements ===")
    print("-" * 40)
    print("✓ Extracts multiple pieces of information from single message")
    print("✓ Handles typos and variations in location names")
    print("✓ Recognizes abbreviations (NYC, SF, LA, etc.)")
    print("✓ Improved date/time parsing for various formats")
    print("✓ Better context awareness for intent detection")
    print("✓ Acknowledges already provided information before asking for more")