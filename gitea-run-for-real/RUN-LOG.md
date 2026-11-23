# Run log: Gitea, run for real

Writer: Tobias Brandt. Date: 2026-11-15 (all times UTC).

## Environment

- Machine: cloud container, x86_64, 4 vCPU, 16 GB RAM, Ubuntu 24.04.5 LTS.
- Network: outbound HTTPS goes through the session's proxy. That proxy blocks
  github.com's web and codeload URLs (HTTP 403) but allows `git` over HTTPS.
  This matters for test (b); see below.
- Gitea 1.27.3 (`gitea-1.27.3-linux-amd64`, SHA-256 verified against
  `dl.gitea.com`), "built with go1.26.7".
- Gitea Runner v6.0.0 (`gitea-runner-6.0.0-linux-amd64.xz`, SHA-256
  verified against the gitea.com release).
- Database: SQLite (bundled in the binary). git 2.43.0. Node v22.23.4.
- Docker was not running, so the runner used host mode (label `lab:host`).

Every command's raw output is in `logs/`, numbered in the order it happened.

## Setup

1. Downloaded and verified both binaries (`sha256sum -c`, both `OK`).
2. Wrote `harness/app.ini`: SQLite, `INSTALL_LOCK = true`, listen on
   127.0.0.1:3000, SSH off. Generated secrets were removed from the copy
   published here.
3. First start as root failed (expected; see What broke #1). Created a system
   user `git` and ran Gitea as that user from `/srv/gitea-run`.
4. `gitea admin user create` and `gitea admin user generate-access-token`
   (scope `all`). Gitea answered `{"version":"1.27.3"}` on the fifth
   one-second poll after start (four connection failures first), so roughly
   four seconds from a cold start with a fresh SQLite database. One run.

## Test (a): the built-in GitLab migrator

Target: https://gitlab.com/greut/eclint (public). Counts read anonymously from
the GitLab API on 2026-11-15: 14 issues, 164 merge requests, 57 releases.

Anonymous GitLab API responses (no token):

```
GET /api/v4/projects/15130865/labels      -> {"message":"401 Unauthorized"}
GET /api/v4/projects/15130865/milestones  -> {"message":"401 Unauthorized"}
issues, merge_requests, releases          -> 200 with X-Total headers
```

Migration was driven through `POST /api/v1/repos/migrate` with
`"service":"gitlab"` and no `auth_token`.

| Attempt | Options | Result | Log |
|---|---|---|---|
| 1 | all items | HTTP 422: `Problem with the SSL CA cert` (my setup, What broke #2) | `02-` |
| 2 | all items | HTTP 409: `The repository with the same name already exists.` | `03-` |
| 3 | all items | HTTP 500 after 12 s: `GET .../milestones: 401 {message: 401 Unauthorized}` | `04-`, `05-` |
| 4 | labels, milestones off | No response after 1,500 s (client timeout); 0 rows written; killed by container restart at ~03:27 | `06-`, `15-` |
| 5 | labels, milestones, PRs off | Stalled at 41 of 356 asset files for 13 min; 0 rows; ended by my Gitea restart (770 s) | `18-`, `19-` |
| 6 | releases, labels, milestones off | HTTP 500 after 15 s: `GET .../issues/1/discussions: 401` | `21-` |
| 7 | code and wiki only | HTTP 201 in 3 s; 7 branches, 58 tags | `26-` |
| 8 | releases only, other project (29 releases, 0 asset links) | HTTP 201 in 3 s; 29 releases | `26-` |

Attempt 8 used https://gitlab.com/JakobDev/minecraft-launcher-lib.

After attempt 3 failed, the repository was **not** empty: `size 1320`,
default branch `master`, seven branches (`03-migrate-anon.txt`). The git data
had been cloned; the issue data was not.

After the container restart, the attempt-4 repository stayed at
`status 1` (being migrated). Its web page showed "Migration failed." with a
"Cancel Migration" button; nothing resumed it (`15-`).

**Which anonymous calls gitlab.com refuses** (`22-anon-endpoint-matrix.txt`,
project 15130865, 2026-11-15):

| Endpoint | HTTP |
|---|---:|
| `issues` | 200 |
| `issues/1/discussions` | 401 |
| `issues/1/notes` | 401 |
| `merge_requests` | 200 |
| `merge_requests/1/discussions` | 401 |
| `releases` | 200 |
| `labels` | 401 |
| `milestones` | 401 |

Gitea's migration form (`templates/repo/migrate/gitlab.tmpl` at v1.27.3)
does not mark the access-token field as required.

**Where attempt 5 waited** (`19-manager-stacks.txt`, from `gitea manager
processes --stacktraces` at 03:40): the migrate request's goroutine was in
`go-retryablehttp (*Client).Do` → `ReleaseLinksService.GetReleaseLink` →
`GitlabDownloader.convertGitlabRelease.func1` (gitlab.go:327) →
`GiteaLocalUploader.CreateReleases`. The project has 57 releases with 356
asset links. My own anonymous probes at 03:40–03:41 (`20-`) showed no
throttling: `ratelimit-name: throttle_unauthenticated_api`,
`ratelimit-remaining: 499` of 500, and the same for
`throttle_unauthenticated_web` on an asset download. **Cause not
determined.**

Not tested: migration with a GitLab personal access token. That needs a
GitLab account, which I did not create for this run.

## Test (b): `uses: actions/checkout@v4` without github.com

Workflow (`harness/.gitea/workflows/ci.yml`): `runs-on: lab`, steps
`uses: actions/checkout@v4` then `run: ls -la && git log --oneline -1`.

`[actions] DEFAULT_ACTIONS_URL` left at its default. The runner's own log
confirms the effect: `actions_url="https://github.com"`.

**Deliberate test condition.** To make github.com unreachable for the runner
only, the runner daemon was started with `HTTPS_PROXY=http://127.0.0.1:9`
(nothing listens there) and `NO_PROXY=127.0.0.1,localhost`, so it could still
reach Gitea. Sanity check (`09-`):

```
$ git ls-remote https://github.com/actions/checkout   # as user git, dead proxy
fatal: unable to access 'https://github.com/actions/checkout/': Failed to connect to 127.0.0.1 port 9 after 0 ms: Couldn't connect to server
```

| Run | Network | `uses:` | Result | Time | Log |
|---|---|---|---|---|---|
| 1 | normal (control) | `actions/checkout@v4` | success; `Download action repository 'actions/checkout@v4' (SHA:11d5960a326750d5838078e36cf38b85af677262)` | ~1 s for the action | `08-` |
| 2a | github.com unreachable, cache warm from run 1 | `actions/checkout@v4` | **failure** | 49 s | `11-` |
| 2c | github.com unreachable, cache warm | `actions/checkout@11d5960a…` (SHA pin) | **failure** | 53 s | `13-` |
| 3a | github.com unreachable | `http://127.0.0.1:3000/actions/checkout@v4` (local mirror) | success, same SHA 11d5960a | under 1 s | `17-` |
| 3b | github.com unreachable, `DEFAULT_ACTIONS_URL = self` | `actions/checkout@v4` | success, same SHA 11d5960a; runner logged `actions_url="http://127.0.0.1:3000"` | under 1 s | `25-` |

Run 2a, trimmed (`11-run2a-job.txt`):

```
03:10:04.548 Failed to download action 'https://codeload.github.com/actions/checkout/tar.gz/v4'. Error: ... proxyconnect tcp: dial tcp 127.0.0.1:9: connect: connection refused. Back off 24s before retry.
03:10:28.548 Failed to download action '...tar.gz/v4'. ... Back off 25s before retry.
03:10:53.565 ##[error]git -C /home/git/.cache/act/b085c58a.../git fetch --force --no-prune --depth 1 --no-tags origin +v4:refs/runner/8e38a1ea...: exit status 128: fatal: unable to access ...
03:10:53.567 Job failed
```

Run 2c, trimmed (`13-run2c-job.txt`): two codeload failures with back-off,
then `##[error]git clone --no-checkout https://github.com/actions/checkout
/home/git/.cache/act/9b1f5699.../git: exit status 128`. A new ref went to a
new cache directory, so the copy fetched in run 1 was not used.

Mirror for run 3a (`14-`): created org `actions`, then
`POST /api/v1/repos/migrate` with `"service":"git"`,
`"clone_addr":"https://github.com/actions/checkout.git"`, `"mirror":true`.
HTTP 201 in 3 s; tag `v4` present.

Run 3b: appended `[actions] ENABLED = true` and `DEFAULT_ACTIONS_URL = self`
to `app.ini`, restarted Gitea (this ended migration attempt 5), restored the
plain `uses: actions/checkout@v4`, runner still behind the dead proxy.

## What broke

1. **Gitea will not start as root.** Expected from the docs; I tried anyway.
   Output: `[F] Gitea is not supposed to be run as root.` Fix: a dedicated
   `git` system user.
2. **First migration failed on certificates (my fault).** I pointed
   `SSL_CERT_FILE` at the proxy CA bundle under `/root`, which user `git`
   cannot read (`head: cannot open '/root/.ccr/ca-bundle.crt' for reading:
   Permission denied`). Gitea's `git clone` reported `Problem with the SSL CA
   cert (path? access rights?)`. Fix: copied the bundle to `/srv/gitea-run`,
   set `SSL_CERT_FILE` and `GIT_SSL_CAINFO`, restarted Gitea.
3. **A failed migration leaves a repository behind.** After attempt 1 (HTTP
   422), the name `eclint-anon` was taken by an empty repository, so attempt 2
   returned HTTP 409. After attempt 3 (HTTP 500), the leftover held the full
   git history and seven branches. In both cases I deleted it by API (HTTP 204)
   before retrying. The log also shows `DeleteRepository() [E]
   CloseRepoBranchesPulls failed: no such file or directory` during the first
   delete.
4. **Anonymous GitLab migration aborts on milestones.** gitlab.com returns 401
   to anonymous requests for labels and milestones. Gitea treats that as fatal
   and fails the whole migration with HTTP 500 instead of skipping those items.
5. **The runner's cache does not cover an outage.** With github.com
   unreachable, both a tag ref and a SHA ref failed even though the action
   had been fetched minutes earlier.
6. **Host-mode noise.** Jobs logged `EACCES: permission denied, stat
   '/root/.local/bin/git'` because the runner inherited root's `PATH` through
   `runuser`. Harmless; the jobs still succeeded.
7. **Anonymous issue migration fails too.** With labels and milestones off,
   attempt 6 failed on `issues/1/discussions: 401`. There is no option to
   migrate issues without their comments, so anonymous issue migration from
   gitlab.com is not possible.
8. **Release migration stalled.** Attempt 5 stopped making progress at 41 of
   356 asset files. Stack trace above; cause not determined. Never solved.
9. **My migration client timed out first.** Attempt 4's `curl --max-time
   1500` gave up while the server was still working, which told me nothing.
   From attempt 5 on, I watched progress through the SQLite database and
   attachment files instead.
10. **The container restarted mid-run** (~03:27), killing Gitea, the runner
    and my progress poller. Environment event, not a Gitea fault. Restarted
    both by hand with the same commands.

## Draft upstream issue (NOT filed; for editor review)

Searched go-gitea/gitea issues on 2026-11-15 (`23-upstream-search.txt`) and
found no duplicate. Related: #17039 (closed), #12779 (closed).

> **Title:** GitLab migration without a token fails entirely (HTTP 500) when
> gitlab.com refuses anonymous access to milestones, labels or discussions
>
> **Gitea version:** 1.27.3 (official linux-amd64 binary), SQLite.
>
> **What happened:** Migrating the public project
> https://gitlab.com/greut/eclint with `service: gitlab`, no `auth_token`,
> and milestones selected fails with HTTP 500:
> `GET https://gitlab.com/api/v4/projects/15130865/milestones: 401
> {message: 401 Unauthorized}`. With labels and milestones deselected, it
> fails on `.../issues/1/discussions: 401`. gitlab.com currently answers 401
> to anonymous requests for labels, milestones, issue notes and discussions,
> while listing issues, merge requests and releases works anonymously.
>
> **Expected:** Either (a) the form says a token is required for these items
> on gitlab.com and refuses to start, or (b) the migration skips items it
> cannot read and reports what it skipped. The access-token field in
> `templates/repo/migrate/gitlab.tmpl` is optional, so users are invited down
> this path.
>
> **Also:** The failed migration leaves a repository behind (git data and
> branches present after the 500), so retrying with the same name returns 409
> until it is deleted.
>
> **Steps:** `POST /api/v1/repos/migrate` with
> `{"clone_addr":"https://gitlab.com/greut/eclint","service":"gitlab",
> "issues":true,"labels":true,"milestones":true,"repo_owner":"<you>",
> "repo_name":"x"}`.

The release-link stall (What broke #8) is **not** included: I could not
determine its cause and do not have a minimal reproduction.

## Clean-up

03:43: stopped `gitea-runner daemon` and `gitea web`; no processes left for
user `git`, nothing listening on port 3000 (`27-`). The data under
`/srv/gitea-run` was left in the throwaway container. The published
`harness/app.ini` has generated secrets removed.

## Addendum, 2026-11-19: test one re-run on Gitea 28.4.0

1.27.3, used above, was the last of the 1.x line; Gitea moved to 28.0 on
29 September 2026. In 28.4.0, `services/migrations/gitlab.go` is unchanged
except for a move from version 2 to version 3 of the GitLab API client
library, which could change behaviour, so I re-ran test one.

Gitea 28.4.0 (`gitea-28.4.0-linux-amd64`, SHA-256 verified against
dl.gitea.com), same container, fresh SQLite instance on port 3001 as user
`git`, no GitLab token. Output in `logs/28-gitea-28.4.0-migration.txt`.

| Options | Result | Time (s) |
|---|---|---:|
| All items | HTTP 500: `GET .../milestones: 401 {message: 401 Unauthorized}` | 12 |
| Labels, milestones, releases off | HTTP 500: `GET .../issues/1/discussions: 401` | 20 |

Both failed migrations again left a non-empty repository behind (size 1320,
branch `master`). Both findings reproduce on 28.4.0. Test two (Actions) was
not re-run; `DEFAULT_ACTIONS_URL` still defaults to `github` in 28.4.0's
`custom/conf/app.example.ini`. Gitea 28.4.0 stopped at 20:51 UTC; no
processes left.
