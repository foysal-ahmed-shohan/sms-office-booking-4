#!/usr/bin/env python3
"""Test that IDs are returned in separate field"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
import json

def test_ids_response():
    """Test the IDs response structure"""
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
        print("IDS RESPONSE STRUCTURE TEST")
        print("="*70)
        
        # Step 1: Initial request
        print("\n1. User provides all info:")
        message = "need meeting room for 2 people in atlanta on dec 20 2025 4pm to 5pm"
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"Response: {response[:100]}...")
        print(f"IDs: {ids}")
        
        # Step 2: Select resource
        print("\n2. User selects resource:")
        result = conv_manager.process_message(user, "1")
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"Response: {response[:100]}...")
        print(f"IDs: {ids}")
        
        # Step 3: Confirm booking
        print("\n3. User confirms:")
        result = conv_manager.process_message(user, "yes")
        response, ids = result if isinstance(result, tuple) else (result, None)
        
        print(f"\n=== FINAL RESPONSE ===")
        print(f"Message:\n{response}")
        
        print(f"\n=== ALL REQUIRED IDS ===")
        if ids:
            print(json.dumps(ids, indent=2))
            
            # Verify all expected IDs are present
            expected_ids = ['booking_id', 'location_id', 'resource_type_id', 'resource_id', 'resource_name']
            for id_name in expected_ids:
                if id_name in ids and ids[id_name]:
                    print(f"✅ {id_name}: {ids[id_name]}")
                else:
                    print(f"❌ {id_name}: Missing!")
                    
            # Check for member/company ID
            if 'member_id' in ids:
                print(f"✅ member_id: {ids['member_id']}")
            elif 'company_id' in ids:
                print(f"✅ company_id: {ids['company_id']}")
            else:
                print("❌ No member_id or company_id found!")
        else:
            print("❌ No IDs returned!")
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_ids_response()