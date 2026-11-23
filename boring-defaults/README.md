# The case for boring defaults

Build for [The case for boring defaults](https://seekanddeploy.io/news/lazyvim-boring-defaults) by Wren Halloran.

## What this is

A clean LazyVim install on Neovim 0.12.6, following the official steps inside
an isolated `HOME`, with everything logged: what it installs, how long it takes
to start, what format-on-save does with no configuration, and what failed.

## Requirements

- Logged on Ubuntu 24.04.5 LTS, x86_64, with tmux 3.4, git 2.43 and gcc
- Neovim v0.12.6 official release tarball; LazyVim v16.0.2 via the starter at `803bc18`
- Network access to GitHub, including `github.com/.../archive/` downloads for treesitter parsers

## Run it

```bash
curl -sSLf -o nvim.tar.gz https://github.com/neovim/neovim/releases/download/v0.12.6/nvim-linux-x86_64.tar.gz
mkdir -p nvim && tar -xzf nvim.tar.gz -C nvim --strip-components=1
mkdir -p work/proj && printf 'def total(items):\n    return sum(i.price for i in items)\n' > work/proj/app.py
./install.sh "$PWD/nvim/bin/nvim" "$PWD/work"   # clean install into work/home
./startup.sh "$PWD/nvim/bin" "$PWD/work" 10     # bare vs LazyVim startup, 10 runs each

# Second measurement, outside LazyVim's defaults: parsers fetched with git clone
H="$PWD/work/home"; ENVS="HOME=$H XDG_CONFIG_HOME=$H/.config XDG_DATA_HOME=$H/.local/share XDG_STATE_HOME=$H/.local/state XDG_CACHE_HOME=$H/.cache"
env $ENVS PATH="$PWD/nvim/bin:$PATH" nvim --headless "+lua require('lazy').load({plugins={'nvim-treesitter'}})" "+luafile dump-parsers.lua" +qa | grep '^\[' > parsers.json
./clone-parsers.sh parsers.json "$PWD/work/parser-src"
env $ENVS PATH="$H/.local/share/nvim/mason/bin:$PWD/nvim/bin:$PATH" PARSER_SRC="$PWD/work/parser-src" PARSERS_JSON=logs/parsers-with-deps.json \
  nvim --headless -u NONE --cmd "set rtp+=$H/.local/share/nvim/lazy/nvim-treesitter" "+luafile install-parsers-local.lua" +qa
./startup-ab.sh "$PWD/nvim/bin" "$PWD/work" 10  # parsers missing vs present, interleaved
```

## What broke

- **Treesitter parsers could not download** on my test machine (HTTP 403 from
  its proxy for GitHub archive tarballs), so all 27 were missing in the main
  measurement. The second measurement fetched them with git clone instead.
- **First-start errors were truncated** in popups; a headless install printed them in full.
- **Installing parsers from git clones took three tries:** an override wiped by
  nvim-treesitter's reload, a race with LazyVim's own install, and a folder I
  nested by mistake. With them installed, startup was slower (167 vs 124 ms median).
- **stylua reformatted Lua with tabs** on save while LazyVim indents with two
  spaces, because the starter's `stylua.toml` only covers the config directory.

Full detail in [RUN-LOG.md](RUN-LOG.md).
