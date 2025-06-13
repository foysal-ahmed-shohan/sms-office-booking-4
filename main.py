from fastapi import FastAPI, Form, Response, HTTPException, Request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioException
from datetime import datetime
import os
from dotenv import load_dotenv
import pytz
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SMS Service API",
    description="A service that receives SMS via Twilio and sends automated replies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize Twilio client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
enable_sms_sending = os.getenv('ENABLE_SMS_SENDING', 'false').lower() == 'true'

# Validate configuration
if not all([account_sid, auth_token, twilio_phone_number]):
    logger.error("Missing Twilio configuration. Please check environment variables.")
    logger.error(f"TWILIO_ACCOUNT_SID: {'Set' if account_sid else 'Missing'}")
    logger.error(f"TWILIO_AUTH_TOKEN: {'Set' if auth_token else 'Missing'}")
    logger.error(f"TWILIO_PHONE_NUMBER: {'Set' if twilio_phone_number else 'Missing'}")
else:
    logger.info("Twilio configuration loaded successfully")
    logger.info(f"Twilio phone number: {twilio_phone_number}")
    logger.info(f"SMS sending enabled: {enable_sms_sending}")

try:
    client = Client(account_sid, auth_token)
    logger.info("Twilio client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {str(e)}")
    client = None


@app.post("/sms/webhook")
async def receive_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None),
    To: str = Form(None)
):
    """
    Webhook endpoint that receives SMS messages from Twilio
    and sends back a reply with the received message details
    """
    try:
        # Log incoming request details
        logger.info(f"=== Incoming SMS ===")
        logger.info(f"From: {From}")
        logger.info(f"To: {To}")
        logger.info(f"Body: {Body}")
        logger.info(f"MessageSid: {MessageSid}")
        logger.info(f"AccountSid: {AccountSid}")
        
        # Get current datetime
        current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Create reply message
        reply_message = f"Hello! I received your message: '{Body}' from phone number: {From} at {current_time}"
        
        # Prepare response data for testing
        response_data = {
            "status": "success",
            "received": {
                "from": From,
                "to": To,
                "body": Body,
                "message_sid": MessageSid,
                "account_sid": AccountSid
            },
            "reply": {
                "message": reply_message,
                "timestamp": current_time,
                "sms_sent": False,
                "sms_sending_enabled": enable_sms_sending
            }
        }
        
        # Check if request is from Postman (JSON response expected)
        user_agent = request.headers.get("User-Agent", "")
        is_postman = "Postman" in user_agent or request.headers.get("Accept", "").startswith("application/json")
        
        # Send SMS if enabled
        if enable_sms_sending and client and twilio_phone_number:
            try:
                message = client.messages.create(
                    body=reply_message,
                    from_=twilio_phone_number,
                    to=From
                )
                logger.info(f"SMS sent successfully via API. Message SID: {message.sid}")
                response_data["reply"]["sms_sent"] = True
                response_data["reply"]["message_sid"] = message.sid
                
            except TwilioException as e:
                logger.error(f"Failed to send SMS via Twilio API: {str(e)}")
                response_data["error"] = str(e)
            except Exception as e:
                logger.error(f"Unexpected error sending SMS: {str(e)}")
                logger.error(traceback.format_exc())
                response_data["error"] = str(e)
        else:
            if not enable_sms_sending:
                logger.info("SMS sending is disabled. Reply message prepared but not sent.")
                response_data["reply"]["reason"] = "SMS sending disabled in configuration"
            else:
                logger.warning("Cannot send SMS - Twilio client not initialized or phone number missing")
                response_data["reply"]["reason"] = "Twilio not properly configured"
        
        # Return appropriate response based on client
        if is_postman:
            # Return JSON for Postman testing
            return response_data
        else:
            # Return TwiML for Twilio webhook
            resp = MessagingResponse()
            # Only add message to TwiML if SMS wasn't sent via API
            if not (enable_sms_sending and response_data["reply"]["sms_sent"]):
                resp.message(reply_message)
            return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return error TwiML response
        error_resp = MessagingResponse()
        error_resp.message("Sorry, there was an error processing your message. Please try again later.")
        
        return Response(content=str(error_resp), media_type="application/xml")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "SMS service is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SMS Reply Service"}


@app.get("/test-config")
async def test_config():
    """Test Twilio configuration and environment variables"""
    config_status = {
        "twilio_account_sid": "Set" if account_sid else "Missing",
        "twilio_auth_token": "Set" if auth_token else "Missing",
        "twilio_phone_number": twilio_phone_number if twilio_phone_number else "Missing",
        "twilio_client_initialized": client is not None,
        "sms_sending_enabled": enable_sms_sending,
        "environment_variables": {
            "TWILIO_ACCOUNT_SID": account_sid[:10] + "..." if account_sid and len(account_sid) > 10 else account_sid,
            "TWILIO_AUTH_TOKEN": "***" if auth_token else None,
            "TWILIO_PHONE_NUMBER": twilio_phone_number,
            "ENABLE_SMS_SENDING": str(enable_sms_sending)
        }
    }
    
    # Test Twilio connection if client is initialized
    if client:
        try:
            # Try to fetch account details
            account = client.api.accounts(account_sid).fetch()
            config_status["twilio_connection"] = "Success"
            config_status["account_status"] = account.status
        except Exception as e:
            config_status["twilio_connection"] = "Failed"
            config_status["error"] = str(e)
    else:
        config_status["twilio_connection"] = "Client not initialized"
    
    return config_status


@app.post("/test-sms")
async def test_sms(phone_number: str = Form(...), message: str = Form("Test message from SMS service")):
    """Test endpoint to send an SMS directly"""
    if not client or not twilio_phone_number:
        raise HTTPException(status_code=500, detail="Twilio client not initialized or phone number missing")
    
    try:
        message_obj = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        
        return {
            "status": "success",
            "message_sid": message_obj.sid,
            "to": message_obj.to,
            "from": message_obj.from_,
            "body": message_obj.body,
            "status": message_obj.status
        }
    except TwilioException as e:
        logger.error(f"Twilio error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Twilio error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)