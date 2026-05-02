import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORT_HEALTH = int(os.getenv("PORT_HEALTH", "8000"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/ping":
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT_HEALTH), HealthHandler)
    print(f"Starting health server on port {PORT_HEALTH}...", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
