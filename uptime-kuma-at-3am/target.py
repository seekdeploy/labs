"""A target service we control. GET / returns 200 when state is 'up', 503 when 'down'.
State lives in ./state/target (one word). Optional flapping: python3 target.py --flap SECONDS
toggles the state on a timer and logs each change to ./logs/target-changes.log."""
import argparse, http.server, pathlib, threading, time
HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / "state" / "target"
LOG = HERE / "logs" / "target-changes.log"

def now(): return time.strftime("%FT%TZ", time.gmtime())

def set_state(s):
    STATE.write_text(s)
    with open(LOG, "a") as f: f.write(f"{now()} target -> {s}\n")

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        s = STATE.read_text().strip() if STATE.exists() else "up"
        code = 200 if s == "up" else 503
        self.send_response(code); self.end_headers(); self.wfile.write(f"{s}\n".encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--port", type=int, default=8081)
    p.add_argument("--flap", type=float, default=0); a = p.parse_args()
    STATE.parent.mkdir(exist_ok=True); LOG.parent.mkdir(exist_ok=True)
    if not STATE.exists(): set_state("up")
    if a.flap:
        def flapper():
            while True:
                time.sleep(a.flap)
                set_state("down" if STATE.read_text().strip() == "up" else "up")
        threading.Thread(target=flapper, daemon=True).start()
    http.server.ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
