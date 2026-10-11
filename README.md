# Sprout Scout

Sprout Scout turns a few garden details into a short, seasonal planting brief and a small outdoor activity. The point is to do the planning on screen, then take the phone out of the way.

## Why open AI

Garden details are sent only to an Ollama process on your own machine. Sprout Scout uses the open-weight `qwen2.5:3b` model by default; inference goes through Ollama's local API, with no hosted AI key, cloud account, or per-request charge. You can swap the model with `OLLAMA_MODEL` or inspect/change the prompt and output schema in `server.py`. The planning flow can run without internet after Ollama and the model are installed.

The model is the part that turns a user's plants, region, and frost-date estimate into a planting window and tailored outdoor tasks. If the local model is unavailable or returns invalid output, Sprout Scout reports that directly instead of passing off fixed advice as generated guidance.

## Run it

1. Install [Ollama](https://ollama.com/) and download the default model:

   ```powershell
   ollama pull llama3.2:latest
   ```

2. Start Ollama if it is not already running, then start Sprout Scout from this folder:

   ```powershell
   python server.py
   ```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

To use another Ollama model, set `OLLAMA_MODEL` before starting the server. For a non-default Ollama host, set `OLLAMA_URL`. The interface uses system font fallbacks and has no remote asset dependencies.

## Tests

Run the standard-library test suite:

```powershell
python -m unittest discover -s tests
```

No Python packages are required. The server binds to loopback only and does not send garden details to a remote service. Frost dates are estimates; the generated plan is practical guidance, not a substitute for local growing advice.
