from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Flask app working!"})

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    return jsonify([
        {"id": 1, "name": "Technologia", "description": "Procesy fotograficzne"},
        {"id": 2, "name": "Maszynoznawstwo", "description": "Aparaty fotograficzne"},
        {"id": 3, "name": "Materiałoznawstwo", "description": "Materiały światłoczułe"}
    ])

# Serve frontend with password protection
@app.route('/app')
def serve_frontend():
    access = request.args.get('access')
    if access == 'papiezpolak':
        return '''
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Frontend working!</h1>
    <p>API: <a href="/api/chapters">/api/chapters</a></p>
</body>
</html>
        '''
    else:
        return '''
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h1>Enter password</h1>
    <a href="/app?access=papiezpolak">Login</a>
</body>
</html>
        '''

@app.route('/app/<path:filename>')
def static_files(filename):
    return "Static files disabled for testing"
