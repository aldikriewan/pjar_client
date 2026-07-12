"""
PJAR Client - Web-based client
Menggantikan UI tkinter dengan antarmuka web (HTML/CSS/JS) yang tetap
terhubung ke Backend Server (pjar_server) via HTTP API yang sama.

Web app ini hanya bertindak sebagai "client":
  - Menyajikan UI web (templates/index.html)
  - Mem-proxy semua request /api/* ke SERVER_URL (backend) agar tidak kena CORS

Tidak butuh library requests: proxy memakai urllib (standard library).
"""

import json
import os
import uuid
import urllib.request
import urllib.error
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

urllib_request = urllib.request.Request
urllib_HTTPError = urllib.error.HTTPError
urllib_URLError = urllib.error.URLError

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Server endpoint - dapat diubah sesuai kebutuhan (sama seperti app.py tkinter)
SERVER_URL = os.environ.get("SERVER_URL", "http://192.168.1.12:5000")
# Port tempat web client berjalan
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", 5001))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)


def _forward(method, path, body=None, content_type=None):
    """Teruskan request ke backend server dan kembalikan response-nya."""
    url = f"{SERVER_URL}{path}"
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            data = body
            if content_type:
                headers["Content-Type"] = content_type
        else:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

    req = urllib_request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            status = resp.status
    except urllib_HTTPError as exc:
        content = exc.read()
        ctype = exc.headers.get("Content-Type", "")
        status = exc.code
    except urllib_URLError as exc:
        reason = getattr(exc, "reason", exc)
        return jsonify({"error": f"Tidak dapat terhubung ke server: {reason}"}), 502

    if "application/json" in ctype:
        try:
            return jsonify(json.loads(content)), status
        except ValueError:
            pass
    return content, status, {"Content-Type": ctype or "application/octet-stream"}


def _build_multipart(form_fields, files):
    """Buat body multipart/form-data secara manual (tanpa library requests)."""
    boundary = "----PJARClientBoundary" + uuid.uuid4().hex
    chunks = []
    for name, value in form_fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(value.encode("utf-8") if isinstance(value, str) else value)
        chunks.append(b"\r\n")
    for name, f in files.items():
        filename = secure_filename(f.filename) or "file.bin"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {f.mimetype or 'application/octet-stream'}\r\n\r\n".encode())
        chunks.append(f.read())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    body = b"".join(chunks)
    return body, f"multipart/form-data; boundary={boundary}"


@app.route("/")
def index():
    return render_template("index.html")


# Proxy semua endpoint API ke backend server
@app.route("/api/health", methods=["GET"])
@app.route("/api/videos", methods=["GET"])
@app.route("/api/login", methods=["POST"])
@app.route("/api/register", methods=["POST"])
@app.route("/api/verify", methods=["POST"])
@app.route("/api/upload", methods=["POST"])
@app.route("/api/stream", methods=["POST"])
def proxy_api():
    path = request.path
    if request.method == "GET":
        return _forward("GET", path)

    if request.files:
        form_fields = {k: v for k, v in request.form.items()}
        body, ctype = _build_multipart(form_fields, request.files)
        return _forward("POST", path, body=body, content_type=ctype)

    if request.is_json:
        return _forward("POST", path, body=request.get_json(silent=True))

    return _forward("POST", path, body=request.form.to_dict())


# Proxy file video dari backend (teruskan Range header agar seek di player bekerja)
@app.route("/videos/<path:filename>")
def proxy_video(filename):
    url = f"{SERVER_URL}/videos/{filename}"
    req_headers = {}
    if request.headers.get("Range"):
        req_headers["Range"] = request.headers["Range"]
    req = urllib_request(url, headers=req_headers)
    try:
        backend = urllib.request.urlopen(req, timeout=30)
    except urllib_HTTPError as exc:
        return exc.read(), exc.code, dict(exc.headers)

    def generate():
        try:
            while True:
                chunk = backend.read(65536)
                if not chunk:
                    break
                yield chunk
        finally:
            backend.close()

    out_headers = {}
    for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
        if h in backend.headers:
            out_headers[h] = backend.headers[h]
    return Response(generate(), status=backend.status, headers=out_headers)


if __name__ == "__main__":
    print(f"[PJAR Client] Menyajikan UI web di http://localhost:{CLIENT_PORT}")
    print(f"[PJAR Client] Terhubung ke backend: {SERVER_URL}")
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=CLIENT_PORT)
