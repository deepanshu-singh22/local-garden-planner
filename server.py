import json
import os
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
MAX_BODY_BYTES = 4096
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "planting_window": {"type": "string"},
        "outdoor_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "duration_minutes": {"type": "integer"},
                    "instructions": {"type": "string"},
                },
                "required": ["title", "duration_minutes", "instructions"],
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["headline", "planting_window", "outdoor_plan", "notes"],
}


class LocalModelError(Exception):
    pass


def validate_input(payload):
    if not isinstance(payload, dict):
        raise ValueError("Send a JSON object with your garden details.")

    location = payload.get("location", "")
    frost_date = payload.get("last_frost_date", "")
    plants = payload.get("plants", "")
    if not isinstance(location, str) or len(location) > 80:
        raise ValueError("Region must be 80 characters or fewer.")
    if not isinstance(frost_date, str):
        raise ValueError("Enter a valid last frost date.")
    try:
        parsed_date = date.fromisoformat(frost_date)
    except ValueError as error:
        raise ValueError("Enter a valid last frost date.") from error
    if not isinstance(plants, str) or not plants.strip() or len(plants) > 180:
        raise ValueError("List at least one plant, using 180 characters or fewer.")

    return {
        "location": location.strip() or "not specified",
        "last_frost_date": parsed_date.isoformat(),
        "plants": plants.strip(),
    }


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise LocalModelError("The local model returned an invalid plan. Try again.")
    for key in ("headline", "planting_window", "notes"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise LocalModelError("The local model returned an incomplete plan. Try again.")
    activities = plan.get("outdoor_plan")
    if not isinstance(activities, list) or not 1 <= len(activities) <= 3:
        raise LocalModelError("The local model returned an invalid activity list. Try again.")
    for activity in activities:
        if not isinstance(activity, dict):
            raise LocalModelError("The local model returned an invalid activity. Try again.")
        if not isinstance(activity.get("title"), str) or not isinstance(activity.get("instructions"), str):
            raise LocalModelError("The local model returned an incomplete activity. Try again.")
        minutes = activity.get("duration_minutes")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 5 <= minutes <= 180:
            raise LocalModelError("The local model returned an invalid activity duration. Try again.")
    return plan


def generate_plan(payload):
    garden = validate_input(payload)
    prompt = (
        f"Create a practical garden plan for {garden['plants']}. "
        f"Region: {garden['location']}. User-estimated last spring frost: {garden['last_frost_date']}. "
        f"Today's date: {date.today().isoformat()}. "
        "Give a short planting window and one to three specific outdoor activities that get the user away "
        "from screens. Make the first activity doable today. Durations must be 5 to 180 minutes. "
        "Use the supplied frost date as an estimate, not a guarantee. Do not claim to have checked live weather, "
        "soil, local regulations, or other external data. Keep advice beginner-friendly and note uncertainty. "
        "Return only the requested JSON object."
    )
    request_body = json.dumps({
        "model": MODEL,
        "stream": False,
        "format": PLAN_SCHEMA,
        "messages": [
            {
                "role": "system",
                "content": "You are Sprout Scout, a concise and cautious local garden companion. Never invent live local conditions.",
            },
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.3},
    }).encode("utf-8")
    request = Request(
        f"{OLLAMA_URL.rstrip('/')}/api/chat",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read(1024).decode("utf-8", errors="replace").strip()
        raise LocalModelError(f"Ollama could not generate a plan ({error.code}). {detail}".strip()) from error
    except (URLError, TimeoutError) as error:
        raise LocalModelError(
            f"Can't reach Ollama at {OLLAMA_URL}. Start Ollama and download {MODEL}."
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LocalModelError("Ollama returned an unreadable response. Check the local model and try again.") from error

    try:
        content = result["message"]["content"]
        plan = json.loads(content)
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise LocalModelError("The local model returned an unreadable plan. Try again.") from error
    return validate_plan(plan)


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if urlparse(self.path).path == "/api/health":
            self.send_json(200, {"model": MODEL, "inference": "local via Ollama"})
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/plan":
            self.send_json(404, {"error": "Not found."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 1 or content_length > MAX_BODY_BYTES:
                self.send_json(413, {"error": "Request must be between 1 byte and 4 KB."})
                return
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            plan = generate_plan(payload)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})
            return
        except LocalModelError as error:
            self.send_json(503, {"error": str(error)})
            return
        self.send_json(200, plan)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Sprout Scout listening on http://127.0.0.1:{port} (model: {MODEL})")
    ThreadingHTTPServer(("127.0.0.1", port), AppHandler).serve_forever()
