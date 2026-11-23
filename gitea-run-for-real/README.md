# Gitea, run for real: testing our own comparison

Build for [Gitea, run for real: testing our own comparison](https://seekanddeploy.io/news/gitea-run-for-real) by Tobias Brandt.

## What this is

A single-binary Gitea install on SQLite, used to test two claims from the
earlier [Gitea vs GitLab](https://seekanddeploy.io/news/gitea-vs-gitlab)
piece. First, does Gitea's built-in GitLab migrator work on a public
gitlab.com project without a token? Second, what happens to a workflow that
says `uses: actions/checkout@v4` when the runner cannot reach github.com?

## Requirements

- Linux x86_64. Run on Ubuntu 24.04.5 LTS in a cloud container, 4 vCPU,
  16 GB RAM.
- Gitea 1.27.3 and Gitea Runner 6.0.0, plus Gitea 28.4.0 for the 19 Nov re-run of test one. Download links and SHA-256 checksums
  are in [BINARIES.md](BINARIES.md); the binaries are not committed.
- git 2.43, and Node 22 for the runner's host mode.
- A non-root user to run Gitea (it refuses to run as root).

## Run it

```bash
# 1. Install Gitea as a non-root user; config in harness/app.ini
useradd --system --create-home --shell /bin/bash git
mkdir -p /srv/gitea-run/custom/conf
cp gitea-1.27.3-linux-amd64 /srv/gitea-run/gitea
cp harness/app.ini /srv/gitea-run/custom/conf/app.ini
chown -R git:git /srv/gitea-run
cd /srv/gitea-run && runuser -u git -- ./gitea web --config custom/conf/app.ini &

# 2. Admin user and API token
runuser -u git -- ./gitea --config custom/conf/app.ini admin user create \
  --username tobias --password '<choose one>' --email you@example.invalid --admin
runuser -u git -- ./gitea --config custom/conf/app.ini admin user \
  generate-access-token --username tobias --token-name lab --scopes all --raw

# 3. Test one: anonymous GitLab migration (vary the item flags)
curl -X POST -H "Authorization: token $TOKEN" -H "Content-Type: application/json" \
  -d '{"clone_addr":"https://gitlab.com/greut/eclint","repo_owner":"tobias",
       "repo_name":"eclint","service":"gitlab","issues":true,"labels":true,
       "milestones":true,"releases":true}' \
  http://127.0.0.1:3000/api/v1/repos/migrate

# 4. Test two: register a host-mode runner, push harness/.gitea/workflows/ci.yml,
#    then restart the runner with github.com unreachable (deliberate):
runuser -u git -- env HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 \
  NO_PROXY=127.0.0.1,localhost ./gitea-runner daemon --config config.yaml

# 5. The fix: mirror actions/checkout into an "actions" org, then add to app.ini:
#    [actions]
#    DEFAULT_ACTIONS_URL = self
```

The exact commands used, in order, with their output, are in
[RUN-LOG.md](RUN-LOG.md) and `logs/`. The workflow variants tested are in
`harness/`.

## What broke

- **Running as root:** Gitea refuses. Fixed with a dedicated `git` user.
- **CA bundle:** my mistake; the `git` user could not read the certificate
  file I pointed it at. Copied it somewhere readable.
- **Anonymous GitLab migration:** gitlab.com returns 401 for labels,
  milestones and issue discussions without a token, and Gitea fails the whole
  migration with HTTP 500. No fix without a token.
- **Leftover repositories:** a failed migration leaves a repository behind,
  so a retry returns 409 until you delete it.
- **Release stall:** a project with 356 release asset links stalled after 41
  files. Stack trace captured; cause not determined. Never solved.
- **Offline runner:** `actions/checkout@v4` failed without github.com even
  with a warm cache, and so did a SHA pin. Fixed by mirroring the action and
  setting `DEFAULT_ACTIONS_URL = self`.

A draft upstream issue for the migration failure is in the run log. It has
not been filed.
