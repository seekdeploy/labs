# Run log: forks-are-governance

- **Writer:** Tobias Brandt
- **Started:** 2026-11-23
- **Environment:** cloud container, x86_64, 4 vCPU, 16 GB RAM, Ubuntu 24.04.5 LTS
- **Versions:** git 2.43.0, Python 3.13.18

## What this measures

Monthly non-merge commits and distinct commit authors for four fork/upstream
pairs, from the month of their last shared commit to 23 November 2026:
Gitea/Forgejo, Redis/Valkey, Terraform/OpenTofu, Vault/OpenBao. Script:
`harness/count_forks.py`. Output: `data/*.csv` (month, commits, authors) and
`data/summary.json`. No e-mail addresses are written anywhere; identities are
used in memory to count distinct authors and overlap, then discarded.

## Sources for the pairs

| Fork | Upstream event | Source |
|---|---|---|
| Forgejo | Announced 15 Dec 2022; hard fork 15 Feb 2024 | forgejo.org blog |
| Valkey | Redis to RSALv2/SSPLv1, 20 Mar 2024; Valkey announced 28 Mar 2024 | redis.io blog; Linux Foundation press release |
| OpenTofu | Terraform to BUSL 1.1, 10 Aug 2023; OpenTofu launched 20 Sep 2023 | terraform commit `b145fbca`; Linux Foundation press release |
| OpenBao | Vault to BUSL 1.1, 10 Aug 2023 | vault commit `0b12cdcf` |

HashiCorp's licence blog post returned HTTP 429 twice, so the BUSL date comes
from the licence commits in both repositories. I found no dated founding
statement for OpenBao on its README or site; the data supplies one (below).

## Log

### Clones

`git clone --filter=tree:0 --no-checkout --single-branch` (commit history
only) of each default branch: forgejo `forgejo`, gitea `main`, valkey and
redis `unstable`, opentofu, terraform, openbao, vault `main`. Commit counts at
clone time: forgejo 26,162; gitea 22,114; valkey 14,414; redis 13,465;
opentofu 34,013; terraform 36,223; openbao 21,379; vault 25,152. Newest
commits 2026-11-20 to 2026-11-23, so none of the clones was stale.

### Method, and what changed while building it

1. First draft wrote contributor e-mail lists into `summary.json`. Removed
   before any run: only counts are written.
2. Fetching a fork from its local tree-less clone into the upstream clone
   failed (`fatal: git upload-pack: aborting due to possible repository
   corruption on the remote side`). Fixed by fetching from the fork's origin
   URL.
3. First complete run compared forks against the upstream default branch
   only. OpenBao's "first fork-only commit" came out as 2017-08-31: OpenBao
   forked from a Vault release branch, and its repository also carries 2017
   history merged in from elsewhere (`2de267a9 first commit`, `5bb695c1
   Initial merge (#1)`). Fix, applied to all pairs: a commit counts as
   fork-only only if it is on no upstream branch (all 24, 126, 934 and 2,867
   upstream branches fetched), and only from the month of the last shared
   commit. OpenBao fork-only commits fell from 3,142 to 2,028; the other pairs
   did not change.
4. Bots excluded by name or e-mail pattern (`BOT_PATTERN` in the script). The
   top three human committers in each of terraform, gitea, opentofu and valkey
   were checked by hand and are not filtered.

### Windows (month of last shared commit)

| Pair | Last shared commit |
|---|---|
| Gitea / Forgejo | 2024-02-05 |
| Redis / Valkey | 2024-03-20 |
| Terraform / OpenTofu | 2023-08-10 |
| Vault / OpenBao | 2023-05-26 |

### Results (`data/summary.json`)

Last 12 full months (2025-11 to 2026-10), non-merge commits and mean monthly
distinct authors:

```text
gitea      1659 commits  33.5 authors/month   | forgejo (fork-only)  1366 commits  38.7
redis       600 commits  23.9                 | valkey               870 commits  32.8
terraform  1211 commits  14.2                 | opentofu             841 commits   9.9
vault      1642 commits   4.8 (see below)     | openbao              916 commits  21.0
```

First 12 months after the last shared commit:

```text
gitea      1760  29.8 | forgejo  3068  45.4
redis       356  11.2 | valkey    854  25.9
terraform  1418  18.9 | opentofu  817  18.8
vault      2269  57.3 | openbao   333   5.2
```

Distinct authors since the window start (upstream / fork / both):
Gitea-Forgejo 557 / 577 / 135; Redis-Valkey 223 / 339 / 31;
Terraform-OpenTofu 243 / 236 / 9; Vault-OpenBao 392 / 239 / 24.

### Vault's public history

Share of non-merge commits on Vault `main` authored by "Vault Automation", by
quarter: 0% from 2023Q1 through 2025Q2, 48% in 2025Q3, 96% in 2025Q4, 98%,
97%, 96%, 96% in 2026Q1 to Q4. In the last 12 months, 1,584 of 1,642 commits.
From late 2025 the public repository no longer shows who writes Vault, so its
author counts from then on measure the sync, not the team.

### Forgejo ports

Forgejo can port Gitea's MIT-licensed code; a port gets a new hash and counts
as fork-only. In the last 12 months, 14 of 2,106 Forgejo fork-only commits
(bots included) mention Gitea, a Gitea PR or a cherry-pick in the message.
Ports without such a mention cannot be ruled out. Ports keep their original
author, which may raise the Gitea-Forgejo overlap (135).

### Latest releases (23 Nov 2026)

All `vN.N.N` tags, sorted with `sort -V`, which orders 1.27.3 below 28.0.0:
Gitea v28.4.0; Forgejo v17.0.2.

## What broke

1. **E-mail addresses in the output (caught before running).** Expected only
   counts; the first draft would have published contributor addresses. Fixed
   in the script.
2. **Fetching from a partial clone.** Expected a local fetch to work; got
   `bad pack header`. A `--filter=tree:0` clone cannot serve objects it does
   not have. Fixed by fetching from origin.
3. **OpenBao dated to 2017.** Expected a first fork-only commit in 2023; got
   2017-08-31. Comparing against the default branch only counted Vault
   release-branch commits and imported history as OpenBao's. Fixed by
   excluding all upstream branches and starting each window at the last
   shared commit.
4. **Vault's author count collapsed.** Expected tens of authors a month; got
   4.8. Not a bug in the script: the public history is now authored by an
   automation account. Reported as unmeasurable, not as low.
5. **Relative paths.** `git -C clones/gitea fetch clones/forgejo` resolved the
   second path inside the first. Fixed with absolute paths.

## Limits

Commits are not value; one large change and one typo fix count the same.
Authors are distinct e-mail addresses, so one person with two addresses counts
twice (seen in terraform's top three). Counts are a snapshot taken on
2026-11-23; the November 2026 partial month is in the CSVs but not in the
12-month figures.
