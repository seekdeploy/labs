"""Replay each task in Neovim and Helix through a real terminal (tmux).

Usage: python3 run.py [runs_per_task]

For every editor x task x run:
  1. copy fixture.py to a fresh temp file
  2. start the editor on it in a detached tmux pane (80x24, escape-time 0)
  3. wait until the file is drawn on screen
  4. send the task's keys, then :wq<CR>
  5. wait for the editor to exit, then compare the file with the expected text

Timings measure scripted replay from first key to editor exit, including
tmux and process overhead. They are not human editing speed.
"""
import json, os, shutil, subprocess, sys, tempfile, time
from tasks import TASKS, keystrokes

HERE = os.path.dirname(os.path.abspath(__file__))
NVIM = os.path.join(HERE, "dl/nvim/bin/nvim")
HX = os.path.join(HERE, "dl/hx/hx")
HX_RUNTIME = os.path.join(HERE, "dl/hx/runtime")
EMPTY_HX_CONFIG = os.path.join(HERE, "hx-empty-config.toml")
SESSION = "modal"

def tmux(*args, check=True):
    return subprocess.run(["tmux", *args], capture_output=True, text=True, check=check)

def command(editor, path):
    if editor == "nvim":
        return f"{NVIM} --clean {path}"
    return f"HELIX_RUNTIME={HX_RUNTIME} {HX} -c {EMPTY_HX_CONFIG} {path}"

def send(tokens):
    for t in tokens:
        if t == "<Esc>":
            tmux("send-keys", "-t", SESSION, "Escape")
        elif t == "<CR>":
            tmux("send-keys", "-t", SESSION, "Enter")
        else:
            tmux("send-keys", "-t", SESSION, "-l", t)

def wait_for(pred, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.01)
    return False

def alive():
    return tmux("has-session", "-t", SESSION, check=False).returncode == 0

def screen():
    return tmux("capture-pane", "-p", "-t", SESSION, check=False).stdout

def run_once(editor, task):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "fixture.py")
    shutil.copy(os.path.join(HERE, "fixture.py"), path)
    tmux("kill-server", check=False)
    tmux("new-session", "-d", "-s", SESSION, "-x", "80", "-y", "24", command(editor, path))
    tmux("set-option", "-g", "escape-time", "0")
    ready = wait_for(lambda: "def total_price" in screen())
    if not ready:
        return {"ok": False, "error": "editor never drew the file", "screen": screen()}
    t0 = time.monotonic()
    send(task[editor] + [":wq", "<CR>"])
    exited = wait_for(lambda: not alive())
    t1 = time.monotonic()
    if not exited:
        snap = screen()
        tmux("kill-server", check=False)
        return {"ok": False, "error": "editor did not exit", "screen": snap}
    got = open(path).read()
    shutil.rmtree(d)
    return {"ok": got == task["expected"], "seconds": round(t1 - t0, 4),
            "got": None if got == task["expected"] else got}

def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    open(EMPTY_HX_CONFIG, "w").close()
    results = []
    for task in TASKS:
        for editor in ("nvim", "hx"):
            rs = [run_once(editor, task) for _ in range(runs)]
            secs = sorted(r["seconds"] for r in rs if "seconds" in r)
            row = {
                "task": task["id"], "editor": editor,
                "keys": "".join(task[editor]),
                "keystrokes": keystrokes(task[editor]),
                "runs": runs,
                "correct": sum(r["ok"] for r in rs),
                "median_s": secs[len(secs) // 2] if secs else None,
                "min_s": secs[0] if secs else None,
                "max_s": secs[-1] if secs else None,
                "failures": [r for r in rs if not r["ok"]][:1],
            }
            results.append(row)
            print(f'{row["task"]:26} {editor:4} keys={row["keystrokes"]:2} '
                  f'correct={row["correct"]}/{runs} median={row["median_s"]}s  {row["keys"]!r}',
                  flush=True)
    json.dump(results, open(os.path.join(HERE, "results.json"), "w"), indent=2)

if __name__ == "__main__":
    main()
