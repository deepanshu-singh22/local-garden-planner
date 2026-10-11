# Sprout Scout

Sprout Scout is a local-first garden planner that helps people decide what to plant, when to plant it, and what small outdoor task to do next. The goal is to spend a minute planning and then get outside instead of endlessly scrolling.

## What it does

- Accepts a location (optional), last spring frost date, and the plants you want to grow
- Generates a simple, season-aware planting window
- Suggests 1–3 practical outdoor tasks
- Keeps the experience focused on the garden, not the screen

## Why this matters

This app is designed for real-world use:
- local inference with Ollama
- no cloud AI service required
- no subscription or per-request cost
- user data stays on the machine
- model can be swapped or tuned easily

## Open-source AI used

This project uses:
- Ollama
- open-weight model: `llama3.2:latest`

It runs locally on your machine, which means:
- your garden info stays private
- it works without internet after the model is installed
- the model can be replaced with another local model anytime

## How to run

### 1. Install Ollama

Download and install Ollama from:

https://ollama.com/

### 2. Pull the model

```powershell
ollama pull llama3.2:latest
