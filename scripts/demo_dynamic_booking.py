#!/usr/bin/env python3
"""Demo script showing dynamic booking with OfficeRND integration"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime
from app.config import settings


def send_sms_request(message: str, phone_number: str = "+1234567890"):
    """Send a test SMS request to the API"""
    url = "http://localhost:8000/sms/webhook"
    
    data = {
        "From": phone_number,
        "To": settings.twilio_phone_number,
        "Body": message,
        "MessageSid": f"TEST_{datetime.now().timestamp()}",
        "AccountSid": "AC123456789"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Postman/Demo"
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def demo_booking_flow():
    """Demonstrate a complete booking flow with dynamic data"""
    print("\n" + "=" * 60)
    print("DEMO: Dynamic Booking System with OfficeRND Integration")
    print("=" * 60)
    
    # First, show available locations and room types
    from app.services.officernd_service import officernd_service
    
    print("\n📍 Available Locations (from OfficeRND):")
    locations = officernd_service.get_locations()
    for loc in locations:
        print(f"  • {loc.get('name')} - {loc.get('city')}, {loc.get('state')}")
    
    print("\n🏢 Available Room Types (from OfficeRND):")
    room_types = officernd_service.get_resource_types()
    for rt in room_types:
        print(f"  • {rt.get('title')} ({rt.get('type')})")
    
    print("\n" + "-" * 60)
    print("Starting Booking Conversation...")
    print("-" * 60)
    
    # Simulate conversation
    conversations = [
        {
            "message": "I want to book a meeting room",
            "description": "Initial booking request"
        },
        {
            "message": "Chicago",
            "description": "Invalid location (not in OfficeRND)"
        },
        {
            "message": "Atlanta",
            "description": "Valid location from OfficeRND"
        },
        {
            "message": "conference room",
            "description": "Room type not available in OfficeRND"
        },
        {
            "message": "meeting room",
            "description": "Valid room type from OfficeRND"
        },
        {
            "message": "5 people, tomorrow 2pm-4pm",
            "description": "Multiple booking details"
        }
    ]
    
    for conv in conversations:
        print(f"\n💬 {conv['description']}:")
        print(f"User: \"{conv['message']}\"")
        
        response = send_sms_request(conv['message'])
        
        if "reply" in response:
            bot_message = response["reply"]["message"]
            print(f"Bot: \"{bot_message}\"")
        else:
            print(f"Response: {json.dumps(response, indent=2)}")
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• Dynamic location suggestions from real OfficeRND data")
    print("• Dynamic room type options from real OfficeRND data")
    print("• Validation against actual available locations")
    print("• Validation against actual available room types")
    print("• Intelligent conversation flow with context awareness")
    print("=" * 60)


def main():
    """Run the demo"""
    print("\n🚀 Starting Dynamic Booking Demo...")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ Server is not healthy. Please start the server first.")
            print("Run: uvicorn app.main:app --reload --port 8000")
            return
    except:
        print("❌ Server is not running. Please start the server first.")
        print("Run: uvicorn app.main:app --reload --port 8000")
        return
    
    try:
        demo_booking_flow()
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()