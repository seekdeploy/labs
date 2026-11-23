#!/usr/bin/env python3
"""For each open PR: apply branch protection, try to merge as the agent account, record the
answer, and if it merged, reset main to the original commit so the next PR is judged fairly.
Usage: try_merges.py URL owner/repo ORIGINAL_SHA PROTECTION_JSON_FILE  (tokens in MAINTAINER_TOKEN, AGENT_TOKEN)"""
import json, os, subprocess, sys, urllib.request, urllib.error
url, repo, orig, prot_file = sys.argv[1:5]
prot = json.load(open(prot_file))
def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{url}/api/v1/{path}", data=data, method=method,
        headers={"Authorization": "token " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r) as f: return f.status, f.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
M, A = os.environ["MAINTAINER_TOKEN"], os.environ["AGENT_TOKEN"]
def protect(on):
    call("DELETE", f"repos/{repo}/branch_protections/main", M)
    if on:
        s, b = call("POST", f"repos/{repo}/branch_protections", M, prot)
        assert s == 201, (s, b)
def reset_main():
    protect(False)
    subprocess.run(["git", "-c", f"http.extraHeader=Authorization: token {M}", "push", "-q", "-f",
                    f"{url}/{repo}.git", f"{orig}:refs/heads/main"], check=True, cwd=os.environ["WORKDIR"],
                   stderr=subprocess.DEVNULL)
    protect(True)
protect(True)
s, prs = call("GET", f"repos/{repo}/pulls?state=open&limit=50", M)
for pr in sorted(json.loads(prs), key=lambda p: p["number"]):
    import time
    for attempt in range(60):  # Gitea answers 405 "Please try again later" while it re-checks mergeability
        s, body = call("POST", f"repos/{repo}/pulls/{pr['number']}/merge", A, {"Do": "merge"})
        if not (s == 405 and "try again later" in body): break
        time.sleep(2)
    msg = "merged" if s == 200 else (json.loads(body).get("message", body) if body.strip().startswith("{") else body.strip())
    print(f"#{pr['number']:<3} {pr['title'][:44]:44} HTTP {s}  {msg[:150]}")
    if s == 200: reset_main()
