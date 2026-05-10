import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Flask app
from app import app

# Vercel serverless handler
def handler(environ, start_response):
    return app(environ, start_response)
