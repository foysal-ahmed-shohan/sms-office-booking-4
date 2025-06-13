#!/usr/bin/env python3
"""
Quick test to verify the server can start and respond
"""
import requests
import time
import subprocess
import sys

def test_server():
    # Start the server
    print("Starting server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000/", "Root endpoint"),
        ("http://localhost:8000/health", "Health check"),
        ("http://localhost:8000/docs", "API docs"),
        ("http://127.0.0.1:8000/", "Root via 127.0.0.1"),
    ]
    
    for url, description in endpoints:
        try:
            print(f"\nTesting {description}: {url}")
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # Stop the server
    process.terminate()
    print("\nServer stopped.")

if __name__ == "__main__":
    test_server()