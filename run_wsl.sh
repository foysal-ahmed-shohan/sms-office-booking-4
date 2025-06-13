#!/bin/bash
# Run script optimized for WSL

echo "Starting SMS Service in WSL mode..."
echo "====================================="
echo "Access the service at:"
echo "- http://localhost:8000"
echo "- http://127.0.0.1:8000"
echo "- http://$(hostname -I | awk '{print $1}'):8000"
echo "====================================="

# Export the host to ensure it binds to all interfaces
export HOST=0.0.0.0

# Run with explicit host binding
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info