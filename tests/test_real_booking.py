#!/usr/bin/env python3
"""Test real booking creation with OfficeRND"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
from app.services.officernd_service import officernd_service
import json
import logging

# Show INFO level logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_real_booking():
    """Test creating a real booking in OfficeRND"""
    db = next(get_db())
    
    try:
        # Setup user
        user = db.query(User).filter(User.phone_number == "+1234567890").first()
        if not user:
            user = User(phone_number="+1234567890", twilio_phone_number="+10987654321", is_active=True)
            db.add(user)
            db.commit()
        
        # Clear conversation
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        
        conv_manager = ConversationManager(db)
        
        print("\n" + "="*70)
        print("REAL BOOKING TEST")
        print("="*70)
        
        # Step 1: Initial request
        print("\n1. User provides booking info:")
        message = "need meeting room for 2 people in atlanta on dec 30 2025 3pm to 4pm"
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"Response: {response[:100]}...")
        
        # Step 2: Select resource
        print("\n2. User selects resource:")
        result = conv_manager.process_message(user, "1")  # Select first resource
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"Response: {response[:100]}...")
        
        # Step 3: Confirm booking
        print("\n3. User confirms (REAL BOOKING WILL BE CREATED):")
        result = conv_manager.process_message(user, "yes")
        response, ids = result if isinstance(result, tuple) else (result, None)
        
        print(f"\n=== BOOKING RESPONSE ===")
        print(response)
        
        if ids:
            print(f"\n=== BOOKING IDS ===")
            print(json.dumps(ids, indent=2))
            
            # Verify booking was created
            if 'booking_id' in ids and ids['booking_id']:
                print(f"\n✅ Booking created successfully!")
                print(f"   Booking ID: {ids['booking_id']}")
                print(f"   Reference: {ids.get('booking_reference', 'N/A')}")
                
                # Check if we can retrieve the booking
                bookings = officernd_service.get_bookings()
                booking_found = any(b['_id'] == ids['booking_id'] for b in bookings)
                if booking_found:
                    print("✅ Booking verified in OfficeRND!")
                else:
                    print("❌ Could not find booking in OfficeRND")
            else:
                print("\n❌ No booking ID returned!")
        else:
            print("\n❌ No IDs returned!")
            
        # Test conflict scenario
        print("\n" + "="*70)
        print("TESTING BOOKING CONFLICT")
        print("="*70)
        
        # Clear conversation
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        
        # Try to book same time again
        print("\n4. Trying to book same time slot again:")
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        
        result = conv_manager.process_message(user, "1")  # Select first resource
        response, ids = result if isinstance(result, tuple) else (result, None)
        
        result = conv_manager.process_message(user, "yes")
        response, ids = result if isinstance(result, tuple) else (result, None)
        
        print(f"\nConflict Response: {response}")
        
        if "not available" in response.lower():
            print("\n✅ Conflict detection working correctly!")
        else:
            print("\n❌ Conflict not detected!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This test will create REAL bookings in OfficeRND!")
    print("Press Ctrl+C to cancel or Enter to continue...")
    input()
    test_real_booking()