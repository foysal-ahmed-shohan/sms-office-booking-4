#!/usr/bin/env python3
"""
Test app components one by one to isolate the hanging issue
"""
import sys
import time

def test_import(module_name, description):
    """Test importing a module and measure time"""
    print(f"Testing {description}...")
    start_time = time.time()
    try:
        if module_name == "app.config":
            from app.config import settings
            print(f"  [OK] Settings loaded - Host: {settings.host}, Port: {settings.port}")
        elif module_name == "app.utils.logging":
            from app.utils.logging import setup_logging
            print(f"  [OK] Logging utils imported")
        elif module_name == "app.services.twilio_service":
            from app.services.twilio_service import twilio_service
            print(f"  [OK] Twilio service imported")
        elif module_name == "app.api.endpoints":
            from app.api.endpoints import router
            print(f"  [OK] API endpoints imported")
        elif module_name == "app.main":
            from app.main import app
            print(f"  [OK] Main app imported")
        else:
            __import__(module_name)
            print(f"  [OK] {module_name} imported")
        
        end_time = time.time()
        print(f"  Time taken: {end_time - start_time:.3f} seconds")
        return True
    except Exception as e:
        end_time = time.time()
        print(f"  [ERROR] Failed to import {module_name}: {e}")
        print(f"  Time taken: {end_time - start_time:.3f} seconds")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing app components step by step...")
    print("=" * 50)
    
    # Test basic imports first
    components = [
        ("app.config", "App configuration"),
        ("app.utils.logging", "Logging utilities"),
        ("app.services.twilio_service", "Twilio service"),
        ("app.api.endpoints", "API endpoints"),
        ("app.main", "Main FastAPI app"),
    ]
    
    for module_name, description in components:
        success = test_import(module_name, description)
        if not success:
            print(f"FAILED at: {description}")
            break
        print()
    
    print("Component testing completed.")

if __name__ == "__main__":
    main()