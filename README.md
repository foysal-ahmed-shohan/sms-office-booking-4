# sms-office-booking-4

A FastAPI-based SMS service that receives messages via Twilio webhooks and sends automated replies.

## Features

- Receives SMS messages through Twilio webhooks
- Sends automated replies with message details and timestamp
- RESTful API with automatic documentation
- Health check and configuration testing endpoints
- Comprehensive logging and error handling

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Twilio credentials:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

3. Run the server:
```bash
python run.py
# or
./run.sh
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `POST /sms/webhook` - Twilio webhook endpoint for receiving SMS
- `GET /docs` - Swagger UI documentation
- `GET /test-config` - Test Twilio configuration
- `POST /test-sms` - Send test SMS message

## Twilio Configuration

1. Log in to your Twilio Console
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your Twilio phone number
4. In the "Messaging" section, set the webhook URL to: `https://your-domain.com:8000/sms/webhook`
5. Set the HTTP method to `POST`

Note: For local testing, use ngrok to expose your local server to the internet.