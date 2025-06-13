from fastapi import APIRouter, Form, Request, Response, HTTPException, Depends
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import pytz
import logging
import uuid
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
from app.database.connection import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.sms_repository import SMSRepository
from app.database.models import User, SMSMessage
from app.services.chat.conversation_manager import ConversationManager


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
    db: Session = Depends(get_db),
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
        
        # Initialize repositories
        user_repo = UserRepository(db)
        sms_repo = SMSRepository(db)
        
        # Store/get user in database FIRST
        try:
            user = user_repo.create_or_update(
                phone_number=sms_data.From,
                twilio_phone_number=sms_data.To
            )
            logger.info(f"User stored/updated in database: {user.id}")
        except Exception as e:
            logger.error(f"Database error creating/updating user: {str(e)}")
            user = None
        
        # Check if request expects JSON response (from Postman)
        user_agent = request.headers.get("User-Agent", "")
        is_postman = "Postman" in user_agent or request.headers.get("Accept", "").startswith("application/json")
        
        # Use conversation manager to generate intelligent reply
        if user:
            try:
                conversation_manager = ConversationManager(db)
                reply_message = conversation_manager.process_message(user, sms_data.Body)
                logger.info(f"Generated intelligent reply: {reply_message[:100]}...")
            except Exception as e:
                logger.error(f"Error in conversation manager: {str(e)}")
                # Fallback to simple reply if chat system fails
                reply_message = "I'm sorry, I'm having trouble understanding your request. Please try again or call our support."
        else:
            reply_message = "I'm sorry, I'm having trouble accessing your account. Please try again later."
        
        # Prepare reply data
        reply_data = SMSReplyData(
            message=reply_message,
            timestamp=current_time,
            sms_sent=False,
            sms_sending_enabled=settings.enable_sms_sending
        )
        
        # Store inbound SMS message
        if user:
            try:
                # Generate unique MessageSid for testing if not provided or if it's a duplicate
                message_sid = sms_data.MessageSid
                if not message_sid or is_postman:
                    # For testing, generate a unique message SID
                    message_sid = f"TEST_{uuid.uuid4().hex[:32]}"
                    logger.debug(f"Generated test MessageSid: {message_sid}")
                
                inbound_sms = sms_repo.create_message(
                    user_id=user.id,
                    direction='inbound',
                    from_number=sms_data.From,
                    to_number=sms_data.To,
                    message_body=sms_data.Body,
                    message_sid=message_sid,
                    account_sid=sms_data.AccountSid,
                    messaging_service_sid=sms_data.MessagingServiceSid,
                    num_media=int(sms_data.NumMedia or 0)
                )
                logger.info(f"Inbound SMS stored in database: {inbound_sms.id}")
            except Exception as e:
                logger.error(f"Database error storing SMS data: {str(e)}")
                # Continue processing even if database fails
        
        # Always store the reply message in database (regardless of SMS sending)
        outbound_sms = None
        try:
            # Determine status based on SMS sending
            if settings.enable_sms_sending:
                success, message_sid, error = twilio_service.send_sms(
                    to_number=sms_data.From,
                    message=reply_message
                )
                
                if success:
                    reply_data.sms_sent = True
                    reply_data.message_sid = message_sid
                    status = 'sent'
                    error_msg = None
                else:
                    reply_data.error = error
                    status = 'failed'
                    error_msg = error
                    message_sid = None
                    # Generate test MessageSid for failed sends during testing
                    if is_postman:
                        message_sid = f"TEST_FAIL_{uuid.uuid4().hex[:32]}"
            else:
                # SMS sending disabled - still store the reply
                reply_data.reason = "SMS sending disabled in configuration"
                status = 'draft'  # Not sent but prepared
                message_sid = None
                error_msg = None
            
            # Generate unique MessageSid for outbound testing if needed
            if not message_sid and is_postman:
                message_sid = f"TEST_OUT_{uuid.uuid4().hex[:32]}"
                logger.debug(f"Generated test outbound MessageSid: {message_sid}")
            
            # Store outbound SMS in database
            outbound_sms = sms_repo.create_message(
                user_id=user.id,
                direction='outbound',
                from_number=sms_data.To,
                to_number=sms_data.From,
                message_body=reply_message,
                message_sid=message_sid,
                account_sid=sms_data.AccountSid,
                status=status,
                error_message=error_msg
            )
            logger.info(f"Outbound SMS stored in database: {outbound_sms.id} (status: {status})")
            
        except Exception as e:
            logger.error(f"Database error storing outbound SMS: {str(e)}")
        
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
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    # Check database connection
    db_status = "healthy"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_count = db.query(User).count()
        logger.debug(f"Database health check: {db_count} users")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")
    
    return HealthCheckResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="SMS Reply Service",
        version=settings.api_version,
        database_status=db_status
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