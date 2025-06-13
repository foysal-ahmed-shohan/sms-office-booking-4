from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class SMSWebhookRequest(BaseModel):
    """Twilio SMS webhook request schema"""
    From: str = Field(..., description="Sender's phone number in E.164 format")
    To: str = Field(..., description="Recipient's phone number (your Twilio number)")
    Body: str = Field(..., description="SMS message content")
    MessageSid: Optional[str] = Field(None, description="Unique message identifier from Twilio")
    AccountSid: Optional[str] = Field(None, description="Twilio account identifier")
    MessagingServiceSid: Optional[str] = Field(None, description="Messaging service identifier")
    NumMedia: Optional[str] = Field("0", description="Number of media attachments")
    
    @validator("From", "To")
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not v:
            raise ValueError("Phone number is required")
        
        # Basic E.164 format validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError(f"Invalid phone number format: {v}")
        
        # Ensure it starts with +
        if not v.startswith("+"):
            v = "+" + v
            
        return v
    
    @validator("Body")
    def validate_body(cls, v):
        """Validate message body"""
        if not v or not v.strip():
            raise ValueError("Message body cannot be empty")
        
        # Limit message length for safety
        if len(v) > 1600:  # SMS limit
            raise ValueError("Message body exceeds SMS length limit")
            
        return v.strip()
    
    class Config:
        # Allow field names to start with capital letters
        populate_by_name = True


class SMSReplyData(BaseModel):
    """SMS reply data structure"""
    message: str = Field(..., description="Reply message content")
    timestamp: str = Field(..., description="Message timestamp")
    sms_sent: bool = Field(default=False, description="Whether SMS was actually sent")
    sms_sending_enabled: bool = Field(..., description="Whether SMS sending is enabled")
    message_sid: Optional[str] = Field(None, description="Twilio message SID if sent")
    reason: Optional[str] = Field(None, description="Reason if SMS was not sent")
    error: Optional[str] = Field(None, description="Error message if any")


class SMSWebhookResponse(BaseModel):
    """Response schema for SMS webhook"""
    status: str = Field(..., description="Response status")
    received: dict = Field(..., description="Received message details")
    reply: SMSReplyData = Field(..., description="Reply message details")
    validation: Optional[dict] = Field(None, description="Validation details")
    

class TestSMSRequest(BaseModel):
    """Request schema for test SMS endpoint"""
    phone_number: str = Field(..., description="Recipient phone number")
    message: str = Field(default="Test message from SMS service", description="Message to send")
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError("Invalid phone number format. Must be in E.164 format")
        
        if not v.startswith("+"):
            v = "+" + v
            
        return v
    
    @validator("message")
    def validate_message(cls, v):
        """Validate message content"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
            
        if len(v) > 1600:
            raise ValueError("Message exceeds SMS length limit")
            
        return v.strip()


class ConfigStatus(BaseModel):
    """Configuration status response"""
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    twilio_client_initialized: bool
    sms_sending_enabled: bool
    signature_validation_enabled: bool
    environment_variables: dict
    twilio_connection: Optional[str] = None
    account_status: Optional[str] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0.0"
    database_status: Optional[str] = None