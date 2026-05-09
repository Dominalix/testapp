from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Flask app working!"})

@app.route('/api/test')
def test():
    return jsonify({"status": "API working!"})
