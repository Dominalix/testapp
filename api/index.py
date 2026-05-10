import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import of Flask app (Debug version for troubleshooting)
from app_debug import app

# Vercel serverless handler - this is the main entry point
def handler(environ, start_response):
    return app(environ, start_response)

# Also export as module-level handler for Vercel
application = app

# Vercel might expect this name too
def lambda_handler(event, context):
    return app
