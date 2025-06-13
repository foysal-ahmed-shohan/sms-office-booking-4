#!/usr/bin/env python3
"""Test API endpoint with IDs response"""
import requests
import json

def test_api_ids():
    """Test the API endpoint returns IDs correctly"""
    base_url = "http://localhost:8000"
    
    # Test data for complete booking flow
    messages = [
        "need meeting room for 2 people in atlanta on dec 25 2025 2pm to 3pm",
        "1",  # Select first resource
        "yes"  # Confirm booking
    ]
    
    print("\n" + "="*70)
    print("API IDS RESPONSE TEST")
    print("="*70)
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. Sending: '{message}'")
        
        # Prepare form data like Twilio would send
        form_data = {
            "From": "+1234567890",
            "To": "+10987654321",
            "Body": message,
            "MessageSid": f"TEST{i}",
            "AccountSid": "ACtest"
        }
        
        try:
            response = requests.post(
                f"{base_url}/sms/webhook",
                data=form_data,
                headers={"User-Agent": "Postman/Test"}  # Trigger JSON response
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get('reply', {})
                
                print(f"Response message: {reply.get('message', '')[:100]}...")
                
                # Check for IDs in the final response
                if reply.get('all_required_ids'):
                    print("\n=== ALL REQUIRED IDS ===")
                    print(json.dumps(reply['all_required_ids'], indent=2))
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Note: Make sure the server is running before running this test
    print("Note: Make sure the server is running on port 8000")
    print("Run with: python run.py")
    test_api_ids()