from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.database.base import BaseModel
import logging

logger = logging.getLogger(__name__)


class User(BaseModel):
    """User model to store phone number information"""
    __tablename__ = "users"
    
    # Phone numbers
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    twilio_phone_number = Column(String(20), nullable=True)  # The Twilio number they're messaging
    
    # User details
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Metadata
    country_code = Column(String(5), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    
    # Additional fields for future use
    extra_data = Column(JSON, nullable=True, default=dict)
    notes = Column(Text, nullable=True)
    
    # Relationships
    sms_messages = relationship("SMSMessage", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_phone_twilio', 'phone_number', 'twilio_phone_number'),
        Index('idx_user_active_phone', 'is_active', 'phone_number'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone_number})>"


class SMSMessage(BaseModel):
    """SMS message model to store all messages"""
    __tablename__ = "sms_messages"
    
    # Foreign key to user
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message details
    direction = Column(String(10), nullable=False)  # 'inbound' or 'outbound'
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    message_body = Column(Text, nullable=False)
    
    # Twilio specific fields
    message_sid = Column(String(50), nullable=True, unique=True, index=True)
    account_sid = Column(String(50), nullable=True)
    messaging_service_sid = Column(String(50), nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=True)  # sent, delivered, failed, received
    error_message = Column(Text, nullable=True)
    
    # Additional data
    num_segments = Column(Integer, default=1)
    num_media = Column(Integer, default=0)
    price = Column(String(20), nullable=True)
    price_unit = Column(String(10), nullable=True)
    
    # Extra data for extensibility
    extra_data = Column(JSON, nullable=True, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="sms_messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_sms_user_direction', 'user_id', 'direction'),
        Index('idx_sms_created_direction', 'created_at', 'direction'),
        Index('idx_sms_from_to', 'from_number', 'to_number'),
    )
    
    def __repr__(self):
        return f"<SMSMessage(id={self.id}, direction={self.direction}, from={self.from_number})>"


# Log model creation
logger.info("Database models created: User, SMSMessage")