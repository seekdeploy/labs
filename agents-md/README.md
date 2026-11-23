# AGENTS.md: docs for a reader that isn't human

Build for [AGENTS.md: docs for a reader that isn't human](https://seekanddeploy.io/news/agents-md) by Sora Villanueva.

## What this is

An `AGENTS.md` written for [sindresorhus/slugify](https://github.com/sindresorhus/slugify) (commit `99b35c2`), plus a small harness that asks a local model to plan a change to that repo, with and without the file in context, and scores each plan against a 7-item checklist. The file was never sent upstream. `results/` holds every reply.

What it measures is narrow: two free local models, one planning task, 10 seeds per condition, and no code execution. It shows whether the file changes a plan, not how much it helps a real agent.

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5), 4 vCPU, no GPU, Node.js v22.23.4
- node-llama-cpp 3.22.3 (pinned in `package.json`)
- A clone of slugify at `99b35c2`
- Models (Apache-2.0, not included): Qwen2.5-Coder-1.5B-Instruct and Qwen2.5-Coder-7B-Instruct, both `q4_k_m` GGUF from Hugging Face. The sha256 hashes are in the run log.

## Run it

```bash
npm install
git clone https://github.com/sindresorhus/slugify ../slugify && git -C ../slugify checkout 99b35c2
mkdir -p models && curl -L -o models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
node experiment.mjs models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf ../slugify AGENTS.md 10 out.json
```

The 1.5B run took about 7 minutes on the logged machine, and the 7B run about 12. The `git clone` above is a full clone so the checkout works. The logged run used a shallow clone of that same commit.

## What broke

- **My first checklist rewarded repetition.** A small model scored well by copying file names from AGENTS.md into a nonsense plan. I added a seventh check before the main runs.
- **The 3B model was skipped over its licence** (`qwen-research`). The 7B, Apache-2.0, was used instead.
- **A model-suggested command passed silently while doing the wrong thing:** `npm test --test-name-pattern=...` runs the whole suite.

Full detail in [RUN-LOG.md](RUN-LOG.md).
