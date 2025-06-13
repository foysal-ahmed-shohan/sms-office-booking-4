from fastapi import APIRouter, Form, Request, Response, HTTPException, Depends
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import pytz
import logging
from typing import Dict, Optional

from app.schemas import (
    SMSWebhookRequest, 
    SMSWebhookResponse, 
    SMSReplyData,
    TestSMSRequest,
    ConfigStatus,
    HealthCheckResponse
)
from app.services.twilio_service import twilio_service
from app.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


def get_full_url(request: Request) -> str:
    """Get the full URL of the request for signature validation"""
    return str(request.url)


def get_request_params(request: Request) -> Dict[str, str]:
    """Extract request parameters for signature validation"""
    return dict(request._form)


@router.post("/sms/webhook")
async def receive_sms(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None),
    MessagingServiceSid: Optional[str] = Form(None),
    NumMedia: Optional[str] = Form("0")
):
    """
    Webhook endpoint that receives SMS messages from Twilio
    and sends back a reply with the received message details
    """
    try:
        # Create SMS data object for validation
        sms_data = SMSWebhookRequest(
            From=From,
            To=To,
            Body=Body,
            MessageSid=MessageSid,
            AccountSid=AccountSid,
            MessagingServiceSid=MessagingServiceSid,
            NumMedia=NumMedia
        )
        
        # Log incoming request
        logger.info("=" * 50)
        logger.info("INCOMING SMS WEBHOOK REQUEST")
        logger.info(f"From: {sms_data.From}")
        logger.info(f"To: {sms_data.To}")
        logger.info(f"Body: {sms_data.Body}")
        logger.info(f"MessageSid: {sms_data.MessageSid}")
        logger.debug(f"Full request data: {sms_data.dict()}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Validate Twilio signature if enabled
        validation_result = {"signature_checked": False, "signature_valid": None}
        
        if settings.validate_twilio_signature:
            signature = request.headers.get("X-Twilio-Signature", "")
            if not signature:
                logger.warning("Missing X-Twilio-Signature header")
                if not request.headers.get("User-Agent", "").startswith("Postman"):
                    raise HTTPException(status_code=400, detail="Missing Twilio signature")
            else:
                url = get_full_url(request)
                params = await request.form()
                params_dict = dict(params)
                
                is_valid = twilio_service.validate_request(url, params_dict, signature)
                validation_result = {
                    "signature_checked": True,
                    "signature_valid": is_valid
                }
                
                if not is_valid:
                    logger.error("Invalid Twilio signature")
                    raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Get current datetime
        current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Create reply message
        reply_message = f"Hello! I received your message: '{sms_data.Body}' from phone number: {sms_data.From} at {current_time}"
        
        # Prepare reply data
        reply_data = SMSReplyData(
            message=reply_message,
            timestamp=current_time,
            sms_sent=False,
            sms_sending_enabled=settings.enable_sms_sending
        )
        
        # Check if request expects JSON response (from Postman)
        user_agent = request.headers.get("User-Agent", "")
        is_postman = "Postman" in user_agent or request.headers.get("Accept", "").startswith("application/json")
        
        # Send SMS if enabled
        if settings.enable_sms_sending:
            success, message_sid, error = twilio_service.send_sms(
                to_number=sms_data.From,
                message=reply_message
            )
            
            if success:
                reply_data.sms_sent = True
                reply_data.message_sid = message_sid
            else:
                reply_data.error = error
        else:
            reply_data.reason = "SMS sending disabled in configuration"
        
        # Prepare response
        response_data = SMSWebhookResponse(
            status="success",
            received=sms_data.dict(),
            reply=reply_data,
            validation=validation_result if settings.validate_twilio_signature else None
        )
        
        # Return appropriate response
        if is_postman:
            return response_data
        else:
            # Return TwiML response for Twilio
            resp = MessagingResponse()
            # Only add message if SMS wasn't sent via API
            if not (settings.enable_sms_sending and reply_data.sms_sent):
                resp.message(reply_message)
            return Response(content=str(resp), media_type="application/xml")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}", exc_info=True)
        
        # Return error response
        if is_postman:
            raise HTTPException(status_code=500, detail=str(e))
        else:
            error_resp = MessagingResponse()
            error_resp.message("Sorry, there was an error processing your message.")
            return Response(content=str(error_resp), media_type="application/xml")


@router.post("/test-sms")
async def test_sms(request: TestSMSRequest):
    """Test endpoint to send an SMS directly"""
    success, message_sid, error = twilio_service.send_sms(
        to_number=request.phone_number,
        message=request.message
    )
    
    if success:
        return {
            "status": "success",
            "message_sid": message_sid,
            "to": request.phone_number,
            "message": request.message,
            "sms_sending_enabled": settings.enable_sms_sending
        }
    else:
        raise HTTPException(status_code=400, detail=error)


@router.get("/test-config", response_model=ConfigStatus)
async def test_config():
    """Test Twilio configuration and environment variables"""
    # Test connection
    connection_success, connection_info = twilio_service.test_connection()
    
    return ConfigStatus(
        twilio_account_sid="Set" if settings.twilio_account_sid else "Missing",
        twilio_auth_token="Set" if settings.twilio_auth_token else "Missing",
        twilio_phone_number=settings.twilio_phone_number,
        twilio_client_initialized=twilio_service.client is not None,
        sms_sending_enabled=settings.enable_sms_sending,
        signature_validation_enabled=settings.validate_twilio_signature,
        environment_variables={
            "TWILIO_ACCOUNT_SID": settings.twilio_account_sid[:10] + "..." if len(settings.twilio_account_sid) > 10 else settings.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": "***",
            "TWILIO_PHONE_NUMBER": settings.twilio_phone_number,
            "ENABLE_SMS_SENDING": str(settings.enable_sms_sending),
            "VALIDATE_TWILIO_SIGNATURE": str(settings.validate_twilio_signature)
        },
        twilio_connection="Success" if connection_success else "Failed",
        account_status=connection_info.get("status") if connection_success else None,
        error=connection_info.get("error") if not connection_success else None
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="SMS Reply Service",
        version=settings.api_version
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SMS Service API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }