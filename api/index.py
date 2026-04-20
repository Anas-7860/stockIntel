"""
Vercel serverless entry point for the Stock Data Intelligence Dashboard.
Re-exports the FastAPI app from main.py for Vercel's @vercel/python builder.
"""

import sys
import os

# Add the project root to the Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
