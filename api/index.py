import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app import app
    flask_app = app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current path: {sys.path}")
    print(f"Backend path: {backend_path}")
    raise

# Vercel serverless handler with error handling
def handler(environ, start_response):
    try:
        return flask_app(environ, start_response)
    except Exception as e:
        print(f"Handler error: {e}")
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [b'Internal Server Error']

# Also support direct WSGI call
def application(environ, start_response):
    return handler(environ, start_response)
