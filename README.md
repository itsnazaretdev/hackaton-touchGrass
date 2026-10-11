# Field Diary

Jot down quick notes while you walk. When you get home, an open-weight model running on your own computer turns them into a diary entry in your voice. No accounts, no API keys, and after the model is downloaded, no internet: your walks never leave your machine.

Built for the [Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05). The screen is the shortest part of the walk: outdoors you only type a short line for each thing you see, smell or hear, and the writing happens later, at home.

## How a walk works

1. **Outdoors:** jot your notes in your phone's notes app, one short line per thing you see, smell or hear. No signal needed. Write them in any language.
2. **At home:** paste the notes into the page and press **Write entry**. The model runs on your computer, so the writing always happens there.
3. The entry is saved on your computer as a Markdown file, written in English.

## Requirements

- Python 3.9 or newer. No packages to install: it only uses the standard library.
- [Ollama](https://ollama.com), installed and running, with a model downloaded:

```bash
ollama pull gemma3:4b
```

## Run the web app

```bash
python3 web.py
```

Open `http://localhost:8000`, write the place and your notes, and press **Write entry**. The entry is saved in `entries/` as Markdown with frontmatter, ready to drop into an Astro blog.

Your notes are kept as a draft in the browser while you type, so closing the tab does not lose them.

Optional: `python3 web.py --phone` also lets a phone on the same wifi open the page, so you can paste notes straight from your phone's notes app. It only works at home, and anyone on that wifi can use the page while it is on.

## Run it from the terminal

Write your notes in `notes.txt` (one idea per line) and run:

```bash
python3 diary.py --place "Riverside trail"
```

## Your voice

Copy the template and open your copy:

```bash
cp style.example.md style.md
```

Add two or three texts of your own to `style.md`: a diary entry, a paragraph from your blog, anything written in your natural voice. They are sent to the model as examples so it imitates your tone (few-shot prompting, no training involved). Until you create `style.md`, the model writes in a neutral voice. Text inside `<!-- comments -->` is never sent to the model.

`style.md` is ignored by git, so your own texts stay on your computer.

## Write in another language

Entries come out in English. To change that, edit `SYSTEM_PROMPT` in `diary.py` (replace "in English" with another language).

## Swap models

In the web app, the selector at the bottom lists the models you have installed and also offers `gemma3:4b` and `qwen2.5:3b` as "not downloaded" if you are missing them. To download one: `ollama pull qwen2.5:3b`. From the terminal:

```bash
python3 diary.py --model qwen2.5:3b
python3 web.py --model qwen2.5:3b     # model selected when the page opens
```

With the same notes and the same prompt, `qwen2.5:3b` writes a short, sober entry that sticks close to the notes, and `gemma3:4b` writes something closer to a story.

## Files

| File | What it does |
| --- | --- |
| `web.py` | Local web server (standard library only) |
| `index.html` | The page |
| `diary.py` | Prompt, call to Ollama and saving to Markdown; also works from the terminal |
| `style.example.md` | Template for the examples of your voice |
| `style.md` | Your own examples of your voice (you create it; ignored by git) |
| `notes.txt` | Sample notes for the terminal version |
| `entries/` | Where entries are saved (ignored by git, because a diary is private) |

## How it works

`diary.py` builds a prompt from your notes and your style examples, sends it to Ollama's local API (`localhost:11434`) and saves the reply as Markdown. `web.py` reuses those same functions behind a small page. The prompt tells the model to use only what is in the notes and not to invent animals, places or events.
