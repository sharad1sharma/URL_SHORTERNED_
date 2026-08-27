from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, redirect, render_template_string

from database import init_db
from models import (
    create_url, get_by_code, get_by_id, get_all,
    update_url, delete_url, clear_history,
    increment_clicks, get_stats
)
from utils import generate_short_code, is_valid_url, row_to_dict

api = Blueprint("api", __name__)
init_db()

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def build_short_url(short_code):
    return request.host_url.rstrip("/") + "/" + short_code

@api.post("/shorten")
def shorten():
    data = request.get_json(silent=True) or {}
    original_url = str(data.get("url", "")).strip()

    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    if not is_valid_url(original_url):
        return jsonify({
            "error": "Please enter a valid URL beginning with http:// or https://"
        }), 400

    
    for _ in range(10):
        short_code = generate_short_code()
        if not get_by_code(short_code):
            break
    else:
        return jsonify({"error": "Could not generate a unique short code"}), 500

    created_at = now()
    url_id = create_url(original_url, short_code, created_at)
    row = get_by_id(url_id)

    return jsonify({
        "message": "URL shortened successfully",
        "data": {
            **row_to_dict(row),
            "short_url": build_short_url(short_code)
        }
    }), 201

@api.get("/history")
def history():
    search = request.args.get("search", "").strip()
    rows = get_all(search)

    return jsonify({
        "data": [
            {
                **row_to_dict(row),
                "short_url": build_short_url(row["short_code"])
            }
            for row in rows
        ]
    })

@api.get("/urls/<int:url_id>")
def get_url(url_id):
    row = get_by_id(url_id)

    if not row:
        return jsonify({"error": "URL not found"}), 404

    return jsonify({
        "data": {
            **row_to_dict(row),
            "short_url": build_short_url(row["short_code"])
        }
    })

@api.put("/urls/<int:url_id>")
def edit_url(url_id):
    data = request.get_json(silent=True) or {}
    original_url = str(data.get("url", "")).strip()

    if not is_valid_url(original_url):
        return jsonify({"error": "Please enter a valid URL"}), 400

    if not get_by_id(url_id):
        return jsonify({"error": "URL not found"}), 404

    update_url(url_id, original_url, now())
    row = get_by_id(url_id)

    return jsonify({
        "message": "URL updated successfully",
        "data": {
            **row_to_dict(row),
            "short_url": build_short_url(row["short_code"])
        }
    })

@api.delete("/urls/<int:url_id>")
def remove_url(url_id):
    if delete_url(url_id) == 0:
        return jsonify({"error": "URL not found"}), 404

    return jsonify({"message": "URL deleted successfully"})

@api.delete("/history")
def remove_history():
    clear_history()
    return jsonify({"message": "History cleared successfully"})

@api.get("/stats")
def stats():
    return jsonify({"data": get_stats()})

NOT_FOUND_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Short URL not found</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 4rem 1rem; color: #333; }
        a { color: #1565c0; }
    </style>
</head>
<body>
    <h1>Short URL not found</h1>
    <p>This link does not exist or was deleted.</p>
    <p><a href="/">Back to URL Shortener</a></p>
</body>
</html>
"""


def redirect_short_url(short_code):
    row = get_by_code(short_code)

    if not row:
        return render_template_string(NOT_FOUND_PAGE), 404

    original_url = row["original_url"]
    increment_clicks(short_code)
    return redirect(original_url, code=302)
