#!/usr/bin/env python3
"""
Minimal FastAPI server test to isolate the hanging issue
"""
import uvicorn
from fastapi import FastAPI

print("Creating minimal FastAPI app...")
app = FastAPI(title="Test API", docs_url="/docs")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting minimal server on localhost:8001...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )