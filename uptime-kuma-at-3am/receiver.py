"""Webhook receiver standing in for a pager. Logs every POST to ./logs/alerts.jsonl.
Mode lives in ./state/receiver: 'ok' returns 200, 'fail' returns 500 (and still logs the attempt)."""
import http.server, json, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent
MODE = HERE / "state" / "receiver"
LOG = HERE / "logs" / "alerts.jsonl"

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        mode = MODE.read_text().strip() if MODE.exists() else "ok"
        try: data = json.loads(body)
        except Exception: data = {"raw": body.decode(errors="replace")}
        rec = {"received": time.strftime("%FT%TZ", time.gmtime()), "receiver_mode": mode,
               "msg": data.get("msg"), "status": (data.get("heartbeat") or {}).get("status"),
               "heartbeat_time": (data.get("heartbeat") or {}).get("time")}
        with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
        self.send_response(200 if mode == "ok" else 500); self.end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    MODE.parent.mkdir(exist_ok=True); LOG.parent.mkdir(exist_ok=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", 8082), H).serve_forever()
