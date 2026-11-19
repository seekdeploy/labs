"""Baseline: send only :wq<CR> (no edit) to measure save-and-exit overhead."""
import sys
from run import run_once, EMPTY_HX_CONFIG
from tasks import FIXTURE
open(EMPTY_HX_CONFIG, "w").close()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
noop = {"id": "t0-noop", "expected": FIXTURE, "nvim": [], "hx": []}
for ed in ("nvim", "hx"):
    rs = [run_once(ed, noop) for _ in range(n)]
    s = sorted(r["seconds"] for r in rs)
    print(f"t0-noop {ed:4} correct={sum(r['ok'] for r in rs)}/{n} median={s[n//2]}s min={s[0]}s max={s[-1]}s")
