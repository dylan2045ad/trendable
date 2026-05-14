from __future__ import annotations

import json
import sys
import time
import urllib.parse
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trendable import SOURCES, trendable  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        limit = parse_int(params.get("limit", ["15"])[0], default=15, minimum=1, maximum=50)
        timeout = parse_float(params.get("timeout", ["10"])[0], default=10.0, minimum=2.0, maximum=20.0)

        started = time.time()
        headlines, errors = trendable(limit=limit, timeout=timeout)
        payload = {
            "triggerword": "Trendable",
            "count": len(headlines),
            "sourceCount": len(SOURCES),
            "durationSeconds": round(time.time() - started, 2),
            "headlines": [asdict(item) for item in headlines],
            "errors": [{"source": source, "error": error} for source, error in errors],
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "s-maxage=120, stale-while-revalidate=300")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_int(value: str, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def parse_float(value: str, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))
