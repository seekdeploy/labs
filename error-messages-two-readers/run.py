"""Collect each error, then let a scripted agent act on the message text alone.

Usage: python3 run.py            -> writes results.json and prints a summary

The scripted agent has no model and no knowledge of any CLI. Its rules were
fixed before the first run (see RUN-LOG.md) and are the same for every case:

  R1  quoted or backticked text whose first word is an executable on PATH
  R2  a line whose first word is an executable on PATH, after stripping common
      log prefixes (error:, fatal:, hint:, "npm error", ...) and "# comments"
  R3  a "did you mean" / "most similar command" suggestion, substituted for the
      closest-matching word of the original command

It tries at most three candidates in that order. R1/R2: run the candidate,
then rerun the original command. R3: run the corrected command instead.
Resolved = the (re)run exits 0. A candidate containing a placeholder
(path/to, <...>, example.com, "Your Name", "...") is flagged.
"""
import difflib, json, os, re, shutil, subprocess, tempfile
from cases import CASES

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = re.compile(r"^\s*(?:\w+ (?:error|ERR!|warn|WARN)|error:|fatal:|hint:|warning:|ERROR:)\s*")
SUGGEST = re.compile(
    r"(?:did you mean|most similar commands? (?:is|are)|perhaps you meant)[:\s]*\n?\s*['\"`]?([\w.-]+)",
    re.I)
PLACEHOLDER = re.compile(r"path/to|<[^>]+>|example\.com|your name|\.\.\.", re.I)

def sh(cmd, cwd, env, timeout=60):
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr

def is_exe(word):
    return bool(word) and shutil.which(word) is not None

def candidates(text, original):
    found = []
    for m in re.finditer(r"`([^`\n]+)`|'([^'\n]+)'|\"([^\"\n]+)\"", text):
        c = next(g for g in m.groups() if g).strip()
        if is_exe(c.split()[0] if c.split() else ""):
            found.append(("R1", c))
    for line in text.splitlines():
        line = PREFIX.sub("", line).split(" #")[0].strip()
        if line.split() and is_exe(line.split()[0]) and len(line.split()) > 1:
            found.append(("R2", line))
    for m in SUGGEST.finditer(text):
        sug = m.group(1)
        words = re.findall(r"[\w.-]+", original)
        close = difflib.get_close_matches(sug, words, n=1, cutoff=0.5)
        if close and close[0] != sug:
            found.append(("R3", re.sub(r"\b%s\b" % re.escape(close[0]), sug, original, count=1)))
    seen, out = set(), []
    for rule, c in found:
        if c not in seen:
            seen.add(c); out.append((rule, c))
    return out[:3]

def run_case(case):
    d = tempfile.mkdtemp(prefix="err-")
    env = {"PATH": os.environ["PATH"], "HOME": d, "GIT_CONFIG_NOSYSTEM": "1",
           "LANG": "C.UTF-8", "TERM": "dumb"}
    for k in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy",
              "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS", "RUSTUP_HOME"):
        if k in os.environ:
            env[k] = os.environ[k]
    env.setdefault("RUSTUP_HOME", os.path.expanduser("~/.rustup"))
    env["CARGO_HOME"] = os.path.expanduser("~/.cargo")
    code, out, err = sh(case["setup"], d, env)
    if code != 0:
        return {"id": case["id"], "cli": case["cli"], "setup_failed": True, "stderr": err}
    cwd = os.path.join(d, case.get("cwd", ""))
    code, out, err = sh(case["cmd"], cwd, env)
    msg = (err + out).strip()
    attempts, resolved = [], False
    for rule, c in candidates(msg, case["cmd"]):
        if rule == "R3":
            rc, o, e = sh(c, cwd, env)
            cand_rc, cand_out = rc, (e + o).strip()
        else:
            cand_rc, co, ce = sh(c, cwd, env)
            cand_out = (ce + co).strip()
            rc, o, e = sh(case["cmd"], cwd, env)
        attempts.append({"rule": rule, "candidate": c, "exit": rc,
                         "candidate_exit": cand_rc, "candidate_output": cand_out[:600],
                         "placeholder": bool(PLACEHOLDER.search(c)),
                         "after": (e + o).strip()[:400]})
        if rc == 0:
            resolved = True
            break
    shutil.rmtree(d, ignore_errors=True)
    return {"id": case["id"], "cli": case["cli"], "cmd": case["cmd"], "exit": code,
            "message": msg, "attempts": attempts, "resolved": resolved}

def main():
    results = [run_case(c) for c in CASES]
    json.dump(results, open(os.path.join(HERE, "results.json"), "w"), indent=2)
    for r in results:
        if r.get("setup_failed"):
            print(f'{r["id"]:24} SETUP FAILED: {r["stderr"][:200]}')
            continue
        a = r["attempts"]
        tag = "RESOLVED" if r["resolved"] else ("tried" if a else "no-candidate")
        ph = " (placeholder)" if any(x["placeholder"] for x in a) else ""
        print(f'{r["id"]:24} exit={r["exit"]:<3} {tag}{ph}  '
              + "; ".join(f'{x["rule"]}:{x["candidate"]!r}->{x["exit"]}' for x in a))

if __name__ == "__main__":
    main()
