# uptime-kuma-at-3am

The test harness for the SeekDeploy article "Uptime Kuma, critiqued at 3am". It runs a local
Uptime Kuma 2.5.12 against a target we control, sends alerts to a local webhook "pager", and
breaks things on purpose: a flapping target, a failing notification channel, a Kuma restart
mid-outage, and an outage while Kuma is down. Every alert is logged to `logs/alerts.jsonl`.

- `target.py`: HTTP target on 127.0.0.1:8081; returns 200 or 503 depending on `state/target`.
- `flap.py PERIOD DURATION`: toggles the target up/down.
- `receiver.py`: webhook pager on 127.0.0.1:8082; returns 200 or 500 depending on `state/receiver`.
- `kuma-ctl.js`: sets up Kuma and adds monitors over its Socket.IO API
  (run with `NODE_PATH=<uptime-kuma>/node_modules`).
- `scenarios-3-4.sh`: the restart and Kuma-down scenarios (needs `KUMA_SRC`).

`RUN-LOG.md` has every command, the output, and what broke.
