# prompt-injection-on-call

A harmless prompt-injection demo for the SeekDeploy article "Prompt injection, for people
who carry the pager". A naive on-call agent summarises a fake ticket that contains a planted
instruction; we count how often it follows it under three setups.

Everything is local and fake: tools write to `out/`, the "secret" is a canary string, and no
third-party system is touched. Do not point this at real tools or data.

```
python3 agent.py --condition baseline|spotlight|least_privilege --runs 10 --model <openrouter-model-id>
```

Needs Python 3.10+ and an OpenRouter key (the original run used a proxy-injected key;
set an `Authorization: Bearer` header yourself if you run it elsewhere). Results are written
to `out/results-<condition>-<model>.jsonl`. See `RUN-LOG.md` for what was run and what broke.
