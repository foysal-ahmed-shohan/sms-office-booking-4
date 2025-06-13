from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from app.database.models import SMSMessage, User

logger = logging.getLogger(__name__)


class SMSRepository:
    """Repository for SMS message database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(
        self,
        user_id: int,
        direction: str,
        from_number: str,
        to_number: str,
        message_body: str,
        message_sid: Optional[str] = None,
        **kwargs
    ) -> SMSMessage:
        """
        Create a new SMS message record
        
        Args:
            user_id: ID of the user
            direction: 'inbound' or 'outbound'
            from_number: Sender's phone number
            to_number: Recipient's phone number
            message_body: Message content
            message_sid: Twilio message SID
            **kwargs: Additional fields
            
        Returns:
            SMSMessage object
        """
        try:
            logger.info(f"Creating {direction} SMS: from={from_number}, to={to_number}")
            
            # Extract status from kwargs if provided, otherwise use default
            status = kwargs.pop('status', 'received' if direction == 'inbound' else 'sent')
            
            sms = SMSMessage(
                user_id=user_id,
                direction=direction,
                from_number=from_number,
                to_number=to_number,
                message_body=message_body,
                message_sid=message_sid,
                status=status,
                **kwargs
            )
            
            self.db.add(sms)
            self.db.commit()
            self.db.refresh(sms)
            
            logger.debug(f"SMS message created: {sms}")
            return sms
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_message: {str(e)}")
            self.db.rollback()
            raise
    
    def get_by_message_sid(self, message_sid: str) -> Optional[SMSMessage]:
        """Get SMS message by Twilio message SID"""
        try:
            return self.db.query(SMSMessage).filter(
                SMSMessage.message_sid == message_sid
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_message_sid: {str(e)}")
            raise
    
    def get_user_messages(
        self,
        user_id: int,
        direction: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SMSMessage]:
        """Get messages for a specific user"""
        try:
            query = self.db.query(SMSMessage).filter(
                SMSMessage.user_id == user_id
            )
            
            if direction:
                query = query.filter(SMSMessage.direction == direction)
            
            messages = query.order_by(
                SMSMessage.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_messages: {str(e)}")
            raise
    
    def get_conversation(
        self,
        phone_number1: str,
        phone_number2: str,
        limit: int = 50
    ) -> List[SMSMessage]:
        """Get conversation between two phone numbers"""
        try:
            messages = self.db.query(SMSMessage).filter(
                ((SMSMessage.from_number == phone_number1) & (SMSMessage.to_number == phone_number2)) |
                ((SMSMessage.from_number == phone_number2) & (SMSMessage.to_number == phone_number1))
            ).order_by(
                SMSMessage.created_at.desc()
            ).limit(limit).all()
            
            logger.debug(f"Retrieved {len(messages)} messages in conversation")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_conversation: {str(e)}")
            raise
    
    def update_status(
        self,
        message_sid: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[SMSMessage]:
        """Update message status"""
        try:
            sms = self.get_by_message_sid(message_sid)
            if sms:
                sms.status = status
                if error_message:
                    sms.error_message = error_message
                
                self.db.commit()
                self.db.refresh(sms)
                logger.info(f"Updated SMS status: {message_sid} -> {status}")
                return sms
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_status: {str(e)}")
            self.db.rollback()
            raise
    
    def get_recent_messages(
        self,
        hours: int = 24,
        direction: Optional[str] = None
    ) -> List[SMSMessage]:
        """Get messages from the last N hours"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = self.db.query(SMSMessage).filter(
                SMSMessage.created_at >= since
            )
            
            if direction:
                query = query.filter(SMSMessage.direction == direction)
            
            messages = query.order_by(SMSMessage.created_at.desc()).all()
            
            logger.debug(f"Retrieved {len(messages)} messages from last {hours} hours")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_recent_messages: {str(e)}")
            raise
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict:
        """Get SMS statistics"""
        try:
            query = self.db.query(SMSMessage)
            if user_id:
                query = query.filter(SMSMessage.user_id == user_id)
            
            total = query.count()
            inbound = query.filter(SMSMessage.direction == 'inbound').count()
            outbound = query.filter(SMSMessage.direction == 'outbound').count()
            failed = query.filter(SMSMessage.status == 'failed').count()
            
            stats = {
                'total_messages': total,
                'inbound_messages': inbound,
                'outbound_messages': outbound,
                'failed_messages': failed,
                'success_rate': ((total - failed) / total * 100) if total > 0 else 0
            }
            
            logger.debug(f"SMS statistics: {stats}")
            return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_statistics: {str(e)}")
            raise