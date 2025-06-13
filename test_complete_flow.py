#!/usr/bin/env python3
"""Test complete booking flow with resource selection"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
import logging

# Show INFO level logging to debug the issue
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_complete_flow():
    """Test the complete booking flow"""
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
        print("COMPLETE BOOKING FLOW TEST")
        print("="*70)
        
        # Step 1: Initial request
        print("\n1. User provides all info at once:")
        message = "need space for atlanta, 2 people, meeting room, 4 dec 2025 1pm to 2pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        response = conv_manager.process_message(user, message)
        print(f"System:\n{response}")
        
        # Check for resource display
        if "please choose a specific" not in response.lower():
            print("\n❌ ERROR: Resources not shown!")
            return
        
        print("\n✅ Resources shown successfully!")
        
        # Step 2: Select resource
        print("\n2. User selects a resource:")
        print("   User: '2'")  # Select by number
        print("-"*70)
        
        # Check conversation state before processing
        conv_state = db.query(ConversationState).filter(ConversationState.user_id == user.id).first()
        if conv_state and conv_state.booking_data:
            print(f"DEBUG: Available resources in booking_data: {'_available_resources' in conv_state.booking_data}")
            if '_available_resources' in conv_state.booking_data:
                print(f"DEBUG: Number of resources: {len(conv_state.booking_data['_available_resources'])}")
        
        response = conv_manager.process_message(user, "2")
        print(f"System:\n{response}")
        
        # Check for confirmation request
        if "is this correct?" not in response.lower():
            print("\n❌ ERROR: Confirmation not requested!")
            return
            
        print("\n✅ Confirmation requested!")
        
        # Step 3: Confirm booking
        print("\n3. User confirms:")
        print("   User: 'yes'")
        print("-"*70)
        
        response = conv_manager.process_message(user, "yes")
        print(f"System:\n{response}")
        
        # Check for booking confirmation
        if "your booking id is:" in response.lower() and "resource id:" in response.lower():
            print("\n✅ Booking confirmed with resource ID!")
        else:
            print("\n❌ ERROR: Booking confirmation incomplete!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_complete_flow()