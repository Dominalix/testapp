import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# Vercel serverless handler
def handler(environ, start_response):
    return app(environ, start_response)

# Also support direct WSGI call
def application(environ, start_response):
    return app(environ, start_response)
