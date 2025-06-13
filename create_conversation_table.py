#!/usr/bin/env python3
"""Create conversation_states table"""
from app.database.connection import engine
from app.database.models import ConversationState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_conversation_table():
    """Create the conversation_states table"""
    try:
        # Create only the conversation_states table
        ConversationState.__table__.create(engine, checkfirst=True)
        logger.info("Created conversation_states table successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        return False

if __name__ == "__main__":
    if create_conversation_table():
        print("✓ Conversation table created successfully!")
    else:
        print("✗ Failed to create conversation table")