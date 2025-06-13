"""Conversation manager for handling chat state and context"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timedelta

from app.database.models import User, ConversationState
from app.services.chat.booking_schema import BookingIntent, BookingSlots
from app.services.chat.openai_service import OpenAIService
from app.services.chat.simple_chat_service import SimpleChatService

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and context for users"""
    
    def __init__(self, db: Session):
        self.db = db
        self.chat_service = None
        
        # Try to use OpenAI service, fallback to simple service
        try:
            self.chat_service = OpenAIService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI service: {str(e)}")
            logger.info("Falling back to simple chat service")
            self.chat_service = SimpleChatService()
        
        self.max_history_messages = 10  # Keep last 10 messages for context
        
    def process_message(self, user: User, message: str) -> str:
        """Process incoming message and generate response"""
        try:
            # Get or create conversation state
            conv_state = self._get_or_create_conversation(user)
            
            # Add message to history BEFORE processing
            self._add_to_history(conv_state, "user", message)
            
            # Commit the history update immediately to ensure persistence
            self.db.commit()
            
            # Extract intent with conversation history
            intent = self.chat_service.extract_booking_intent(
                message, 
                conv_state.conversation_history
            )
            logger.info(f"Detected intent: {intent}")
            
            # If we have an active booking conversation and intent is unknown,
            # assume it's continuing the booking flow
            if (conv_state.current_intent == 'book_room' and 
                intent == BookingIntent.UNKNOWN and 
                conv_state.booking_data):
                intent = BookingIntent.BOOK_ROOM
                logger.info("Continuing booking flow based on conversation context")
            
            # Update conversation intent if needed
            if intent != BookingIntent.UNKNOWN:
                conv_state.current_intent = intent.value
            
            # Handle based on intent
            if intent == BookingIntent.BOOK_ROOM or conv_state.current_intent == 'book_room':
                response = self._handle_booking_flow(conv_state, message)
            else:
                # For other intents, generate response
                slots = BookingSlots(**(conv_state.booking_data or {}))
                response = self.chat_service.generate_response(
                    message, intent, slots, conv_state.conversation_history
                )
                
                # Reset booking data for non-booking intents
                if intent != BookingIntent.BOOK_ROOM:
                    conv_state.booking_data = {}
            
            # Add response to history
            self._add_to_history(conv_state, "assistant", response)
            
            # Update last interaction time
            conv_state.last_interaction = datetime.utcnow()
            
            # Save conversation state
            self.db.commit()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.db.rollback()
            return "I apologize, but I'm having trouble processing your request. Please try again."
    
    def _get_or_create_conversation(self, user: User) -> ConversationState:
        """Get existing or create new conversation state"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.user_id == user.id
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(
                user_id=user.id,
                conversation_history=[],
                booking_data={},
                state='active'
            )
            self.db.add(conv_state)
            self.db.commit()
            logger.info(f"Created new conversation state for user {user.id}")
        else:
            # Check if conversation is stale (older than 30 minutes)
            if conv_state.last_interaction:
                time_diff = datetime.utcnow() - conv_state.last_interaction.replace(tzinfo=None)
                if time_diff > timedelta(minutes=30):
                    # Reset conversation
                    conv_state.conversation_history = []
                    conv_state.booking_data = {}
                    conv_state.current_intent = None
                    logger.info(f"Reset stale conversation for user {user.id}")
        
        return conv_state
    
    def _handle_booking_flow(self, conv_state: ConversationState, message: str) -> str:
        """Handle the booking conversation flow"""
        # Get current booking slots
        current_slots = BookingSlots(**(conv_state.booking_data or {}))
        
        # Log what we had before extraction
        before_extraction = current_slots.dict(exclude_none=True)
        logger.info(f"Slots before extraction: {before_extraction}")
        
        # Extract information from message
        updated_slots = self.chat_service.extract_booking_slots(message, current_slots)
        
        # Log what we have after extraction
        after_extraction = updated_slots.dict(exclude_none=True)
        logger.info(f"Slots after extraction: {after_extraction}")
        
        # Check what new information was extracted
        new_info = {}
        for key, value in after_extraction.items():
            if key not in before_extraction or before_extraction[key] != value:
                new_info[key] = value
        
        if new_info:
            logger.info(f"New information extracted: {new_info}")
        
        # Update booking data - create new dict to ensure SQLAlchemy detects change
        conv_state.booking_data = updated_slots.dict(exclude_none=True)
        
        # Mark as modified explicitly
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conv_state, 'booking_data')
        
        # Generate response based on what's missing
        response = self.chat_service.generate_response(
            message,
            BookingIntent.BOOK_ROOM,
            updated_slots,
            conv_state.conversation_history
        )
        
        # If booking is complete, mark conversation as completed
        if updated_slots.is_complete():
            conv_state.state = 'completed'
            # In future, this is where we'd call OfficeRND API
            logger.info(f"Booking completed for user {conv_state.user_id}: {updated_slots.to_summary()}")
        
        return response
    
    def _add_to_history(self, conv_state: ConversationState, role: str, content: str):
        """Add message to conversation history"""
        if not isinstance(conv_state.conversation_history, list):
            conv_state.conversation_history = []
        
        # Create a new list to ensure SQLAlchemy detects the change
        history = list(conv_state.conversation_history)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last N messages
        if len(history) > self.max_history_messages:
            history = history[-self.max_history_messages:]
        
        # Assign back to trigger SQLAlchemy change detection
        conv_state.conversation_history = history
        
        # Mark the object as modified explicitly
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conv_state, 'conversation_history')
    
    def get_conversation_summary(self, user_id: int) -> Optional[Dict]:
        """Get summary of current conversation state"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.user_id == user_id
        ).first()
        
        if not conv_state:
            return None
        
        slots = BookingSlots(**(conv_state.booking_data or {}))
        
        return {
            "current_intent": conv_state.current_intent,
            "state": conv_state.state,
            "booking_summary": slots.to_summary(),
            "missing_info": slots.missing_slots(),
            "last_interaction": conv_state.last_interaction.isoformat() if conv_state.last_interaction else None,
            "message_count": len(conv_state.conversation_history)
        }