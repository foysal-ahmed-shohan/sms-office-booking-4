"""Tests package initialization - adds parent directory to Python path"""
import sys
import os

# Add parent directory to Python path so tests can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)