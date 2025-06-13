# Test Files

This directory contains diagnostic test files created during debugging the server accessibility issue.

## Test Files Description

### `test_twilio_init.py`
- **Purpose**: Tests Twilio client initialization in isolation
- **What it checks**: Verifies that Twilio SDK can be imported and initialized without hanging
- **Result**: Confirmed Twilio initialization works fine (0.53 seconds)

### `test_minimal_server.py`
- **Purpose**: Tests a minimal FastAPI server without any application-specific code
- **What it checks**: Verifies basic FastAPI/uvicorn functionality
- **Result**: Confirmed basic server works fine

### `test_app_components.py`
- **Purpose**: Tests importing each application component step by step
- **What it checks**: Isolates which component might be causing startup issues
- **Components tested**: config, logging, twilio_service, api.endpoints, main app
- **Result**: All components import successfully

### `test_server_host.py`
- **Purpose**: Tests the full application server with exact configuration
- **What it checks**: Tests server startup with the actual app configuration
- **Key difference**: Uses `reload=False` instead of `reload=settings.debug`
- **Result**: Server works perfectly when reload is disabled

### `test_server.py`
- **Purpose**: Original test server file (pre-existing)
- **What it checks**: General server functionality testing

## Root Cause Identified

The issue was with **uvicorn's reload feature** when `DEBUG=true` in the environment. The reload functionality was causing the server to hang and not respond to HTTP requests, even though it appeared to be running in the terminal.

## Solution

Disable the reload feature by setting `reload=False` in the uvicorn.run() call, or set `DEBUG=false` in the environment variables.

## Usage

These test files can be run individually to verify different aspects of the application:

```bash
# Test Twilio initialization
python tests/test_twilio_init.py

# Test minimal server (runs on port 8001)
python tests/test_minimal_server.py

# Test app components import
python tests/test_app_components.py

# Test full server with fixed configuration
python tests/test_server_host.py