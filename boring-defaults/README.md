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
```

## What broke

- **Treesitter parsers could not download** in this sandbox (HTTP 403 from the
  proxy for GitHub archive tarballs), so all 27 were missing. Not worked around.
- **First-start errors were truncated** in popups; a headless install printed them in full.
- **stylua reformatted Lua with tabs** on save while LazyVim indents with two
  spaces, because the starter's `stylua.toml` only covers the config directory.

Full detail in [RUN-LOG.md](RUN-LOG.md).
