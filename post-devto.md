---
title: A diary that writes itself after your walk (Gemma running on my laptop)
published: false
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

Field Diary is for people who love a walk but forget what they noticed by the time they get home.

Outdoors, you only jot down a few words for each thing you see, smell or hear. At home, an open-weight model running on my laptop turns those scraps into a diary entry that sounds like me.

The screen is the shortest part of the walk. Each note is one short line in my phone’s notes app and takes a few seconds. The writing happens later, when I am sitting down anyway.

I made it for myself. I am a first-year web development student in Spain, and I wanted to keep a record of my walks without turning them into more screen time.

Outdoors I only use my Xiaomi's notes app. At home I paste the notes into the page, press one button, and the model on my laptop does the writing. For the tests in this post I ran the same thing from the terminal instead, reading the notes from a text file.

## Demo

{% embed https://youtu.be/t_7lboKqb68 %}

[Watch the demo on YouTube](https://youtu.be/t_7lboKqb68)

The notes can be in any language; the entries come out in English. I jot mine down in Spanish.

## Code

{% embed https://github.com/itsnazaretdev/hackaton-touchGrass %}

## How I Built It

- **Model:** Gemma 3 (4B), Google's open-weight model, served locally by [Ollama](https://ollama.com).
- **App:** Python standard library only. A tiny web server plus one `index.html` with plain JavaScript. No frameworks, no packages.
- **Prompt:** the model is told to use *only* what is in my notes and not to invent animals, places or events.
- **My voice:** a file called `style.md` holds a few of my own texts. They go into the prompt as examples, so the model imitates my tone. There is no training and no fine-tuning: to change the style I edit a text file.
- **Output:** each entry is saved as Markdown with frontmatter, ready for my Astro blog.
- **Model selector:** the page lists the models installed in Ollama, so I can swap them with one click.

### Two models, same notes

I ran the same five notes and the same prompt through two models.

**qwen2.5:3b**
wrote one tidy paragraph that reads like a summary:
> Today, I ventured to Nombre del Parque and was greeted by the vibrant scene of kids playing football. The sky was clear, with no clouds in sight, and the temperature was just right, making it perfect for a stroll. The days are indeed getting shorter, which is a melancholic thought as it means the fading light at dusk has me yearning for longer nights. People strolled with their furry companions, adding a playful touch to the serene park atmosphere.

**gemma3:4b**
wrote two paragraphs with more rhythm and more feeling:
> The Parque María Zambrano was buzzing today. A group of kids were really getting into a football game, the shouts and the thud of the ball against the ground a constant rhythm. The sky was just… blue. Completely blue, not a single cloud to be seen. It was warm, a really nice warmth, and I could feel the sun on my skin. 

> It feels like the days are shrinking. They’re getting shorter and shorter, and I noticed it especially here, with the light already starting to slant. I saw people walking, mostly with dogs – a few Labradors and a golden retriever, pulling gently on their leashes. There was a gentle, steady flow of people, just enjoying the afternoon.

I preferred Gemma because it sounds more like me.

Both models added details that were not in my notes (see the five lines in the next section). Gemma named "a few Labradors and a golden retriever" and added "the sun on my skin" and "the light already starting to slant", when my notes only said people were walking dogs and the days were getting short. Qwen turned the shortening days into "nature at its peak vibrancy", which is not what I wrote. My prompt says to use only the notes, so that rule reduces the invention but does not remove it, and I read every entry before keeping it.

I also learned that the model can only be as specific as I am. With short notes, the entry was generic. When I wrote down smells, sounds and how I felt, the entry got much better.

### What didn't work

After the Python version worked, I tried to make it easier to try by moving it to Astro, with Gemma running inside the browser (WebLLM). It worked in Chrome on my Mac. A friend opened it on her iPhone, the model download reached 100%, and then nothing is written. I did not have time to find out why, so I decided not to ship it.

So this submission is the Ollama version, which runs on a laptop.

### Taking it outside

I went yesterday to the park on the south side of my city and wrote my notes in my phone’s notes app, one short line for each thing I noticed. 

Typing on the phone didn’t bother me. It took a few seconds per line and I put it away straight after.

Still, writing on paper is always a pleasure, and something traditional adds authenticity that a screen doesn’t. That is the one thing I’d change: a version where you could photograph a handwritten page and have the model read it would suit this idea even better.

## Why Does Open Innovation Matter?

- **Privacy.** A diary is about as personal as data gets: places, routines, how I felt. With an open model my notes and entries stay on my laptop. The only time it needs the internet is to download the model once.
- **No account, no cost.** There is no API key and no bill, so anyone can run it.
- **Swapping models.** Switching models is one click, and the comparison above shows why that matters: each model has its own voice, and I got to choose the one that sounds like me.
- **Control over the style.** I shaped the tone by editing a plain text file, not by asking a company to change its model.

A closed API would have been easier to set up. But I could not have kept my diary off someone else's server, and I could not have chosen a voice.

## My Agent Session

I built this project with the help of Claude, an AI assistant. It helped me write the Python code and the page, and I made the decisions about the idea, the style, which model to use and what to ship. I also tested it myself on a real walk and wrote the notes in this post.

## Prize Categories

**Best Use of Gemma:** Gemma 3 (4B) runs locally through Ollama and writes every entry.