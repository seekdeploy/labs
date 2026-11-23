# What agents are told: the tool descriptions of 200 MCP servers

Build for [What agents are told: I read the tool descriptions of 200 MCP servers](https://seekanddeploy.io/news/mcp-tool-descriptions) by Idris Okonjo.

## What this is

A script that downloads MCP server tool descriptions from the public Smithery registry into SQLite, and one that measures them: length, how much text each server loads into an agent's context, what credentials servers ask for, and text that tries to steer the agent. The published data covers the 200 most-used servers among the 263 that Smithery's public listing exposed on 23 November 2026.

## Files

- `fetch.py`: polite crawler (1 request/second, identifying User-Agent, resumable)
- `analyze.py`: metrics and pattern matching
- `servers_derived.csv`: one row per server
- `tools_derived.csv`: one row per tool (8,229 rows): lengths, SHA-256 of the description, flags
- `summary.json`: headline numbers
- `reviewed_self_preference.csv`: the 11 hand-reviewed cases of tools claiming priority over things outside their server, with short quotes
- `RUN-LOG.md`: every command and what broke

The full descriptions are not redistributed here. They belong to the server authors, and the registry marks its content `use=reference`. Run the scripts to rebuild them.

## Requirements

Python 3.10+, standard library only. Network access to registry.smithery.ai.

## Run it

```bash
for ps in 100 50 25 20 10; do python3 fetch.py list --db mcp.sqlite --page-size $ps; done
python3 fetch.py detail --db mcp.sqlite --top 200
python3 analyze.py --db mcp.sqlite
```

Results will differ: the registry changes daily.

## What broke

The registry's listing stops at 500 rows and repeats servers across pages, so only 263 of its 20,743 servers can be reached by paging. Four of the five steering-pattern categories turned out to be entirely false positives on manual review. See [RUN-LOG.md](RUN-LOG.md#what-broke).
