#!/usr/bin/env python3
"""Demo final booking system with all improvements"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chat.simple_chat_service import SimpleChatService
from app.schemas.booking_schema import BookingSlots, BookingIntent
from app.services.officernd_service import officernd_service


def print_conversation(user_msg, bot_response):
    """Print a conversation exchange"""
    print(f"\n👤 User: \"{user_msg}\"")
    print(f"\n🤖 Bot:")
    print("-" * 60)
    print(bot_response)
    print("-" * 60)


def demo_complete_flow():
    """Demonstrate the complete booking flow"""
    print("\n" + "=" * 70)
    print("OFFICERND INTELLIGENT BOOKING ASSISTANT - FINAL DEMO")
    print("=" * 70)
    
    # Show available options from OfficeRND
    print("\n📍 Available Locations (from OfficeRND):")
    locations = officernd_service.get_locations()
    for loc in locations:
        print(f"   • {loc.get('name')} - {loc.get('city')}, {loc.get('state')}")
    
    print("\n🏢 Available Spaces (from OfficeRND):")
    room_types = officernd_service.get_resource_types()
    for rt in room_types:
        print(f"   • {rt.get('title')}")
    
    print("\n" + "=" * 70)
    print("CONVERSATION DEMO")
    print("=" * 70)
    
    chat_service = SimpleChatService()
    slots = BookingSlots()
    
    # Conversation 1: Initial request
    user_msg = "I want to book a room"
    intent = chat_service.extract_booking_intent(user_msg)
    response = chat_service.generate_response(user_msg, intent, slots, [])
    print_conversation(user_msg, response)
    
    # Conversation 2: Provide some info with datetime
    user_msg = "I need a meeting room in Atlanta for 10 people on December 15, 2025 from 2:30pm to 4:30pm"
    slots = chat_service.extract_booking_slots(user_msg, slots)
    response = chat_service.generate_response(user_msg, BookingIntent.BOOK_ROOM, slots, [])
    print_conversation(user_msg, response)
    
    print("\n✅ Booking Complete! All information captured in one message.")
    
    # Show another example
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Step-by-step booking")
    print("=" * 70)
    
    slots = BookingSlots()
    
    # Step 1
    user_msg = "Meeting room for 5 people"
    slots = chat_service.extract_booking_slots(user_msg, slots)
    response = chat_service.generate_response(user_msg, BookingIntent.BOOK_ROOM, slots, [])
    print_conversation(user_msg, response)
    
    # Step 2
    user_msg = "Dallas, tomorrow 1pm to 3pm"
    slots = chat_service.extract_booking_slots(user_msg, slots)
    response = chat_service.generate_response(user_msg, BookingIntent.BOOK_ROOM, slots, [])
    print_conversation(user_msg, response)
    
    print("\n✅ Booking Complete! Information gathered in two messages.")
    
    # Show datetime format examples
    print("\n\n" + "=" * 70)
    print("SUPPORTED DATETIME FORMATS")
    print("=" * 70)
    print("\n✅ Accepted formats:")
    print("   • December 15, 2025 from 2pm to 4pm")
    print("   • Dec 15 2pm-4pm")
    print("   • 12/15/2025 1:30pm to 3:30pm")
    print("   • Tomorrow 9am-11am")
    print("   • Next Monday from 2 to 4 pm")
    print("   • 5-12-2025 14:00-16:00")
    
    print("\n📝 Key features:")
    print("   • Both start AND end times required")
    print("   • Natural language understanding")
    print("   • Multiple format support")
    print("   • Clear, friendly prompts")


def main():
    """Run the demo"""
    print("\n🚀 Starting Final Booking System Demo")
    
    try:
        demo_complete_flow()
        
        print("\n\n" + "=" * 70)
        print("✅ DEMO COMPLETE!")
        print("\nSystem Features:")
        print("• Dynamic locations from OfficeRND API")
        print("• Dynamic room types from OfficeRND API")
        print("• Start and end time requirements")
        print("• Human-like conversational responses")
        print("• Multiple datetime format support")
        print("• All information can be provided at once or step-by-step")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()