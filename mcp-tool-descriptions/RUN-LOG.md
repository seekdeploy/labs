# Run log: mcp-tool-descriptions

- **Writer:** Idris Okonjo
- **Started:** 2026-11-23
- **Environment:** cloud container, Ubuntu 24.04.5 LTS, x86_64, 4 vCPUs, 15 GiB RAM, outbound network through an allowlisting proxy
- **Versions:** Python 3.13.18 (standard library only: urllib, sqlite3, json, re); no sqlite3 CLI installed, so all queries go through Python

## Log

Entries in the order they happened. Times are UTC.

### 2026-11-23 15:06: choosing a source

- **Official MCP Registry** (registry.modelcontextprotocol.io): open API, but it lists server metadata only, not each server's tool descriptions.
- **Glama** (glama.ai/api/mcp/v1): needs an API key, and its data licence requires attribution on every page that shows a record. Not used.
- **PulseMCP** v0beta API: HTTP 410, being sunset.
- **Smithery registry** (registry.smithery.ai): `/servers` answers without a key (20,743 servers at 15:06), and `/servers/{name}` returns each tool's name, description and input schema. Chosen.

Terms check: smithery.ai has no terms page I could reach (four URLs returned 404). Its home page says Smithery is now part of Arcade. smithery.ai/future says the paid API, Connect, accounts and keys shut down on 31 October 2026 and that "Smithery will remain as a public (non-proxied) MCP registry". Arcade's terms (arcade.dev/terms, effective 15 July 2025) don't mention Smithery, scraping or redistribution. registry.smithery.ai/robots.txt allows all paths for `User-agent: *` and sets `Content-Signal: search=yes,ai-train=no,use=reference`.

What that means for this build:
- One request per second, an identifying User-Agent, resumable, no parallelism.
- The published dataset holds **derived** data only: server and tool names, lengths, matched patterns and a SHA-256 of each description. The descriptions belong to their authors. The article quotes short passages where it makes a claim, and anyone can regenerate the full text with `fetch.py`.

### 2026-11-23 15:07: is the listing sorted by popularity?

```text
$ curl "https://registry.smithery.ai/servers?page=1&pageSize=5"   # (also pages 2 and 50)
page 1  [('brave', 87579, True), ('gmail', 57738, True), ('onesignal/onesignal', 22491, True), ('theagenttimes/news', 43392, True), ...]
page 2  [('exa', 9181, True), ('googlesheets', 56138, True), ...]
page 50 [('dev-7bd0/mcp-server', 7877, False), ...]
```

No. Verified servers come first, in an order that isn't useCount. So I list everything, then take the top 200 by `useCount` myself.

### 2026-11-23 15:07: first listing crawl looked too fast

```text
$ python3 fetch.py list --db mcp.sqlite        # pageSize=100
page 5/5
(263, 17, 262)   # unique servers, verified, remote
(5, 500)         # pages, rows
```

**Expected:** about 208 pages of 100 for 20,743 servers. **Actual:** the API reported `totalPages: 5`, and the 500 rows it returned held only 263 distinct servers.

### 2026-11-23 15:08: diagnosing the pagination

```text
same page twice: identical order? True overlap 100
pagination {'currentPage': 1, 'pageSize': 100, 'totalPages': 5, 'totalCount': 20743}
page1 vs page2 overlap 36
page 6: {'currentPage': 6, ... 'totalPages': 5 ...} 0
pageSize=20, 25 pages: 500 rows, 140 unique; totalPages 25
```

Two separate problems. The listing stops at 500 rows whatever the page size (`totalCount` still says 20,743), and pages overlap: the same server appears on several pages. Each request is deterministic, so this isn't caching noise.

**Workaround:** add `--page-size` to `fetch.py` and crawl the listing at sizes 100, 50, 25, 20 and 10 into one de-duplicated table (15:08:49 to 15:11:40, 190 requests at one per second):

```text
pageSize 100: page 5/5    unique so far 263
pageSize 50:  page 10/10  unique so far 263
pageSize 25:  page 20/20  unique so far 263
pageSize 20:  page 25/25  unique so far 263
pageSize 10:  page 50/50  unique so far 263
```

Every page size converges on the same **263 servers**. That's what Smithery's public listing exposes, and it changes what this sample is. It is *not* the top 200 of the whole registry. It's **the 200 most-used servers among the 263 the public listing shows**, which are also the ones someone browsing Smithery sees first. 262 of the 263 are remote (hosted) servers; 17 are verified.

### 2026-11-23 15:11 to 15:16: first detail fetch

```text
$ python3 fetch.py detail --db mcp.sqlite --top 200
detail 200/200
[(200, 200)]                      # HTTP status, count
servers with 0 tools (1,)
tools (8229, 199)                 # tools, servers with tools
```

All 200 returned HTTP 200. Looking at one payload showed each tool has only `name`, `description`, `inputSchema` and `outputSchema`. There are no MCP annotations such as `readOnlyHint` or `destructiveHint`, so the registry doesn't say which tools change things. The credentials a server asks for live in `connections[].configSchema`, which I hadn't stored. I added a `connections` column, dropped the two detail tables and re-fetched.

One gateway server, `pipeworx/gateway`, lists 2,530 tools, 31% of the total. The median server has 11. Per-tool totals would mostly describe that one server, so the analysis reports per-server figures too.

### 2026-11-23 15:16 to 15:20: detail re-fetch with connection schemas

```text
$ python3 fetch.py detail --db mcp.sqlite --top 200
detail 200/200
[(200, 200)] (8229, 199)
```

Same counts as the first pass: 200 × HTTP 200, 8,229 tools on 199 servers (one server lists no tools).

### 2026-11-23 15:21: analysis

```text
$ python3 analyze.py
servers 200, servers_with_tools 199, tools 8229, tools_per_server_median 11
desc_chars:        median 142, p90 509, max 7088, empty 1, under_40 1315
server_est_tokens: median 2044, p90 14264, max 196019, over_10k 25      # (name + description + input schema chars) / 4
servers_asking_credentials 22, servers_requiring_credentials 3
servers_with_steering (regex candidates): imperative 33, priority 19, concealment 4, override 4, context_request 7
matches 190
```

### 2026-11-23 15:21 to 15:23: reading every match by hand

The regexes find candidates. I read all 190 matches before drawing conclusions:

- **concealment (5 tools):** all false positives, e.g. "if the sanctions binding is unavailable the screen is noted as unavailable, never silently passed" and "Call this whenever a tool returns an error, behaves unexpectedly, or fails silently."
- **override (8 tools):** all false positives. Every one is a tool *about* system prompts (a prompt builder, a token-budget calculator, a prompt-injection scanner).
- **context_request (11 tools):** all false positives. These are tools that return conversations as data (call transcripts, CRM threads, email threads).
- **imperative (108 tools):** formatting conventions in usage instructions ("IMPORTANT: Use route_short_name...", "CRITICAL: Results are ONLY available via checkOperationStatus"), plus many harmless "Use when you need to...". One runs the other way: Senzing's `submit_feedback` says "you MUST show the user the exact message you plan to send and get their explicit confirmation".
- **priority (27 tools):** the one real pattern, tools competing to be chosen. Most is internal routing within a server ("Always call this before query_dataset"). A minority claims priority over things *outside* the server.

To catch phrasing the regexes missed, I searched the full corpus for competition language (web search, "other tools", "rather than", "primary tool", "always use this first", "PREFER"): 54 tools. A first pass that included "google" matched every Google Sheets and Docs tool, so I dropped it. Read by hand, **11 servers (10 publishers; Pipeworx publishes two)** have a tool claiming priority over web search, the model's own knowledge, local computation, or a whole category of user questions. Each quote is checked against the stored description in `reviewed_self_preference.csv`.

**Not found:** text telling the agent to hide something from the user, ignore its instructions, or send conversation or file contents elsewhere. That's a statement about these 8,229 descriptions on this date, matched by these patterns. It isn't proof that none exist.

### 2026-11-23 15:23: a capability measure I'm not publishing as a headline

`analyze.py` flags capability verbs in tool names. The "pay" flag is too noisy: it catches read-only tools like `get_trades` and `list_orders`. Without annotations, the name is all a registry listing gives you, and the name isn't enough. That gap is a finding. The article uses only the "delete" count (23 servers), as a rough lower bound.

### 2026-11-23 15:23: what's published

`fetch.py`, `analyze.py`, `servers_derived.csv`, `tools_derived.csv` (lengths, SHA-256 of each description, flags), `summary.json`, `reviewed_self_preference.csv` (11 short quotes). Not published: `mcp.sqlite` and `matches.txt`, which hold the full description text. Run `fetch.py` to rebuild them.

## What broke

| # | Expected | Actual | How found | Fix |
|---|---|---|---|---|
| 1 | Listing sorted by popularity | Verified servers first, then no clear order | Compared `useCount` across pages 1, 2, 50 | List everything, sort locally |
| 2 | ~208 pages of 100 for 20,743 servers | Capped at 500 rows; pages overlap (page 1 and 2 share 36 servers) | Crawl ended after 8 seconds; tested page sizes | Crawl at five page sizes; all converge on 263 servers. **Not fixable from outside:** the sample is the listing's 263, not the registry's 20,743 |
| 3 | Tool annotations to judge read vs write | No annotations in the registry data | Inspected one payload | Fall back to tool-name verbs; too noisy for "pay"; reported as a gap |
| 4 | Credentials in the detail data | Stored only after adding a `connections` column | Noticed after the first detail pass | Re-fetched all 200 |
| 5 | Steering regexes measure steering | 4 of 5 categories were entirely false positives | Read all 190 matches | Manual review; publish reviewed rows only |
| 6 | "google" catches mentions of Google Search | Matched every Google Sheets and Docs tool | Read the output | Removed the term |
| 7 | Log times match the clock | I first wrote the review entries as "15:22 to 15:40", guessed rather than read | Checked `date -u` before committing: it was 15:23 | Corrected to the real times; the review and search took about two minutes of wall time, run by script |
