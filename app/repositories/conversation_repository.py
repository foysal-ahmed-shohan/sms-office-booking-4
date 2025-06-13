"""Repository for conversation state database operations"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import logging
from app.database.models import ConversationState

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for ConversationState database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> Optional[ConversationState]:
        """Get conversation state by user ID"""
        try:
            return self.db.query(ConversationState).filter(
                ConversationState.user_id == user_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_user_id: {str(e)}")
            raise
    
    def create(self, user_id: int) -> ConversationState:
        """Create new conversation state"""
        try:
            conv_state = ConversationState(
                user_id=user_id,
                conversation_history=[],
                booking_data={},
                state='active'
            )
            self.db.add(conv_state)
            self.db.commit()
            self.db.refresh(conv_state)
            logger.info(f"Created conversation state for user {user_id}")
            return conv_state
        except SQLAlchemyError as e:
            logger.error(f"Database error in create: {str(e)}")
            self.db.rollback()
            raise
    
    def update(self, conv_state: ConversationState) -> ConversationState:
        """Update conversation state"""
        try:
            self.db.commit()
            self.db.refresh(conv_state)
            return conv_state
        except SQLAlchemyError as e:
            logger.error(f"Database error in update: {str(e)}")
            self.db.rollback()
            raise
    
    def reset(self, user_id: int) -> Optional[ConversationState]:
        """Reset conversation state for a user"""
        try:
            conv_state = self.get_by_user_id(user_id)
            if conv_state:
                conv_state.conversation_history = []
                conv_state.booking_data = {}
                conv_state.current_intent = None
                conv_state.state = 'active'
                self.db.commit()
                logger.info(f"Reset conversation state for user {user_id}")
            return conv_state
        except SQLAlchemyError as e:
            logger.error(f"Database error in reset: {str(e)}")
            self.db.rollback()
            raise