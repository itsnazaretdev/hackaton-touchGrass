#!/usr/bin/env python3
"""Field Diary: turns quick notes from an outing into a diary entry using a
local open-weight model served by Ollama. Everything runs on your own machine.

Usage:
    python3 diary.py                       # reads notes.txt
    python3 diary.py --place "Retiro"      # adds the place to the prompt
    python3 diary.py --model qwen2.5:3b    # swap the model with one flag
"""

import argparse
import json
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:4b"

MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)

SYSTEM_PROMPT = """You are my personal outdoor diary. You turn my loose notes from an \
outing into a short diary entry (120-200 words), written in the first person, in \
English, in my voice.

Rules:
- Use ONLY what appears in the notes. Do not invent animals, places or events.
- Keep the sensory details I noted (smells, sounds, light).
- No morals or self-help lines at the end.
- Return only the text of the entry, with no title and no comments from you."""

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


class OllamaError(Exception):
    """Raised when the local model can't answer. The message is meant for the
    user, so both the terminal and the web page can show it as it is."""


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def read_style(path: Path) -> str:
    """Reads the examples of my voice. HTML comments are instructions for the
    human and are not sent to the model."""
    return HTML_COMMENT.sub("", read_text(path)).strip()


def build_messages(notes: str, style_examples: str, place: str) -> list[dict]:
    """Builds the chat messages. The style examples are my own texts, so the
    model imitates my voice (few-shot prompting, no training involved)."""
    system = SYSTEM_PROMPT
    if style_examples:
        system += "\n\nThese are examples of how I write. Imitate the tone:\n\n" + style_examples

    user = "These are my notes from today"
    if place:
        user += f" (place: {place})"
    user += ":\n\n" + notes
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def ask_ollama(model: str, messages: list[dict], url: str = OLLAMA_URL) -> str:
    payload = json.dumps(
        {"model": model, "messages": messages, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        # Ollama is running but rejected the request (HTTPError is a subclass
        # of URLError, so it has to be caught first).
        if error.code == 404:
            raise OllamaError(
                f"Ollama is running, but it doesn't have the model '{model}'.\n"
                f"Download it with: ollama pull {model}\n"
                "(and list what you have with: ollama list)"
            ) from error
        raise OllamaError(
            f"Ollama returned an error {error.code}: {error.reason}"
        ) from error
    except (TimeoutError, socket.timeout) as error:
        raise OllamaError(
            "Ollama is taking too long to answer. Try again, or use a smaller model."
        ) from error
    except ValueError as error:  # the reply was not valid JSON
        raise OllamaError("Ollama sent a reply I can't understand.") from error
    except urllib.error.URLError as error:
        raise OllamaError(
            "Can't connect to Ollama. Is it running?\n"
            "Try: ollama serve   (and check that you ran: "
            f"ollama pull {model})"
        ) from error
    try:
        text = data["message"]["content"].strip()
    except (KeyError, TypeError, AttributeError) as error:
        raise OllamaError("Ollama sent a reply I can't understand.") from error
    if not text:
        raise OllamaError("The model returned no text. Try again or use another model.")
    return text


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "outing"


def save_entry(body: str, place: str, out_dir: Path) -> Path:
    """Saves the entry as Markdown with frontmatter, ready for an Astro blog."""
    today = date.today()
    title = f"Outing: {place}" if place else f"Outing on {MONTHS[today.month - 1]} {today.day}"
    # The title goes inside double quotes in the frontmatter: keep it on one
    # line and free of characters that would break it.
    title = " ".join(title.split()).replace('"', "'").replace("\\", "/")
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{today.isoformat()}-{slugify(place or 'outing')}"
    path = out_dir / f"{base}.md"
    counter = 2
    while path.exists():  # two outings on the same day must not overwrite each other
        path = out_dir / f"{base}-{counter}.md"
        counter += 1
    frontmatter = f'---\ntitle: "{title}"\ndate: {today.isoformat()}\ntags: ["outings"]\n---\n\n'
    path.write_text(frontmatter + body + "\n", encoding="utf-8")
    return path


def read_entry(path: Path) -> dict:
    """Reads one saved entry into a plain dict (used by the web page)."""
    text = path.read_text(encoding="utf-8")
    title, body = path.stem, text
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        front, body = text[4:].split("\n---\n", 1)
        for line in front.splitlines():
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
    return {"file": path.name, "title": title, "date": path.stem[:10], "body": body.strip()}


def list_entries(out_dir: Path) -> list[dict]:
    """Returns the saved entries, newest first."""
    return [read_entry(path) for path in sorted(out_dir.glob("*.md"), reverse=True)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick notes -> diary entry")
    parser.add_argument("--notes", default="notes.txt", help="file with your notes")
    parser.add_argument("--style", default="style.md", help="examples of your voice")
    parser.add_argument("--place", default="", help="where you went")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model")
    parser.add_argument("--out", default="entries", help="folder where entries are saved")
    args = parser.parse_args()

    notes = read_text(Path(args.notes))
    if not notes:
        sys.exit(f"No notes found in {args.notes}. Jot something down from your outing first.")

    messages = build_messages(notes, read_style(Path(args.style)), args.place)
    print(f"Writing your entry with {args.model} (locally)...")
    try:
        body = ask_ollama(args.model, messages)
    except OllamaError as error:
        sys.exit(str(error))
    path = save_entry(body, args.place, Path(args.out))
    print(f"Done: {path}\n\n{body}")


if __name__ == "__main__":
    main()
