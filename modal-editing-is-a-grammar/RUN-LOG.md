# Run log: Modal editing is a grammar, not a shortcut list

Writer: Wren Halloran. Run on 2026-11-15 (UTC) in a SeekDeploy cloud session.

## Environment

- OS: Ubuntu 24.04.5 LTS, Linux 6.18.44, x86_64, 4 vCPU (Intel Xeon @ 2.30GHz)
- tmux 3.4, Python 3.13.18
- Neovim **v0.12.6**: official release tarball `nvim-linux-x86_64.tar.gz`
  (sha256 `474430d53e6264f6d6dd18db42d6dc9df3a1b56ca9e88a325bbf860e1a811d87`)
- Helix **25.07.1 (a05c151b)**: official release tarball
  `helix-25.07.1-x86_64-linux.tar.xz`
  (sha256 `3f08e63ecd388fff657ad39722f88bb03dcf326f1f2da2700d99e1dc40ab2e8b`)
- Both editors started with no user config: `nvim --clean`, and
  `hx -c hx-empty-config.toml` (an empty file) with `HELIX_RUNTIME` pointed at
  the tarball's `runtime/`.

## Reproducing

`run.py` expects the two release tarballs unpacked under `dl/nvim/` and
`dl/hx/`. They are not committed. Fetch them with the `curl` commands below
and check them against the sha256 sums above, then
`tar -xzf nvim.tar.gz -C dl/nvim --strip-components=1` and
`tar -xJf hx.tar.xz -C dl/hx --strip-components=1`. Raw console output from
every run is in `logs/`.

## Method

`fixture.py` is a seven-line Python file. `tasks.py` defines six edits, each
written once in Neovim's grammar and once in Helix's. `run.py` replays each
edit through a real terminal:

1. copy the fixture to a fresh temp file
2. start the editor in a detached tmux pane (80x24, `escape-time 0`)
3. wait until `def total_price` is on screen
4. send the keys with `tmux send-keys`, then `:wq<CR>`
5. wait for the editor to exit and compare the file byte for byte with the
   expected result

Keystrokes: `<Esc>` and `<CR>` count as one; every other character counts as
one. `:wq<CR>` is not counted because both editors use the same keys.

**What the timings are not.** Nobody typed. Timings run from the first key
sent by the script to the editor exiting, and include tmux and process
overhead. They say nothing about how fast a person edits in either editor.

## Commands

```
apt-get install -y neovim tmux          # failed, see What broke #1
apt-get update && apt-get install -y neovim   # gave 0.9.5, not used
curl -sSLf -o nvim.tar.gz https://github.com/neovim/neovim/releases/download/v0.12.6/nvim-linux-x86_64.tar.gz
curl -sSLf -o hx.tar.xz https://github.com/helix-editor/helix/releases/download/25.07.1/helix-25.07.1-x86_64-linux.tar.xz
python3 run.py 1      # smoke test, failed on t3 in Helix, see What broke #4
python3 run.py 20     # full run, output in full-run.txt and results.json
python3 baseline.py 20   # :wq only, output in baseline.txt
```

## Results (20 replays per editor per task, 240 replays plus 40 baseline)

All 240 task replays produced the expected file.

| Task | Neovim keys | Keys | Helix keys | Keys |
|---|---|---|---|---|
| t1 rename a word | `wcworder_total<Esc>` | 15 | `wwcorder_total<Esc>` | 15 |
| t2 change inside quotes | `/SPR<CR>ci"WINTER<Esc>` | 15 | `/SPR<CR>mi"cWINTER<Esc>` | 16 |
| t3 empty round(...) | `/round(<CR>f(di(` | 13 | `/round\(<CR>mi(d` | 13 |
| t4 delete a line | `jdd` | 3 | `jxd` | 3 |
| t5 rename all subtotal | `:%s/subtotal/base/g<CR>` | 20 | `%ssubtotal<CR>cbase<Esc>` | 17 |
| t6 delete last two lines | `Gdk` | 3 | `gekxxd` | 6 |
| **Total** | | **69** | | **70** |

Replay time, median (min to max) in seconds:

| Task | Neovim | Helix |
|---|---|---|
| t0 baseline, `:wq` only | 0.0199 (0.0098–0.0243) | 0.0688 (0.0191–0.0811) |
| t1 | 0.0281 (0.0188–0.0316) | 0.0808 (0.0291–0.0981) |
| t2 | 0.0285 (0.0194–0.0325) | 0.0814 (0.0312–0.0955) |
| t3 | 0.0269 (0.0162–0.0299) | 0.0755 (0.0261–0.0954) |
| t4 | 0.0231 (0.0139–0.0277) | 0.0757 (0.0244–0.0883) |
| t5 | 0.0244 (0.0136–0.0284) | 0.0905 (0.0381–0.1075) |
| t6 | 0.0253 (0.0171–0.0265) | 0.0765 (0.0281–0.1005) |

Reading: most of Helix's extra time is already in the baseline, which only
saves and quits. Above the baseline, each edit costs a few milliseconds of
replay in either editor. The timings don't separate the two grammars.

## Observations of intermediate state

Captured with `tmux capture-pane` partway through t5:

- Helix after `%`: status line `1 sel  7:9` (whole file selected).
- Helix after `s` and typing `subtotal`, before Enter: `1/3 sels`, and the
  prompt `select:subtotal`. The three matches are live selections before any
  change happens.
- Neovim after typing `:%s/subtotal/base`, before Enter: the buffer already
  shows `base` in all three places. This is with `--clean`, so it is the
  default behaviour.

## What broke

1. **`apt-get install neovim` failed.** Output: `Package neovim is not
   available, but is referred to by another package.` The container had no
   package lists. `apt-get update` fixed it, but Ubuntu 24.04's package is
   Neovim 0.9.5, which is much older than the 0.12.6 release. I used the
   upstream release tarballs for both editors instead, so the comparison is
   between current releases.
2. **Wrong assumption about Helix's latest version.** Sorting tags put
   `v0.6.0` last. Helix moved to calendar versions (`25.07.1`), which sort
   below `v`. Listing only `NN.NN` tags gave 25.07.1.
3. **`python3 -I run.py` failed** with `ModuleNotFoundError: No module named
   'tasks'`. `-I` drops the script's directory from `sys.path`. These are my
   own scripts, not downloaded code, so I ran without `-I`.
4. **Helix t3 silently edited the wrong place.** Expected: `round()`. Got:
   the first character of the file deleted (`ef total_price(...`). Cause:
   Helix's `/` takes a regex, and in that syntax `round(` is an unclosed
   group. The search didn't move the cursor and showed no message I could
   capture (status still `1:1` after Enter). `mi(` then found no enclosing
   parentheses, and `d` deleted the character under the cursor. Confirmed by
   searching `round\(` instead: the cursor moved to `4:17`. Neovim's default
   `/` treats `(` as a literal, so the same keys work there. Fix: escape the
   paren in the Helix task, one extra keystroke.

## Clean up

Every replay kills the tmux server before starting. The temp files are
deleted after each comparison. No servers or background processes are left
running.
