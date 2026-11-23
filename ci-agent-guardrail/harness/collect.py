#!/usr/bin/env python3
"""Print each PR's check results from Gitea commit statuses. Usage: collect.py URL owner/repo (token in GITEA_TOKEN)."""
import json, os, sys, urllib.request
url, repo = sys.argv[1], sys.argv[2]
def get(p):
    r = urllib.request.Request(f"{url}/api/v1/{p}", headers={"Authorization": "token " + os.environ["GITEA_TOKEN"]})
    with urllib.request.urlopen(r) as f: return json.load(f)
for pr in sorted(get(f"repos/{repo}/pulls?state=all&limit=50"), key=lambda p: p["number"]):
    st = get(f"repos/{repo}/commits/{pr['head']['sha']}/status")
    res = {s["context"].split(" / ")[-1].replace(" (pull_request)", ""): s["status"] for s in st.get("statuses", [])}
    print(f"#{pr['number']} {pr['title'][:42]:42} combined={st['state']:8} " + " ".join(f"{k}={v}" for k, v in sorted(res.items())))
