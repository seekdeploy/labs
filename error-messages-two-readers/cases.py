"""Real error messages from common CLIs, each reproduced in a fresh temp dir.

Each case: id, cli, setup (bash, run first, must succeed), cmd (bash, expected
to fail). HOME points at the temp dir and system git config is ignored, so no
identity or settings leak in from the machine.
"""

GIT_REPO = "git init -q -b main . && git config user.email t@t && git config user.name t"
GIT_REMOTE = (
    "git init -q --bare remote.git && git clone -q remote.git work 2>/dev/null && cd work && "
    "git config user.email t@t && git config user.name t && "
    "echo a > f && git add f && git commit -qm a && git push -q origin HEAD:main 2>/dev/null"
)

CASES = [
    {"id": "git-no-upstream", "cli": "git",
     "setup": GIT_REMOTE + " && git checkout -qb feat",
     "cwd": "work", "cmd": "git push"},
    {"id": "git-no-identity", "cli": "git",
     "setup": "git init -q -b main . && touch f && git add f",
     "cmd": "git commit -qm x"},
    {"id": "git-typo", "cli": "git",
     "setup": GIT_REPO,
     "cmd": "git stauts"},
    {"id": "git-bad-pathspec", "cli": "git",
     "setup": GIT_REPO + " && touch f && git add f && git commit -qm a",
     "cmd": "git checkout no-such-branch"},
    {"id": "git-dirty-merge", "cli": "git",
     "setup": GIT_REPO + " && echo a > f && git add f && git commit -qm a && "
              "git checkout -qb other && echo b > f && git commit -qam b && "
              "git checkout -q main && echo c > f",
     "cmd": "git merge other"},
    {"id": "git-push-behind", "cli": "git",
     "setup": GIT_REMOTE + " && cd .. && git clone -q remote.git other 2>/dev/null && cd other && "
              "git config user.email t@t && git config user.name t && "
              "echo x > g && git add g && git commit -qm x && git push -q 2>/dev/null && "
              "cd ../work && echo y > h && git add h && git commit -qm y",
     "cwd": "work", "cmd": "git push"},
    {"id": "npm-missing-script", "cli": "npm",
     "setup": "echo '{\"name\":\"x\",\"version\":\"1.0.0\",\"scripts\":{\"test\":\"echo ok\"}}' > package.json",
     "cmd": "npm run tset"},
    {"id": "python-nameerror", "cli": "python3",
     "setup": "true",
     "cmd": "python3 -c 'prnt(1)'"},
    {"id": "python-missing-module", "cli": "python3",
     "setup": "true",
     "cmd": "python3 -c 'import sklearn'"},
    {"id": "pip-externally-managed", "cli": "pip (python3.12)",
     "setup": "true",
     "cmd": "python3.12 -m pip install --dry-run six"},
    {"id": "cargo-no-manifest", "cli": "cargo",
     "setup": "true",
     "cmd": "cargo build"},
    {"id": "curl-bad-host", "cli": "curl",
     "setup": "true",
     "cmd": "curl -sS https://no-such-host.invalid/"},
    {"id": "jq-index-number", "cli": "jq",
     "setup": "true",
     "cmd": "echo 1 | jq .foo"},
    {"id": "grep-bad-regex", "cli": "grep",
     "setup": "echo 'round(x)' > f",
     "cmd": "grep -E 'round(' f"},
    {"id": "tar-missing-file", "cli": "tar",
     "setup": "true",
     "cmd": "tar -xf missing.tar"},
    {"id": "docker-no-daemon", "cli": "docker",
     "setup": "true",
     "cmd": "docker ps"},
    {"id": "make-no-makefile", "cli": "make",
     "setup": "true",
     "cmd": "make"},
]
