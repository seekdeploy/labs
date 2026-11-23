#!/usr/bin/env python3
"""Count monthly commits and distinct authors for fork/upstream pairs.

Usage: count_forks.py <clones dir> <out dir>

For each pair the fork's history is fetched into the upstream clone (as a
remote-tracking ref), so "unique to the fork" can be computed with
`git rev-list fork ^upstream`. Upstream counts use every non-merge commit on
the upstream default branch. "Unique to the fork" excludes commits on ANY
upstream branch (release branches included).

Rules (fixed before looking at the data):
- non-merge commits only (--no-merges)
- month = committer date, UTC, YYYY-MM
- author identity = lower-cased author e-mail
- bots excluded: e-mail or name matching BOT_PATTERN
"""
import collections, csv, json, os, re, subprocess, sys

PAIRS = [
    # pair, upstream dir, upstream ref, fork dir, fork ref
    ("gitea-forgejo",      "gitea",     "main",     "forgejo",  "forgejo"),
    ("redis-valkey",       "redis",     "unstable", "valkey",   "unstable"),
    ("terraform-opentofu", "terraform", "main",     "opentofu", "main"),
    ("vault-openbao",      "vault",     "main",     "openbao",  "main"),
]
FORK_URLS = {"gitea-forgejo": "https://codeberg.org/forgejo/forgejo.git",
             "redis-valkey": "https://github.com/valkey-io/valkey.git",
             "terraform-opentofu": "https://github.com/opentofu/opentofu.git",
             "vault-openbao": "https://github.com/openbao/openbao.git"}
UPSTREAM_URLS = {"gitea-forgejo": "https://github.com/go-gitea/gitea.git",
                 "redis-valkey": "https://github.com/redis/redis.git",
                 "terraform-opentofu": "https://github.com/hashicorp/terraform.git",
                 "vault-openbao": "https://github.com/hashicorp/vault.git"}
# Public start months, for reference only (the window is the merge-base month; see RUN-LOG).
FORK_START = {"gitea-forgejo": "2022-12", "redis-valkey": "2024-03", "terraform-opentofu": "2023-09", "vault-openbao": None}
BOT_PATTERN = re.compile(r"(\[bot\]|dependabot|renovate|github-actions|forgejo-bot|actions@|noreply@codeberg\.org$|bot@|-bot\b)", re.I)

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout

def log(repo, *revs):
    out = git(repo, "log", "--no-merges", "--format=%H%x09%cd%x09%ae%x09%an", "--date=format-local:%Y-%m", *revs)
    for line in out.splitlines():
        h, month, email, name = line.split("\t", 3)
        yield h, month, email.lower(), name

def monthly(rows):
    commits, authors, bots = collections.Counter(), collections.defaultdict(set), 0
    for _, month, email, name in rows:
        if BOT_PATTERN.search(email) or BOT_PATTERN.search(name):
            bots += 1
            continue
        commits[month] += 1
        authors[month].add(email)
    return commits, authors, bots

def main(clones, out):
    clones = os.path.abspath(clones)
    os.environ["TZ"] = "UTC"
    os.makedirs(out, exist_ok=True)
    summary = {}
    for pair, up, up_ref, fk, fk_ref in PAIRS:
        up_repo = os.path.join(clones, up)
        fork_url = FORK_URLS[pair]  # a tree-less local clone cannot serve a fetch, so use the origin
        # bring the fork's commits into the upstream clone under refs/fork/<ref>
        git(up_repo, "fetch", "-q", "--filter=tree:0", fork_url, f"+refs/heads/{fk_ref}:refs/fork/{fk_ref}")
        # every upstream branch, so commits from upstream release branches never count as fork-only
        git(up_repo, "fetch", "-q", "--filter=tree:0", UPSTREAM_URLS[pair], "+refs/heads/*:refs/upstream/*")
        upstream_rev, fork_rev = f"refs/heads/{up_ref}", f"refs/fork/{fk_ref}"
        merge_base = git(up_repo, "merge-base", upstream_rev, fork_rev).strip()
        rows = {
            "upstream": list(log(up_repo, upstream_rev)),
            "fork_unique": list(log(up_repo, fork_rev, "--not", "--glob=refs/upstream/*")),
        }
        first_unique = git(up_repo, "log", "--no-merges", "--reverse", "--format=%cs", fork_rev, "--not", "--glob=refs/upstream/*").split("\n", 1)[0]
        # Window: from the month of the last shared commit (merge base). Uniform for all pairs, and it
        # excludes old histories merged into a fork from elsewhere (OpenBao contains 2017 plugin history).
        start = git(up_repo, "log", "-1", "--format=%cs", merge_base).strip()[:7]
        result = {"merge_base": merge_base,
                  "merge_base_date": git(up_repo, "log", "-1", "--format=%cs", merge_base).strip(),
                  "first_fork_only_commit": first_unique, "window_start_month": start}
        rows["fork_unique"] = [x for x in rows["fork_unique"] if x[1] >= start]
        for side, r in rows.items():
            commits, authors, bots = monthly(r)
            result[side] = {"bot_commits_excluded": bots}
            with open(os.path.join(out, f"{pair}-{side}.csv"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["month", "commits", "authors"])
                for m in sorted(commits):
                    w.writerow([m, commits[m], len(authors[m])])
            result[side]["months"] = {m: [commits[m], len(authors[m])] for m in sorted(commits)}
            result[side]["_authors_since_fork"] = set().union(*(a for m, a in authors.items() if m >= start)) if authors else set()
        up_a, fk_a = result["upstream"].pop("_authors_since_fork"), result["fork_unique"].pop("_authors_since_fork")
        # Identities stay in memory only; publish counts, never e-mail addresses.
        result["authors_since_fork"] = {"upstream": len(up_a), "fork_unique": len(fk_a), "both": len(up_a & fk_a)}
        summary[pair] = result
        print(pair, "merge-base", result["merge_base_date"],
              "upstream commits", sum(v[0] for v in result["upstream"]["months"].values()),
              "fork-unique commits", sum(v[0] for v in result["fork_unique"]["months"].values()))
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
