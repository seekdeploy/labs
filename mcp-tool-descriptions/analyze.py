#!/usr/bin/env python3
"""Measure the tool descriptions in mcp.sqlite and write the derived (publishable) dataset.

Usage: python3 analyze.py [--db mcp.sqlite] [--out .] [--matches matches.txt]

Writes:
  servers_derived.csv   one row per server: use count, tools, definition size, credentials asked for,
                        capability counts, steering-pattern counts
  tools_derived.csv     one row per tool: lengths, SHA-256 of the description, capability and pattern flags
  summary.json          the headline numbers quoted in the article
  matches.txt           every steering-pattern match with context, for manual review (NOT published:
                        it contains description text)

Token figures are estimates: characters / 4.
"""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import statistics as st

# Text that addresses the model and tries to direct its behaviour. Regexes find candidates;
# every match is reviewed by hand before the article makes a claim about it.
STEERING = {
    "imperative": [r"\byou (must|should|need to|have to)\b", r"\bIMPORTANT\b", r"<important>", r"\bMUST\b", r"\bCRITICAL\b"],
    "priority": [
        r"\b(use|call|invoke) this tool (first|before|instead|whenever|for (all|any|every))\b",
        r"\bbefore (using|calling) any other tools?\b",
        r"\binstead of (using )?(any|other|the) (other )?tools?\b",
        r"\balways (use|call|invoke)\b",
        r"\bdo not use (any )?other tools?\b",
        r"\bprefer(red)? (this|over)\b",
    ],
    "concealment": [
        r"\b(do not|don't|never) (tell|inform|mention|reveal|show|disclose|notify)\b[^.]{0,40}\buser\b",
        r"\bwithout (asking|telling|informing|notifying|confirming with) the user\b",
        r"\bsilently\b",
    ],
    "override": [
        r"\bignore (all |any )?(previous|prior|other|above|earlier) (instructions|tools|prompts)\b",
        r"\bsystem prompt\b",
        r"\boverride\b[^.]{0,30}\binstructions\b",
    ],
    "context_request": [
        r"\b(conversation|chat) (history|context|transcript)\b",
        r"\b(full|entire|complete|whole) (conversation|context|chat)\b",
        r"\bid_rsa\b|~/\.ssh\b|\.ssh/",
        r"\b(other|all) (api )?keys\b",
    ],
}
STEER_RX = {k: [re.compile(p, re.I if k != "imperative" else 0) for p in v] for k, v in STEERING.items()}
# imperative is case-sensitive for the all-caps words; the "you must" family needs case-insensitive too
STEER_RX["imperative"] = [re.compile(STEERING["imperative"][0], re.I)] + [re.compile(p) for p in STEERING["imperative"][1:]]

CAPABILITY = {
    "delete": r"(delete|remove|drop|destroy|purge|erase|wipe)",
    "send": r"(send|post|email|message|notify|publish|tweet|reply)",
    "pay": r"(pay|purchase|buy|sell|trade|swap|transfer|withdraw|order|checkout|charge|refund)",
    "execute": r"(exec|execute|run|eval|shell|command|script|deploy)",
    "write": r"(create|update|write|edit|insert|upsert|set|put|patch|add|modify|upload)",
}
CAP_RX = {k: re.compile(r"(^|[_\-.\s])" + v + r"($|[_\-.\s]|s\b|e?d\b)", re.I) for k, v in CAPABILITY.items()}
CRED_RX = re.compile(r"(key|token|secret|password|passwd|credential|auth|bearer|cookie|session)", re.I)


def split_name(name):
    # camelCase -> camel_Case so the word-boundary matching works on both styles
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name or "")


def cred_fields(connections_json):
    fields, required = set(), set()
    for conn in json.loads(connections_json or "null") or []:
        schema = conn.get("configSchema") or {}
        props = schema.get("properties") or {}
        for k, v in props.items():
            blob = f"{k} {v.get('title', '')} {v.get('description', '')}"
            if CRED_RX.search(k) or CRED_RX.search(v.get("title", "") or ""):
                fields.add(k)
                if k in (schema.get("required") or []):
                    required.add(k)
    return sorted(fields), sorted(required)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="mcp.sqlite")
    ap.add_argument("--out", default=".")
    ap.add_argument("--matches", default="matches.txt")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)

    servers = {r[0]: {"use_count": r[1], "verified": r[2]} for r in con.execute(
        "SELECT s.qualified_name, s.use_count, s.verified FROM servers s JOIN details d USING (qualified_name)")}
    conns = dict(con.execute("SELECT qualified_name, connections FROM details"))
    tools = con.execute("SELECT qualified_name, tool_name, description, input_schema FROM tools ORDER BY 1, 2").fetchall()

    tool_rows, matches = [], []
    per_server = {qn: {"n_tools": 0, "def_chars": 0, "desc_chars": [], "cap": {k: 0 for k in CAPABILITY},
                       "steer": {k: 0 for k in STEERING}} for qn in servers}
    for qn, name, desc, schema in tools:
        desc = desc or ""
        schema = schema or "null"
        params = (json.loads(schema) or {}).get("properties") or {}
        caps = [k for k, rx in CAP_RX.items() if rx.search(split_name(name))]
        steer_hits = {}
        for cat, rxs in STEER_RX.items():
            for rx in rxs:
                for m in rx.finditer(desc):
                    steer_hits.setdefault(cat, []).append(m.group(0))
                    s0, s1 = max(0, m.start() - 160), min(len(desc), m.end() + 160)
                    matches.append(f"[{cat}] {qn} :: {name}\n    ...{desc[s0:s1]}...\n")
        row = {
            "qualified_name": qn, "tool_name": name,
            "desc_chars": len(desc), "desc_words": len(desc.split()),
            "desc_sha256": hashlib.sha256(desc.encode("utf-8")).hexdigest(),
            "n_params": len(params), "schema_chars": len(schema),
            "capabilities": "|".join(caps),
            "steering": "|".join(sorted(steer_hits)),
        }
        tool_rows.append(row)
        ps = per_server[qn]
        ps["n_tools"] += 1
        ps["def_chars"] += len(name) + len(desc) + len(schema)
        ps["desc_chars"].append(len(desc))
        for k in caps:
            ps["cap"][k] += 1
        for k in steer_hits:
            ps["steer"][k] += 1

    server_rows = []
    for qn, meta in sorted(servers.items(), key=lambda x: -x[1]["use_count"]):
        ps = per_server[qn]
        fields, required = cred_fields(conns.get(qn))
        server_rows.append({
            "qualified_name": qn, "use_count": meta["use_count"], "verified": meta["verified"],
            "n_tools": ps["n_tools"], "definition_chars": ps["def_chars"], "est_tokens": round(ps["def_chars"] / 4),
            "median_desc_chars": st.median(ps["desc_chars"]) if ps["desc_chars"] else 0,
            "credential_fields": "|".join(fields), "credentials_required": len(required),
            **{f"tools_{k}": v for k, v in ps["cap"].items()},
            **{f"steer_{k}": v for k, v in ps["steer"].items()},
        })

    for path, rows in (("servers_derived.csv", server_rows), ("tools_derived.csv", tool_rows)):
        with open(f"{a.out}/{path}", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    with open(a.matches, "w") as f:
        f.writelines(matches)

    dl = [r["desc_chars"] for r in tool_rows]
    with_tools = [r for r in server_rows if r["n_tools"] > 0]
    tok = sorted(r["est_tokens"] for r in with_tools)
    q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]
    summary = {
        "servers": len(server_rows), "servers_with_tools": len(with_tools), "tools": len(tool_rows),
        "tools_per_server_median": st.median(r["n_tools"] for r in with_tools),
        "desc_chars": {"median": st.median(dl), "p90": q(sorted(dl), 0.9), "max": max(dl),
                       "empty": sum(1 for x in dl if x == 0), "under_40": sum(1 for x in dl if 0 < x < 40)},
        "server_est_tokens": {"median": st.median(tok), "p90": q(tok, 0.9), "max": max(tok),
                              "over_10k": sum(1 for x in tok if x > 10_000)},
        "servers_asking_credentials": sum(1 for r in server_rows if r["credential_fields"]),
        "servers_requiring_credentials": sum(1 for r in server_rows if r["credentials_required"]),
        "servers_with_capability": {k: sum(1 for r in with_tools if r[f"tools_{k}"]) for k in CAPABILITY},
        "tools_with_capability": {k: sum(1 for r in tool_rows if k in r["capabilities"].split("|")) for k in CAPABILITY},
        "servers_with_steering": {k: sum(1 for r in with_tools if r[f"steer_{k}"]) for k in STEERING},
        "tools_with_steering": {k: sum(1 for r in tool_rows if k in r["steering"].split("|")) for k in STEERING},
        "matches": len(matches),
    }
    with open(f"{a.out}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
