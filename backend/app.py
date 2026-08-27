from pathlib import Path

from flask import Flask, abort, send_from_directory
from flask_cors import CORS

from routes import api, redirect_short_url
from database import init_db

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
RESERVED_PATHS = {"api", "favicon.ico"}

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)

app.register_blueprint(api, url_prefix="/api")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/css/<path:filename>")
def css_files(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)


@app.route("/js/<path:filename>")
def js_files(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)


@app.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    if short_code in RESERVED_PATHS:
        abort(404)
    return redirect_short_url(short_code)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
