from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from twilio.request_validator import RequestValidator
import logging
from typing import Optional, Dict, Tuple
from app.config import settings


logger = logging.getLogger(__name__)


class TwilioService:
    """Service class for Twilio operations"""
    
    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.phone_number = settings.twilio_phone_number
        self.client: Optional[Client] = None
        self.validator: Optional[RequestValidator] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Twilio client and validator"""
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.validator = RequestValidator(self.auth_token)
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            self.client = None
            self.validator = None
    
    def validate_request(
        self, 
        url: str, 
        params: Dict[str, str], 
        signature: str
    ) -> bool:
        """
        Validate Twilio request signature
        
        Args:
            url: The full URL of the request
            params: The request parameters
            signature: The X-Twilio-Signature header value
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not settings.validate_twilio_signature:
            logger.info("Twilio signature validation is disabled")
            return True
            
        if not self.validator:
            logger.warning("Twilio validator not initialized, skipping validation")
            return True
            
        try:
            is_valid = self.validator.validate(url, params, signature)
            if is_valid:
                logger.info("Twilio signature validation passed")
            else:
                logger.warning("Twilio signature validation failed")
            return is_valid
        except Exception as e:
            logger.error(f"Error during signature validation: {str(e)}")
            # If validation is enabled but fails, reject the request
            return False
    
    def send_sms(
        self, 
        to_number: str, 
        message: str, 
        from_number: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send SMS message via Twilio
        
        Args:
            to_number: Recipient phone number
            message: Message content
            from_number: Sender phone number (uses default if not provided)
            
        Returns:
            Tuple of (success, message_sid, error_message)
        """
        logger.debug(f"send_sms called - to: {to_number}, message_length: {len(message)}")
        
        if not settings.enable_sms_sending:
            logger.info("SMS sending is disabled, skipping actual send")
            logger.debug(f"Would have sent: '{message[:50]}...' to {to_number}")
            return True, None, "SMS sending disabled"
            
        if not self.client:
            error_msg = "Twilio client not initialized"
            logger.error(error_msg)
            return False, None, error_msg
            
        try:
            from_number = from_number or self.phone_number
            logger.info(f"Sending SMS from {from_number} to {to_number}")
            logger.debug(f"Message content: {message}")
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully. SID: {message_obj.sid}")
            logger.debug(f"Message status: {message_obj.status}, Price: {message_obj.price}")
            return True, message_obj.sid, None
            
        except TwilioException as e:
            error_msg = f"Twilio error: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Twilio error details: {e.__dict__}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error sending SMS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
    
    def test_connection(self) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Test Twilio connection and account status
        
        Returns:
            Tuple of (success, account_info)
        """
        if not self.client:
            return False, {"error": "Client not initialized"}
            
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return True, {
                "status": account.status,
                "friendly_name": account.friendly_name,
                "type": account.type
            }
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_phone_number_info(self, phone_number: str) -> Optional[Dict[str, str]]:
        """
        Get information about a phone number
        
        Args:
            phone_number: Phone number to lookup
            
        Returns:
            Phone number information or None
        """
        if not self.client:
            return None
            
        try:
            lookup = self.client.lookups.v1.phone_numbers(phone_number).fetch()
            return {
                "phone_number": lookup.phone_number,
                "national_format": lookup.national_format,
                "country_code": lookup.country_code,
                "carrier": lookup.carrier.get("name") if lookup.carrier else None
            }
        except Exception as e:
            logger.error(f"Error looking up phone number: {str(e)}")
            return None


# Create singleton instance
twilio_service = TwilioService()