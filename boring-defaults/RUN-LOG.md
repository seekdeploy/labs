# Run log: boring-defaults

- **Writer:** Wren Halloran
- **Started:** 2026-11-23
- **Environment:** SeekDeploy cloud container, Ubuntu 24.04.5 LTS, Linux 6.18 x86_64, 4 vCPU. Outbound HTTPS goes through a proxy that refuses GitHub archive downloads (see What broke #1).
- **Versions:** Neovim v0.12.6 (official release tarball), LazyVim v16.0.2 via the LazyVim starter at commit `803bc18`, nvim-treesitter `52773f0d` (main, 2026-11-21), stylua 2.6.0 (installed by mason), tmux 3.4, git 2.43.0, gcc present. `fd` and `lazygit` not installed (both optional).
- **Isolation:** everything ran with `HOME` and all `XDG_*` directories inside a scratch folder, so no config from the machine leaked in.
- **Times:** headings use the file modification time (UTC) of each output in `logs/`.

## Log

### 2026-11-23 15:28 UTC: clean install, following the official steps

`install.sh` does exactly what https://www.lazyvim.org/installation says:
clone `LazyVim/starter` into `~/.config/nvim` and remove its `.git`. The one
deviation: instead of opening `nvim` and watching, it runs
`nvim --headless "+Lazy! sync" +qa` so the output can be logged.

```text
== nvim: NVIM v0.12.6
== starter commit: 803bc18
...
HEAD is now at 0fa4a847 chore(main): release 16.0.2 (#7290)
== sync took 8s
```

Full output: `logs/01-install.txt`. What it installed (`logs/02-what-installed.txt`):

- 32 plugins, all pinned in `lazy-lock.json` (copied to `logs/`)
- 162 MB under `~/.local/share/nvim`, 76 KB of config
- The starter's own Lua: `init.lua` (2 lines), `lua/config/lazy.lua` (53),
  `options.lua` (3), `keymaps.lua` (3), `autocmds.lua` (8), all comments
  except `init.lua` and `lazy.lua`. `lua/plugins/example.lua` is 197 lines but
  starts with `if true then return {} end`, so it loads nothing.

### 15:28: first interactive start, in tmux

Opened `app.py` in a 120x35 tmux pane and captured the screen at about 3, 30
and 90 seconds. At 3 s the notifications read:

```text
nvim-treesitter/install/printf error: Error du…
nvim-treesitter: Installed 3/27 languages
mason-lspconfig.nvim lua_ls was successfully i…
```

The rest of the screen showed `Downloading tree-sitter-…` messages. mason
installed `lua-language-server`, `shfmt`, `stylua` and `tree-sitter` into
`~/.local/share/nvim/mason/bin`. `logs/mason.log` ends with
`Installation succeeded for Package(name=lua-language-server)`.

### 15:30: what the treesitter error was

The notifications were truncated, and `:messages` was hard to read through
tmux (What broke #2), so I reran one parser install headless:

```text
$ nvim --headless "+lua ... require('nvim-treesitter').install({'python'}):wait(240000) ..." +qa
[nvim-treesitter/install/python]: Downloading tree-sitter-python...
...
[nvim-treesitter/install/python] error: Error during download: curl: (22) The requested URL returned error: 403
```

Full output: `logs/03-ts-install-python.txt` (24 "Downloading" lines, 5 errors
printed before it returned). Afterwards there were **0** compiled parsers on
disk. The only `.so` file was `libblink_cmp_fuzzy.so`.

### 15:31: startup time

`startup.sh` opens `app.py` in a real tmux terminal with `--startuptime` and
`+qa`, 10 runs each, and reads the `--- NVIM STARTED ---` line.

```text
bare     n=10  min 28.1 ms  median 33.1 ms  max 39.1 ms   (nvim --clean)
lazyvim  n=10  min 103.8 ms median 118.5 ms max 141.5 ms  (starter config)
```

Raw runs: `logs/04-startup.txt`. Caveats: "NVIM STARTED" is the end of
Neovim's own startup; plugins LazyVim loads on `VeryLazy` can load after it.
LazyVim's `plugins/treesitter.lua` installs missing parsers from its config,
so every one of these starts happened with all parsers missing and a
background install being attempted. I could not measure the healthy state here.

### 15:31: format on save, with no configuration

LazyVim sets `vim.g.autoformat = true` (`lua/lazyvim/config/options.lua`
line 6). Opened a messy `messy.lua` in tmux, waited 5 s, `:w`, quit.

```text
== before
local   x={1,2,  3}
local function f( a,b ) return a+b end
== after :w in LazyVim (no config changes)
local x = { 1, 2, 3 }
local function f(a, b)
	return a + b
end
```

`od -c` on line 3 shows a literal `\t`. LazyVim's own options set
`expandtab = true` and `shiftwidth = 2`. The starter's `stylua.toml`
(`indent_type = "Spaces"`, width 2) lives in the config directory and does not
apply to a project elsewhere, so stylua fell back to tabs. Full output:
`logs/05-format-on-save.txt`.

## Second measurement: parsers installed by git clone (outside LazyVim's defaults)

Added on 2026-11-23 at the editor's request, after confirming that this
environment refuses GitHub archive downloads but allows `git clone`. This is
**not** LazyVim's default path. LazyVim's config was not changed.

### 17:35 UTC: list and clone

`dump-parsers.lua` asks LazyVim for its parser list
(`LazyVim.opts("nvim-treesitter").ensure_installed`, 23 languages) and records
each one's pinned `url` and `revision` from nvim-treesitter's `parsers.lua`
(`logs/parsers-lazyvim.json`). `clone-parsers.sh` fetches each repo at that
revision with `git fetch --depth 1 <url> <rev>`. All 21 repos cloned
(`logs/06-clone-parsers.txt`; typescript/tsx and markdown/markdown_inline share repos).

### 17:35-17:36 UTC: install from the local checkouts

`install-parsers-local.lua` sets each parser's `install_info.path` to its
checkout, so nvim-treesitter skips the download and runs its normal
`tree-sitter build` and install. Three attempts failed before it worked
(What broke #5 to #7). Final result:

```text
[nvim-treesitter]: Installed 23/24 languages      (logs/09-..., dtd missing)
[nvim-treesitter]: Installed 1/1 languages        (logs/10-..., dtd added)
parsers on disk: 24
```

`dtd` is not on LazyVim's list. `xml` requires it, and it lives in the same
repo and revision as `xml` (`logs/parsers-with-deps.json`). This also explains
"Installed 3/27 languages" from the first start: 24 downloadable parsers plus
`ecma`, `html_tags` and `jsx`, which are query-only and need no download.

Check under unchanged LazyVim, opening `app.py` (`logs/11-ts-active.txt`):

```text
filetype python ts_highlight_active true parser_ok true
```

### 17:36-17:37 UTC: startup with parsers present

Same `startup.sh`, 10 runs each, twice:

```text
logs/12-...  lazyvim median 169.9 ms (147.6-202.9)   bare median 33.8 ms
logs/13-...  lazyvim median 167.8 ms (143.0-198.9)   bare median 31.6 ms
```

Slower than the 118.5 ms measured with parsers missing. To rule out drift,
`startup-ab.sh` alternated the two states run by run, hiding the parsers by
renaming `site/parser` (`logs/16-startup-ab.txt`):

```text
missing  n=10 median 124.5 ms  (102.2-139.5)
present  n=10 median 167.0 ms  (147.4-195.0)
present was slower in all 10 pairs
```

Not profiled further. A single side-by-side pair of `--startuptime` logs
(`logs/14-...`, `logs/15-...`) came out the other way (110 vs 99 ms), which is
why the interleaved run exists: one pair is noise.

Disk after first start, mason tools and parsers (`logs/17-disk-after-parsers.txt`):
195 MB total: `lazy` 123 MB, `mason` 64 MB, `site` (parsers and queries) 8.6 MB.
The 162 MB in `logs/02-what-installed.txt` was taken right after the plugin
sync, before the first interactive start.

## What broke

1. **Parsers could not download.** Expected: 27 treesitter parsers built on
   first start. Actual: `curl: (22) The requested URL returned error: 403`
   for each, 0 parsers on disk. Cause: nvim-treesitter downloads
   `<repo>/archive/<rev>.tar.gz` (`lua/nvim-treesitter/install.lua` line 232),
   and this sandbox's proxy returns 403 for `github.com/.../archive/` and
   `codeload.github.com`, while `git clone` from GitHub works. Not solved:
   the build rules say not to work around network policy, so the editor
   decides whether to allow the host. Effect: no treesitter highlighting
   beyond what Neovim bundles, and a background reinstall attempt on every start.
2. **Reading notifications through tmux.** The first-start errors were
   truncated in noice popups, and `:messages` in a split was hard to capture.
   Rerunning the install headless printed the full errors.
3. **"Installed 3/27 languages" vs 0 parsers.** Resolved later: the 3 were the
   query-only languages `ecma`, `html_tags` and `jsx` (see the second measurement).
4. **Formatter and editor disagree on indentation.** Not a crash, a finding:
   see the format-on-save entry above.

5. **My first override was ignored.** Setting `install_info.path` and then
   calling `install()` still downloaded (403 again, `logs/07-...`). Cause:
   `install()` clears `package.loaded['nvim-treesitter.parsers']` and reloads it
   (`reload_parsers()`, `install.lua` line 488), firing `User TSUpdate`, so the
   change was wiped. The README says to make changes in a `TSUpdate`
   autocommand. Moving the override there fixed it.
6. **A misleading "Installed 24/24".** In the run inside LazyVim
   (`logs/07-...`), LazyVim's own background install was running for the same
   languages, and my run reported `Installed 24/24 languages` with 0 parser
   files on disk. I assume it counted languages already being installed as
   done, but I didn't confirm that. Running the install with `nvim -u NONE`
   and only nvim-treesitter on the runtime path avoided the overlap.
7. **I nested the parser folder.** For a one-off missing/present comparison I
   renamed `site/parser` away. nvim-treesitter recreated an empty `site/parser`
   while it was gone, so my `mv` back put the saved folder inside it. Noticed
   because the count read 1. Fixed by hand. `startup-ab.sh` now removes the
   empty folder before restoring.

## Clean up

tmux server killed after each step. Nothing left running. The scratch HOME
was left in the session's scratch folder and is not part of this repo.
