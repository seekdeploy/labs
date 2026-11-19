# Modal editing is a grammar, not a shortcut list

Build for [Modal editing is a grammar, not a shortcut list](https://seekanddeploy.io/news/modal-editing-is-a-grammar) by Wren Halloran.

## What this is

A harness that replays the same six edits in Neovim and Helix through tmux, counts the keystrokes, and checks every result byte for byte against the expected file. It shows the two grammars side by side: Neovim's verb then noun, and Helix's selection then verb.

## Requirements

- Logged on Linux x86_64 (Ubuntu 24.04.5) with tmux 3.4 and Python 3.13
- Neovim v0.12.6 and Helix 25.07.1, from the official release tarballs (sha256 sums in [RUN-LOG.md](RUN-LOG.md))

## Run it

```bash
curl -sSLf -o nvim.tar.gz https://github.com/neovim/neovim/releases/download/v0.12.6/nvim-linux-x86_64.tar.gz
curl -sSLf -o hx.tar.xz https://github.com/helix-editor/helix/releases/download/25.07.1/helix-25.07.1-x86_64-linux.tar.xz
mkdir -p dl/nvim dl/hx
tar -xzf nvim.tar.gz -C dl/nvim --strip-components=1
tar -xJf hx.tar.xz -C dl/hx --strip-components=1
python3 run.py 20       # 20 replays per editor per task; writes results.json
python3 baseline.py 20  # :wq only, to measure start-up overhead
```

Run the scripts without `python3 -I`: they import `tasks.py` from their own folder.

## What broke

- **A Helix search that edited the wrong place.** `/round(` is an unfinished regular expression in Helix, so the search matched nothing, the selection stayed on the first character of the file, and `d` deleted it. Escaping it as `/round\(` fixed it.
- **apt's Neovim was too old.** The container had no package lists, and after `apt-get update` it offered Neovim 0.9.5, so both editors come from upstream tarballs.
- **The wrong Helix tag.** Picking the newest tag chose `v0.6.0`, because Helix's calendar versions (`25.07.1`) sort below the old `v` tags.
- **`python3 -I` broke the imports.** It drops the script's folder from the module path.

The full detail is in [RUN-LOG.md](RUN-LOG.md), and raw output from every run is in `logs/`.
