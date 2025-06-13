#!/usr/bin/env python3
"""Test the chat system locally"""
import logging
from app.database.connection import get_db_context
from app.database.models import User
from app.repositories.user_repository import UserRepository
from app.services.chat.conversation_manager import ConversationManager
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chat():
    """Test the chat system with sample conversations"""
    
    # Test messages
    test_conversations = [
        # Conversation 1: Complete booking
        [
            "I want to book a meeting room",
            "Salt Lake City, for 5 people",
            "Tomorrow at 2 PM for 2 hours"
        ],
        # Conversation 2: Partial information
        [
            "I need a conference room",
            "In New York",
            "For next Monday"
        ],
        # Conversation 3: Different intent
        [
            "What types of rooms do you have?",
            "I want to book a meeting room in Chicago"
        ]
    ]
    
    with get_db_context() as db:
        # Create or get test user
        user_repo = UserRepository(db)
        test_phone = "+1234567890"
        user = user_repo.create_or_update(test_phone, twilio_phone_number="+0987654321")
        
        # Create conversation manager
        conv_manager = ConversationManager(db)
        
        print("\n" + "="*60)
        print("TESTING CHAT SYSTEM")
        print("="*60)
        
        for conv_num, messages in enumerate(test_conversations, 1):
            print(f"\n--- Conversation {conv_num} ---")
            
            # Reset conversation for new test
            from app.repositories.conversation_repository import ConversationRepository
            conv_repo = ConversationRepository(db)
            conv_repo.reset(user.id)
            
            for msg in messages:
                print(f"\nUSER: {msg}")
                
                try:
                    response = conv_manager.process_message(user, msg)
                    print(f"ASSISTANT: {response}")
                    
                    # Show conversation state
                    summary = conv_manager.get_conversation_summary(user.id)
                    if summary:
                        print(f"\n[State: {summary['state']}, Intent: {summary['current_intent']}]")
                        if summary['missing_info']:
                            print(f"[Missing: {', '.join(summary['missing_info'])}]")
                except Exception as e:
                    print(f"ERROR: {str(e)}")
                    logger.error(f"Test error: {str(e)}", exc_info=True)
        
        print("\n" + "="*60)
        print("CHAT SYSTEM TEST COMPLETE")
        print("="*60)


def interactive_chat():
    """Interactive chat mode for testing"""
    print("\n" + "="*60)
    print("INTERACTIVE CHAT MODE")
    print("Type 'quit' to exit")
    print("="*60 + "\n")
    
    with get_db_context() as db:
        # Create test user
        user_repo = UserRepository(db)
        test_phone = "+1234567890"
        user = user_repo.create_or_update(test_phone, twilio_phone_number="+0987654321")
        
        # Create conversation manager
        conv_manager = ConversationManager(db)
        
        while True:
            try:
                message = input("\nYOU: ").strip()
                
                if message.lower() in ['quit', 'exit', 'bye']:
                    print("ASSISTANT: Goodbye! Thank you for using our booking service.")
                    break
                
                if not message:
                    continue
                
                response = conv_manager.process_message(user, message)
                print(f"ASSISTANT: {response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"ERROR: {str(e)}")
                logger.error(f"Chat error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_chat()
    else:
        test_chat()