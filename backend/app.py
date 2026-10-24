import os
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")


def sb(method, path, **kwargs):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    return requests.request(
        method,
        SUPABASE_URL + "/rest/v1/" + path,
        headers=headers,
        timeout=20,
        **kwargs
    )


def groq(prompt):
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=30,
    )
    data = r.json()
    if r.status_code != 200:
        raise Exception(str(data))
    return data["choices"][0]["message"]["content"]


def fail(r):
    try:
        body = r.json()
    except Exception:
        body = {"error": r.text}
    return jsonify(body), r.status_code


@app.route("/")
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/stages")
def stages():
    r = sb("GET", "stages?select=*&order=number.asc")
    if r.status_code >= 400:
        return fail(r)
    return jsonify(r.json())


@app.route("/calls", methods=["GET"])
def list_calls():
    r = sb("GET", "calls?select=*&order=started_at.desc")
    if r.status_code >= 400:
        return fail(r)
    return jsonify(r.json())


@app.route("/calls", methods=["POST"])
def start_call():
    data = request.get_json(silent=True) or {}
    name = (data.get("prospect_name") or "").strip()
    if not name:
        return jsonify({"error": "prospect_name is required"}), 400
    row = {"prospect_name": name, "company": data.get("company", "")}
    r = sb("POST", "calls", json=row)
    if r.status_code >= 400:
        return fail(r)
    return jsonify(r.json()[0]), 201


@app.route("/calls/<call_id>", methods=["GET"])
def get_call(call_id):
    c = sb("GET", "calls?id=eq." + call_id + "&select=*")
    if c.status_code >= 400:
        return fail(c)
    if not c.json():
        return jsonify({"error": "call not found"}), 404
    s = sb("GET", "stage_results?call_id=eq." + call_id + "&select=*&order=created_at.asc")
    if s.status_code >= 400:
        return fail(s)
    call = c.json()[0]
    call["stage_results"] = s.json()
    return jsonify(call)


@app.route("/calls/<call_id>/stage", methods=["POST"])
def save_stage(call_id):
    data = request.get_json(silent=True) or {}
    try:
        stage = int(data.get("stage"))
    except Exception:
        return jsonify({"error": "stage must be a number from 1 to 8"}), 400
    if stage < 1 or stage > 8:
        return jsonify({"error": "stage must be from 1 to 8"}), 400

    c = sb("GET", "calls?id=eq." + call_id + "&select=*")
    if c.status_code >= 400:
        return fail(c)
    if not c.json():
        return jsonify({"error": "call not found"}), 404
    call = c.json()[0]

    row = {
        "call_id": call_id,
        "stage": stage,
        "what_happened": data.get("what_happened", ""),
        "prospect_words": data.get("prospect_words", ""),
    }
    r = sb("POST", "stage_results", json=row)
    if r.status_code >= 400:
        return fail(r)

    update = {
        "current_stage": min(stage + 1, 8),
        "last_stage_reached": max(call["last_stage_reached"], stage),
    }
    u = sb("PATCH", "calls?id=eq." + call_id, json=update)
    if u.status_code >= 400:
        return fail(u)
    return jsonify(u.json()[0])


@app.route("/calls/<call_id>/check", methods=["POST"])
def check_outcome(call_id):
    data = request.get_json(silent=True) or {}
    outcome = data.get("outcome", "")
    s = sb("GET", "stage_results?call_id=eq." + call_id + "&select=*&order=created_at.asc")
    if s.status_code >= 400:
        return fail(s)
    lines = []
    for x in s.json():
        lines.append(
            "Stage "
            + str(x["stage"])
            + ": what happened = "
            + str(x.get("what_happened"))
            + "; prospect said = "
            + str(x.get("prospect_words"))
        )
    notes = "\n".join(lines) if lines else "Nothing was recorded"
    prompt = (
        "A cold caller logged the outcome '" + outcome + "' for a call. "
        "Here is what they recorded during the call:\n" + notes + "\n\n"
        "Does the logged outcome fit what was recorded? "
        "Start your reply with the single word MATCH or MISMATCH, "
        "then one short plain sentence explaining why. No markdown."
    )
    try:
        answer = groq(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify({"check": answer})


@app.route("/calls/<call_id>/close", methods=["POST"])
def close_call(call_id):
    data = request.get_json(silent=True) or {}
    outcome = (data.get("outcome") or "").strip()
    if not outcome:
        return jsonify({"error": "outcome is required"}), 400
    update = {
        "outcome": outcome,
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    u = sb("PATCH", "calls?id=eq." + call_id, json=update)
    if u.status_code >= 400:
        return fail(u)
    if not u.json():
        return jsonify({"error": "call not found"}), 404
    return jsonify(u.json()[0])


if __name__ == "__main__":
    app.run(debug=True)