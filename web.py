#!/usr/bin/env python3
"""Local web app for Field Diary.

Serves a page where you paste your notes and, with one button, a local
open-weight model (through Ollama) writes the diary entry. It only uses the
Python standard library.

Usage:
    python3 web.py            # only on this computer: http://localhost:8000
    python3 web.py --phone    # also from your phone, if it is on the same wifi
"""

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import diary

HERE = Path(__file__).resolve().parent
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MAX_BODY_BYTES = 20_000
MAX_NOTES_CHARS = 4_000
MAX_PLACE_CHARS = 80
MODEL_NAME = re.compile(r"^[A-Za-z0-9._:/-]{1,80}$")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
# Models the page always offers, even if they aren't downloaded yet.
SUGGESTED_MODELS = ("gemma3:4b", "qwen2.5:3b")


class Handler(BaseHTTPRequestHandler):
    server_version = "FieldDiary"

    # --- helpers ---------------------------------------------------------

    def _send(self, status: int, content_type: str, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", payload)

    def _host_allowed(self) -> bool:
        """Blocks DNS rebinding: when the server is only for this computer,
        it only answers requests addressed to localhost."""
        if self.server.open_to_network:
            return True
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in LOCAL_HOSTS

    # --- routes ----------------------------------------------------------

    def do_GET(self) -> None:
        if not self._host_allowed():
            return self._json(403, {"error": "Address not allowed."})

        if self.path in ("/", "/index.html"):
            page = (HERE / "index.html").read_bytes()
            return self._send(200, "text/html; charset=utf-8", page)

        if self.path == "/favicon.ico":  # the browser asks for it; there isn't one
            self.send_response(204)
            self.end_headers()
            return

        if self.path == "/api/entries":
            entries = diary.list_entries(self.server.out_dir)
            return self._json(200, {"entries": entries})

        if self.path == "/api/models":
            return self._json(200, self._installed_models())

        self._json(404, {"error": "Page not found."})

    def do_POST(self) -> None:
        if not self._host_allowed():
            return self._json(403, {"error": "Address not allowed."})
        if self.path != "/api/write":
            return self._json(404, {"error": "Page not found."})

        # Requiring JSON means a web page on another site can't send this
        # request from the browser (it would need a CORS preflight we refuse).
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._json(415, {"error": "The request must be JSON."})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if not 0 < length <= MAX_BODY_BYTES:
            return self._json(413, {"error": "The notes are too long."})

        try:
            data = json.loads(self.rfile.read(length))
            notes = str(data.get("notes", "")).strip()
            place = " ".join(str(data.get("place", "")).split())[:MAX_PLACE_CHARS]
            model = str(data.get("model", "")).strip()
        except (ValueError, AttributeError):
            return self._json(400, {"error": "Couldn't read the notes."})

        if not notes:
            return self._json(400, {"error": "Add at least one note before writing the entry."})
        if len(notes) > MAX_NOTES_CHARS:
            return self._json(413, {"error": "The notes are too long."})
        if not MODEL_NAME.match(model):
            model = self.server.default_model

        try:
            messages = diary.build_messages(
                notes, diary.read_style(self.server.style_path), place
            )
            body = diary.ask_ollama(model, messages)
            path = diary.save_entry(body, place, self.server.out_dir)
        except diary.OllamaError as error:
            return self._json(502, {"error": str(error)})
        except OSError as error:
            return self._json(500, {"error": f"Couldn't save the entry: {error.strerror}"})

        entry = diary.read_entry(path)
        entry["model"] = model
        self._json(200, {"entry": entry})

    # --- Ollama ----------------------------------------------------------

    def _installed_models(self) -> dict:
        result = {
            "models": [],
            "suggested": list(SUGGESTED_MODELS),
            "default": self.server.default_model,
            "ollama": False,
        }
        try:
            with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=3) as response:
                tags = json.load(response)
            result["models"] = [m["name"] for m in tags.get("models", []) if "name" in m]
            result["ollama"] = True
        except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError, KeyError):
            pass
        return result


def lan_ip() -> "str | None":
    """Finds this computer's address on the local network (no data is sent)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local web app for Field Diary")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--phone",
        action="store_true",
        help="allow other devices on your wifi (for example your phone) to open the page",
    )
    parser.add_argument("--model", default=diary.DEFAULT_MODEL, help="default model")
    parser.add_argument("--style", default=str(HERE / "style.md"))
    parser.add_argument("--out", default=str(HERE / "entries"))
    args = parser.parse_args()

    try:
        server = ThreadingHTTPServer(("0.0.0.0" if args.phone else "127.0.0.1", args.port), Handler)
    except OSError as error:
        sys.exit(f"Can't open port {args.port}: {error.strerror}. Try --port 8001")
    server.open_to_network = args.phone
    server.default_model = args.model
    server.style_path = Path(args.style)
    server.out_dir = Path(args.out)

    print(f"Field Diary at http://localhost:{args.port}")
    if args.phone:
        ip = lan_ip()
        if ip:
            print(f"From your phone (same wifi): http://{ip}:{args.port}")
        print("Anyone on your wifi can use this page while it is open.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSee you on the next outing.")


if __name__ == "__main__":
    main()
