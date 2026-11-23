#!/usr/bin/env python3
"""Fetch MCP server listings and tool descriptions from the public Smithery registry into SQLite.

Usage:
  python3 fetch.py list   [--db mcp.sqlite] [--page-size 100]  # page through the listing
  (the listing caps out at 500 rows and repeats servers across pages, so run it with
   several page sizes; servers are de-duplicated by qualifiedName)
  python3 fetch.py detail [--db mcp.sqlite] [--top 200] # tool lists for the N most-used servers

Polite by design: one request per second, an identifying User-Agent, and resumable
(already-fetched pages and servers are skipped). Standard library only.
"""
import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://registry.smithery.ai"
UA = "seekdeploy-labs-research/1.0 (+https://github.com/seekdeploy/labs/tree/main/mcp-tool-descriptions)"
DELAY = 1.0  # seconds between requests


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = int(e.headers.get("Retry-After") or 0) or 5 * (attempt + 1)
                print(f"  HTTP {e.code} on {path}, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            return e.code, None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 3:
                print(f"  {e} on {path}, retrying", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
                continue
            return None, None
    return None, None


def connect(db):
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS pages (page_size INTEGER, page INTEGER, fetched_at TEXT, n INTEGER, PRIMARY KEY (page_size, page));
        CREATE TABLE IF NOT EXISTS servers (
          qualified_name TEXT PRIMARY KEY, display_name TEXT, description TEXT,
          use_count INTEGER, verified INTEGER, remote INTEGER, is_deployed INTEGER,
          created_at TEXT, homepage TEXT, listed_at TEXT);
        CREATE TABLE IF NOT EXISTS details (
          qualified_name TEXT PRIMARY KEY, http_status INTEGER, fetched_at TEXT, n_tools INTEGER,
          connections TEXT);
        CREATE TABLE IF NOT EXISTS tools (
          qualified_name TEXT, tool_name TEXT, description TEXT, input_schema TEXT,
          PRIMARY KEY (qualified_name, tool_name));
        """
    )
    return con


def cmd_list(con, page_size):
    page, total_pages = 1, None
    while total_pages is None or page <= total_pages:
        done = con.execute("SELECT 1 FROM pages WHERE page_size=? AND page=?", (page_size, page)).fetchone()
        if done and total_pages is not None:
            page += 1
            continue
        status, data = get(f"/servers?page={page}&pageSize={page_size}")
        time.sleep(DELAY)
        if status != 200 or data is None:
            print(f"page {page}: HTTP {status}, stopping", file=sys.stderr)
            break
        total_pages = data["pagination"]["totalPages"]
        for s in data["servers"]:
            con.execute(
                "INSERT OR REPLACE INTO servers VALUES (?,?,?,?,?,?,?,?,?,?)",
                (s.get("qualifiedName"), s.get("displayName"), s.get("description"), s.get("useCount"),
                 int(bool(s.get("verified"))), int(bool(s.get("remote"))), int(bool(s.get("isDeployed"))),
                 s.get("createdAt"), s.get("homepage"), now()),
            )
        con.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?)", (page_size, page, now(), len(data["servers"])))
        con.commit()
        if page % 20 == 0 or page == total_pages:
            print(f"pageSize {page_size}: page {page}/{total_pages}")
        page += 1


def cmd_detail(con, top):
    rows = con.execute(
        "SELECT qualified_name FROM servers ORDER BY use_count DESC, qualified_name LIMIT ?", (top,)
    ).fetchall()
    for i, (qn,) in enumerate(rows, 1):
        if con.execute("SELECT 1 FROM details WHERE qualified_name=?", (qn,)).fetchone():
            continue
        status, data = get("/servers/" + urllib.parse.quote(qn, safe="/@"))
        time.sleep(DELAY)
        tools = (data or {}).get("tools") or []
        for t in tools:
            con.execute(
                "INSERT OR REPLACE INTO tools VALUES (?,?,?,?)",
                (qn, t.get("name"), t.get("description"), json.dumps(t.get("inputSchema"), sort_keys=True)),
            )
        conns = json.dumps((data or {}).get("connections"), sort_keys=True)
        con.execute("INSERT OR REPLACE INTO details VALUES (?,?,?,?,?)", (qn, status, now(), len(tools), conns))
        con.commit()
        if i % 25 == 0 or i == len(rows):
            print(f"detail {i}/{len(rows)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "detail"])
    ap.add_argument("--db", default="mcp.sqlite")
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--page-size", type=int, default=100)
    a = ap.parse_args()
    con = connect(a.db)
    cmd_list(con, a.page_size) if a.cmd == "list" else cmd_detail(con, a.top)


if __name__ == "__main__":
    main()
