#!/bin/bash
# Run the FastAPI application with uvicorn

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload