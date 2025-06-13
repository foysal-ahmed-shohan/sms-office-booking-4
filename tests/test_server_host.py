#!/usr/bin/env python3
"""
Test server with different host configurations
"""
import uvicorn
from app.main import app
from app.config import settings

print(f"Testing server with host: {settings.host}, port: {settings.port}")
print("Starting server...")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,  # Disable reload for testing
        log_level=settings.log_level.lower()
    )