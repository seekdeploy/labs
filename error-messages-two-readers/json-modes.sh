#!/usr/bin/env bash
# Do the CLIs' machine-readable modes cover their errors? Run in a fresh temp dir.
set -u
cd "$(mktemp -d)"
export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
echo "--- cargo build --message-format=json (no Cargo.toml)"
cargo build --message-format=json; echo "exit $?"
echo '{"name":"x","version":"1.0.0","scripts":{"test":"echo ok"}}' > package.json
echo "--- npm run tset --json (stdout only)"
npm run tset --json 2>/dev/null; echo "exit $?"
