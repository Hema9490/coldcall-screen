import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.7-flash"


@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "coldcall backend is running"})


@app.route("/callers")
def callers():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/callers?select=*",
        headers={"apikey": SUPABASE_KEY},
        timeout=20,
    )
    return jsonify(r.json()), r.status_code


@app.route("/ask")
def ask():
    question = request.args.get("q", "Say hello in one short sentence")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": question}]}]},
        timeout=30,
    )
    return jsonify(r.json()), r.status_code


if __name__ == "__main__":
    app.run(debug=True)