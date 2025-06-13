#!/usr/bin/env python3
"""Test resource selection with number input"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db
from app.services.chat.conversation_manager import ConversationManager
from app.database.models import User, ConversationState
import logging

# Show INFO level logging to debug
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_resource_selection():
    """Test selecting resource by number"""
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
        print("RESOURCE SELECTION BY NUMBER TEST")
        print("="*70)
        
        # Step 1: Initial request
        print("\n1. User provides booking info:")
        message = "need meeting room for 2 people in atlanta on jan 15 2026 2pm to 3pm"
        print(f"   User: '{message}'")
        
        result = conv_manager.process_message(user, message)
        response, ids = result if isinstance(result, tuple) else (result, None)
        print(f"\nSystem: {response[:200]}...")
        
        # Step 2: Select resource by number
        print("\n\n2. User selects resource by number:")
        print("   User: '2'")
        
        try:
            result = conv_manager.process_message(user, "2")
            response, ids = result if isinstance(result, tuple) else (result, None)
            print(f"\nSystem: {response[:200]}...")
            
            if "is this correct?" in response.lower():
                print("\n✅ Resource selection worked correctly!")
            else:
                print("\n❌ ERROR: Resource selection failed!")
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
    finally:
        # Cleanup
        db.query(ConversationState).filter(ConversationState.user_id == user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_resource_selection()