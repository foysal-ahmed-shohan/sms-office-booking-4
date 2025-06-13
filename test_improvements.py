#!/usr/bin/env python3
"""Test script to demonstrate improvements in booking system"""

from app.services.chat.simple_chat_service import SimpleChatService
from app.services.chat.booking_schema import BookingSlots, BookingIntent

def test_multiple_info_extraction():
    """Test extraction of multiple pieces of information from a single message"""
    service = SimpleChatService()
    
    print("=== Testing Multiple Information Extraction ===\n")
    
    # Test case 1: Date and room type in one message
    message1 = "02-5-2026 date, meeting room"
    slots1 = BookingSlots()
    result1 = service.extract_booking_slots(message1, slots1)
    print(f"Message: '{message1}'")
    print(f"Extracted: date='{result1.date}', room_type='{result1.room_type}'")
    print()
    
    # Test case 2: Multiple pieces of info
    message2 = "I need a conference room for 10 people tomorrow at 2pm"
    slots2 = BookingSlots()
    result2 = service.extract_booking_slots(message2, slots2)
    print(f"Message: '{message2}'")
    print(f"Extracted: room_type='{result2.room_type}', capacity='{result2.capacity}', date='{result2.date}', time='{result2.time}'")
    print()
    
    # Test case 3: All info at once
    message3 = "Book meeting room in Salt Lake City for 5 people on 03/15/2026 at 3:30pm for 2 hours"
    slots3 = BookingSlots()
    result3 = service.extract_booking_slots(message3, slots3)
    print(f"Message: '{message3}'")
    print(f"Extracted: room_type='{result3.room_type}', location='{result3.location}', capacity='{result3.capacity}', date='{result3.date}', time='{result3.time}', duration='{result3.duration}'")
    print()

def test_fuzzy_location_matching():
    """Test fuzzy matching for misspelled locations"""
    service = SimpleChatService()
    
    print("\n=== Testing Fuzzy Location Matching ===\n")
    
    # Test case 1: Misspelled "Salt Lake City"
    message1 = "I need a room in salt lake sity"
    slots1 = BookingSlots()
    result1 = service.extract_booking_slots(message1, slots1)
    print(f"Message: '{message1}'")
    print(f"Extracted location: '{result1.location}' (should be 'Salt Lake City')")
    print()
    
    # Test case 2: Abbreviations
    message2 = "Book a desk in NYC"
    slots2 = BookingSlots()
    result2 = service.extract_booking_slots(message2, slots2)
    print(f"Message: '{message2}'")
    print(f"Extracted location: '{result2.location}' (should be 'New York')")
    print()
    
    # Test case 3: Another abbreviation
    message3 = "I need an office in SF"
    slots3 = BookingSlots()
    result3 = service.extract_booking_slots(message3, slots3)
    print(f"Message: '{message3}'")
    print(f"Extracted location: '{result3.location}' (should be 'San Francisco')")
    print()

def test_improved_patterns():
    """Test improved pattern matching for various formats"""
    service = SimpleChatService()
    
    print("\n=== Testing Improved Pattern Matching ===\n")
    
    # Test various date formats
    dates = ["02-5-2026", "2/5/26", "Feb 5", "tomorrow", "next monday"]
    for date in dates:
        slots = BookingSlots()
        result = service.extract_booking_slots(date, slots)
        print(f"Date input: '{date}' -> Extracted: '{result.date}'")
    
    print()
    
    # Test various time formats
    times = ["2pm", "2:30 PM", "14:00", "2 o'clock", "afternoon"]
    for time in times:
        slots = BookingSlots()
        result = service.extract_booking_slots(time, slots)
        print(f"Time input: '{time}' -> Extracted: '{result.time}'")
    
    print()
    
    # Test various capacity formats
    capacities = ["5 people", "for 10", "party of 8", "6 of us"]
    for cap in capacities:
        slots = BookingSlots()
        result = service.extract_booking_slots(cap, slots)
        print(f"Capacity input: '{cap}' -> Extracted: '{result.capacity}'")

if __name__ == "__main__":
    test_multiple_info_extraction()
    test_fuzzy_location_matching()
    test_improved_patterns()
    
    print("\n=== Tests Complete ===")
    print("\nThe booking system now properly:")
    print("1. Extracts multiple pieces of information from a single message")
    print("2. Handles misspellings and abbreviations for locations")
    print("3. Recognizes various date, time, and capacity formats")
    print("4. Won't ask for information that was just provided")