#!/usr/bin/env python3
"""Test member/company lookup and creation flow"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
from app.services.officernd_service import officernd_service
import logging

# Show INFO level logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_member_flow():
    """Test the complete booking flow with member check"""
    db = next(get_db())
    
    try:
        # Test with a phone number that might exist as member/company
        test_phone = "+1234567890"  # Change this to test different scenarios
        
        # Setup user
        user = db.query(User).filter(User.phone_number == test_phone).first()
        if not user:
            user = User(phone_number=test_phone, twilio_phone_number="+10987654321", is_active=True)
            db.add(user)
            db.commit()
        
        # Clear conversation
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        
        conv_manager = ConversationManager(db)
        
        print("\n" + "="*70)
        print("MEMBER/COMPANY CHECK TEST")
        print("="*70)
        
        # First check if member/company exists
        print(f"\n1. Checking if phone {test_phone} exists in OfficeRND...")
        member_info = officernd_service.find_member_or_company_by_phone(test_phone)
        
        if member_info:
            print(f"✅ Found existing {member_info['type']}: {member_info['name']} (ID: {member_info['id']})")
        else:
            print("❌ No existing member/company found - will create new member on booking")
        
        # Step 2: Complete booking flow
        print("\n2. User provides all info:")
        message = "need meeting room for 2 people in atlanta on dec 15 2025 3pm to 4pm"
        print(f"   User: '{message}'")
        print("-"*70)
        
        response = conv_manager.process_message(user, message)
        print(f"System:\n{response}")
        
        # Step 3: Select resource
        print("\n3. User selects resource:")
        print("   User: '1'")
        print("-"*70)
        
        response = conv_manager.process_message(user, "1")
        print(f"System:\n{response}")
        
        # Step 4: Confirm booking
        print("\n4. User confirms:")
        print("   User: 'yes'")
        print("-"*70)
        
        response = conv_manager.process_message(user, "yes")
        print(f"System:\n{response}")
        
        # Check for member/company ID in response
        if "member id:" in response.lower() or "company id:" in response.lower():
            print("\n✅ Member/Company ID included in confirmation!")
        else:
            print("\n❌ ERROR: Member/Company ID not shown!")
            
        if "resource id:" in response.lower():
            print("✅ Resource ID included!")
        else:
            print("❌ ERROR: Resource ID not shown!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_member_flow()