#!/usr/bin/env python3
"""
Test script to isolate Twilio client initialization issues
"""
import sys
import time
from app.config import settings

print("Starting Twilio initialization test...")
print(f"Twilio Account SID: {settings.twilio_account_sid[:10]}...")
print(f"Twilio Auth Token: {'*' * 10}")
print(f"Twilio Phone: {settings.twilio_phone_number}")

try:
    print("Importing Twilio Client...")
    from twilio.rest import Client
    print("[OK] Twilio Client imported successfully")
    
    print("Initializing Twilio Client...")
    start_time = time.time()
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    end_time = time.time()
    print(f"[OK] Twilio Client initialized in {end_time - start_time:.2f} seconds")
    
    print("Testing account fetch...")
    start_time = time.time()
    account = client.api.accounts(settings.twilio_account_sid).fetch()
    end_time = time.time()
    print(f"[OK] Account fetched in {end_time - start_time:.2f} seconds")
    print(f"Account status: {account.status}")
    print(f"Account name: {account.friendly_name}")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")