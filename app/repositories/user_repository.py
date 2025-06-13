from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
import logging
from app.database.models import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update(self, phone_number: str, twilio_phone_number: Optional[str] = None, **kwargs) -> User:
        """
        Create a new user or update existing one
        
        Args:
            phone_number: User's phone number
            twilio_phone_number: Twilio number they're messaging
            **kwargs: Additional user fields
            
        Returns:
            User object
        """
        try:
            # Check if user exists
            user = self.get_by_phone(phone_number)
            
            if user:
                logger.info(f"Updating existing user: {phone_number}")
                # Update existing user
                if twilio_phone_number:
                    user.twilio_phone_number = twilio_phone_number
                
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                user.is_active = True  # Reactivate if inactive
            else:
                logger.info(f"Creating new user: {phone_number}")
                # Create new user
                user = User(
                    phone_number=phone_number,
                    twilio_phone_number=twilio_phone_number,
                    **kwargs
                )
                self.db.add(user)
            
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"User saved: {user}")
            return user
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_or_update: {str(e)}")
            self.db.rollback()
            raise
    
    def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        try:
            user = self.db.query(User).filter(
                User.phone_number == phone_number
            ).first()
            
            if user:
                logger.debug(f"Found user: {user}")
            else:
                logger.debug(f"User not found: {phone_number}")
                
            return user
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_phone: {str(e)}")
            raise
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_id: {str(e)}")
            raise
    
    def get_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all active users with pagination"""
        try:
            users = self.db.query(User).filter(
                User.is_active == True
            ).limit(limit).offset(offset).all()
            
            logger.debug(f"Retrieved {len(users)} active users")
            return users
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_active_users: {str(e)}")
            raise
    
    def deactivate(self, phone_number: str) -> bool:
        """Deactivate a user (soft delete)"""
        try:
            user = self.get_by_phone(phone_number)
            if user:
                user.is_active = False
                self.db.commit()
                logger.info(f"User deactivated: {phone_number}")
                return True
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in deactivate: {str(e)}")
            self.db.rollback()
            raise
    
    def update_extra_data(self, phone_number: str, extra_data: dict) -> Optional[User]:
        """Update user extra data"""
        try:
            user = self.get_by_phone(phone_number)
            if user:
                if user.extra_data:
                    user.extra_data.update(extra_data)
                else:
                    user.extra_data = extra_data
                
                self.db.commit()
                self.db.refresh(user)
                logger.debug(f"Updated extra data for user: {phone_number}")
                return user
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_extra_data: {str(e)}")
            self.db.rollback()
            raise