import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


@app.route("/")
def health():
    return jsonify({"message": "Backend is running"})


@app.route("/callers")
def callers():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
    }
    r = requests.get(
        SUPABASE_URL + "/rest/v1/callers?select=*",
        headers=headers,
        timeout=20,
    )
    return jsonify(r.json()), r.status_code


@app.route("/ask")
def ask():
    q = request.args.get("q", "Say hello")
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": q}],
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=30,
    )
    data = r.json()
    if r.status_code != 200:
        return jsonify(data), r.status_code
    answer = data["choices"][0]["message"]["content"]
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True)