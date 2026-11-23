# Forks are governance

Build for [Forks are governance](https://seekanddeploy.io/news/forks-are-governance) by Tobias Brandt.

## What this is

Monthly non-merge commits and distinct commit authors for four fork/upstream
pairs (Gitea/Forgejo, Redis/Valkey, Terraform/OpenTofu, Vault/OpenBao), from
the month of each pair's last shared commit to 23 November 2026. It answers
whether each fork kept contributors after its first year, and how many people
work on both sides.

## Requirements

- git 2.43 or newer (partial clone support), Python 3.10 or newer
- Network access to github.com and codeberg.org; about 100 MB of disk

## Run it

```bash
mkdir clones && cd clones
git clone --filter=tree:0 --no-checkout --single-branch --branch forgejo  https://codeberg.org/forgejo/forgejo.git forgejo
git clone --filter=tree:0 --no-checkout --single-branch --branch main     https://github.com/go-gitea/gitea.git gitea
git clone --filter=tree:0 --no-checkout --single-branch --branch unstable https://github.com/valkey-io/valkey.git valkey
git clone --filter=tree:0 --no-checkout --single-branch --branch unstable https://github.com/redis/redis.git redis
git clone --filter=tree:0 --no-checkout --single-branch --branch main     https://github.com/opentofu/opentofu.git opentofu
git clone --filter=tree:0 --no-checkout --single-branch --branch main     https://github.com/hashicorp/terraform.git terraform
git clone --filter=tree:0 --no-checkout --single-branch --branch main     https://github.com/openbao/openbao.git openbao
git clone --filter=tree:0 --no-checkout --single-branch --branch main     https://github.com/hashicorp/vault.git vault
cd .. && python3 harness/count_forks.py clones data
```

To add a pair, add one entry to each of `PAIRS`, `FORK_URLS` and
`UPSTREAM_URLS` in the script.

## Data

`data/<pair>-upstream.csv` and `data/<pair>-fork_unique.csv`: month, commits,
authors. `data/summary.json`: windows, monthly series, bot commits excluded,
and author counts since the split (upstream, fork, both). Counts only; no
names or e-mail addresses.

## What broke

- The first draft of the script would have written contributor e-mail
  addresses into the data. Removed before any run.
- A tree-less clone cannot serve a fetch; forks are fetched from origin.
- Comparing forks against the upstream default branch only dated OpenBao to
  2017. Fork-only now means "on no upstream branch, since the last shared
  commit".
- Vault's public history has been authored by an automation account since
  2025Q3, so its author counts from then on are not meaningful. Reported, not
  fixed.

Details in [RUN-LOG.md](RUN-LOG.md).
