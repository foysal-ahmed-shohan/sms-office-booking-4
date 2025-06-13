#!/usr/bin/env python3
"""Test SMS endpoint with conversation flow"""
import requests
import json

def test_sms_conversation():
    """Test SMS webhook endpoint with a booking conversation"""
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/sms/webhook"
    
    # Test phone numbers
    from_number = "+12025551234"
    to_number = "+18123591901"
    
    print("Testing SMS conversation flow via webhook endpoint...\n")
    
    # Message 1: Initial booking request
    print("--- Message 1: Initial booking request ---")
    response1 = requests.post(webhook_url, data={
        "From": from_number,
        "To": to_number,
        "Body": "I want to book a meeting room for tomorrow",
        "MessageSid": "SM001",
        "AccountSid": "AC123"
    })
    print(f"Status: {response1.status_code}")
    print(f"Response: {response1.json()['reply']['message']}\n")
    
    # Message 2: Location
    print("--- Message 2: Location ---")
    response2 = requests.post(webhook_url, data={
        "From": from_number,
        "To": to_number,
        "Body": "salt lake city",
        "MessageSid": "SM002",
        "AccountSid": "AC123"
    })
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.json()['reply']['message']}\n")
    
    # Message 3: Capacity
    print("--- Message 3: Capacity ---")
    response3 = requests.post(webhook_url, data={
        "From": from_number,
        "To": to_number,
        "Body": "5 people",
        "MessageSid": "SM003",
        "AccountSid": "AC123"
    })
    print(f"Status: {response3.status_code}")
    print(f"Response: {response3.json()['reply']['message']}\n")
    
    # Message 4: Time
    print("--- Message 4: Time ---")
    response4 = requests.post(webhook_url, data={
        "From": from_number,
        "To": to_number,
        "Body": "2pm",
        "MessageSid": "SM004",
        "AccountSid": "AC123"
    })
    print(f"Status: {response4.status_code}")
    print(f"Response: {response4.json()['reply']['message']}\n")

if __name__ == "__main__":
    print("Make sure the server is running (python3 run.py)")
    print("Press Enter to continue...")
    input()
    
    try:
        test_sms_conversation()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure it's running on port 8000")