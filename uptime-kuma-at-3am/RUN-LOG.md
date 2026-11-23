# Run log: uptime-kuma-at-3am

Writer: Nadia Farouk. Built and run in a SeekDeploy cloud session (Linux 6.18.44,
4 vCPU, 15 GB RAM, Node v22.23.4, Python 3.13.18). Uptime Kuma 2.5.12, commit
`5aa5dec425f8a955b54e150636979a6927745ec5` (tag date 2026-11-17).

Everything is local: the monitored target is `target.py` on 127.0.0.1:8081, and the
"pager" is `receiver.py`, a webhook receiver on 127.0.0.1:8082 that logs every alert
it receives to `logs/alerts.jsonl`. Kuma is driven through its Socket.IO API by
`kuma-ctl.js`, the same API its web UI uses. The admin password is a throwaway value
for this local instance.

## 2026-11-23

### Install (non-Docker)

Docker is installed but no daemon runs in this session
(`failed to connect to the docker API at unix:///var/run/docker.sock`), so I used
the README's non-Docker path:

```
$ git clone --depth 1 --branch 2.5.12 https://github.com/louislam/uptime-kuma.git src
$ cd src && time npm run setup
> git checkout 2.5.12 && npm ci --omit dev --no-audit && npm run download-dist
added 652 packages in 21s
Downloading dist ... Extracting dist... Done
real 0m23.307s
```

Several `npm warn deprecated` lines (glob@10.3.16, prom-client@13.2.0 and others);
none stopped the install.

### First start

```
$ DATA_DIR=../data/ UPTIME_KUMA_HOST=127.0.0.1 node server/server.js
2026-11-23T15:10:28Z [SETUP-DATABASE] INFO: Listening on: http://127.0.0.1:3001
2026-11-23T15:10:28Z [SETUP-DATABASE] INFO: Waiting for user action...
```

What broke (small): 2.x asks you to choose a database before anything else, so the
admin-setup socket call has nothing to talk to yet. The web UI shows this as a
first-run page. Fix: chose SQLite through the same endpoint that page uses:

```
$ curl -s -X POST http://127.0.0.1:3001/setup-database -H 'Content-Type: application/json' -d '{"dbConfig":{"type":"sqlite"}}'
{"ok":true}
2026-11-23T15:11:40Z [SERVER] INFO: No user, need setup
2026-11-23T15:11:40Z [UPDATE-CHECKER] INFO: Failed to check for new versions
```

(The update check fails because this session's network allows only listed hosts.)

### Configuration

```
$ node kuma-ctl.js setup
setup: {"ok":true,"msg":"successAdded","msgi18n":true}
addNotification: {"ok":true,"msg":"Saved.","msgi18n":true,"id":1}
$ node kuma-ctl.js add-monitor "target-default" http://127.0.0.1:8081/ 20 0 20 0
add: {"ok":true,"msg":"successAdded","msgi18n":true,"monitorID":1}
$ node kuma-ctl.js add-monitor "target-retries-2" http://127.0.0.1:8081/ 20 2 20 0
add: {"ok":true,"msg":"successAdded","msgi18n":true,"monitorID":2}
```

Both are HTTP monitors on the same target, checked every 20 seconds. Monitor 1 has
0 retries, which is the UI default (`src/pages/EditMonitor.vue` sets `interval: 60`,
`retryInterval: 60`, `maxretries: 0`, `resendInterval: 0`). Monitor 2 has 2 retries,
20 seconds apart. I used 20 seconds instead of the 60-second default to fit the
scenarios into minutes; that changes timings, not behaviour.

No alert arrived when the monitors first came up, as expected: `sendNotification` in
`server/model/monitor.js` skips the first beat unless it's DOWN.

### What broke: scenario 1, first attempt (the flapping target never flapped)

Expected: restart `target.py` with `--flap 30` so it toggles up/down every 30s.
Got, in `logs/target.out`:

```
OSError: [Errno 98] Address already in use
```

Cause: the PID I'd saved with `echo $!` was the PID of the shell wrapper the command
ran in, not the Python process. `kill` stopped the wrapper, the original
`target.py` kept serving port 8081 (always "up"), and the new flapping copy couldn't
bind. Found by `ps -eo pid,comm,args`, which also showed Kuma runs under the process
name `uptime-kuma`, not `node`. Fix: wrote `flap.py`, which flips the state file the
running target reads, so nothing needs restarting. Recorded the real PIDs
(target 987, receiver 991, Kuma 989). The aborted attempt is marked in
`logs/scenarios.log`.

### Scenario 1: a flapping target (15:15–15:22 UTC)

`python3 flap.py 30 360`: the target alternates up/down every 30 seconds for 6 minutes,
then stays up. Target changes (`logs/target-changes.log`):

```
2026-11-23T15:15:46Z target -> down
2026-11-23T15:16:16Z target -> up
2026-11-23T15:16:46Z target -> down
2026-11-23T15:17:16Z target -> up
2026-11-23T15:17:46Z target -> down
2026-11-23T15:18:16Z target -> up
2026-11-23T15:18:46Z target -> down
2026-11-23T15:19:16Z target -> up
2026-11-23T15:19:46Z target -> down
2026-11-23T15:20:16Z target -> up
2026-11-23T15:20:46Z target -> down
2026-11-23T15:21:16Z target -> up
2026-11-23T15:21:16Z target -> up (flapping stopped)
```

Alerts received by the webhook pager in that window (`logs/alerts.jsonl`, trimmed):

```
2026-11-23T15:15:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:16:18Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:16:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:17:18Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:17:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:18:18Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:18:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:19:18Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:19:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:20:18Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:20:58Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:21:18Z [target-default] [✅ Up] 200 - OK
```

Result: monitor 1 (`target-default`, 0 retries) sent **12 notifications in 6 minutes**,
a DOWN and an UP for every one of the six outages, each 12 seconds or so after the
change (the next 20-second check). Monitor 2 (`target-retries-2`, 2 retries) sent
**none**. Kuma's own log shows it saw every outage and went to PENDING, reached retry 2
of 2, and then the next check found the target up again:

```
2026-11-23T15:15:49Z [MONITOR] WARN: Monitor #2 'target-retries-2': Pending: Request failed with status code 503 | Max retries: 2 | Retry: 1 | Retry Interval: 20 seconds | Type: http
2026-11-23T15:16:09Z [MONITOR] WARN: Monitor #2 'target-retries-2': Pending: Request failed with status code 503 | Max retries: 2 | Retry: 2 | Retry Interval: 20 seconds | Type: http
... (same pair for each of the six outages; Kuma's full server log is in logs/kuma-server.log)
```

The target was down for half of those six minutes. One configuration paged twelve
times; the other paged zero times. Neither is wrong in itself; they're answering
different questions, and the 0-retries default answers "did anything blip?"

### Scenario 2: the notification channel fails (15:23–15:27 UTC)

The webhook pager was switched to answer every request with HTTP 500 (it still logs
each attempt), then the target went down for two minutes and came back up. One
minute later the pager was fixed, and I watched for another minute.

```
2026-11-23T15:23:30Z SCENARIO 2 START receiver -> fail (HTTP 500)
2026-11-23T15:23:35Z target -> down
2026-11-23T15:25:35Z target -> up
2026-11-23T15:26:35Z receiver -> ok
2026-11-23T15:27:35Z SCENARIO 2 END
```

Delivery attempts the pager saw (all answered with 500):

```
2026-11-23T15:23:38Z fail [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:24:29Z fail [target-retries-2] [🔴 Down] Request failed with status code 503
2026-11-23T15:25:38Z fail [target-default] [✅ Up] 200 - OK
2026-11-23T15:25:49Z fail [target-retries-2] [✅ Up] 200 - OK
```

Kuma's server log for each one:

```
2026-11-23T15:23:38Z [MONITOR] ERROR: Cannot send notification to local-webhook-pager
2026-11-23T15:23:38Z [MONITOR] ERROR: Error: Request failed with status code 500 (code=ERR_BAD_RESPONSE) (HTTP 500 Internal Server Error)
    at Webhook.send (.../server/notification-providers/webhook.js:68:18)
    at async Monitor.sendNotification (.../server/model/monitor.js:1512:21)
```

Result: **one attempt per notification, no retry, and nothing re-sent after the
channel recovered.** That matches the code: `Monitor.sendNotification` wraps each
`Notification.send` in a `try/catch` that logs the error and moves on. A two-minute
outage reached no human; the only trace was an ERROR line in the server log. (I did
not check whether the web UI surfaces failed sends anywhere; I only read the server
log.) Kuma does have a per-monitor `resendInterval`, which re-sends a DOWN
notification every N down checks while the monitor stays down; it is 0 (off) by
default and was off here, and it would not have helped this outage after recovery.

### Scenarios 3 and 4: Kuma restarts, and Kuma goes down (15:28–15:36 UTC)

Run by `scenarios-3-4.sh` (Kuma stopped with SIGTERM, then started again with the same
data directory). Timeline from `logs/scenarios.log` and `logs/target-changes.log`:

```
2026-11-23T15:28:00Z SCENARIO 3 START: Kuma restart during an outage
2026-11-23T15:28:00Z target -> down
2026-11-23T15:29:30Z stopping Kuma (SIGTERM pid 989)
2026-11-23T15:29:34Z Kuma stopped
2026-11-23T15:30:07Z Kuma started (pid 2901)
2026-11-23T15:31:37Z target -> up
2026-11-23T15:32:37Z SCENARIO 3 END
2026-11-23T15:32:37Z SCENARIO 4 START: outage while Kuma is down
2026-11-23T15:32:41Z Kuma stopped
2026-11-23T15:32:51Z target -> down
2026-11-23T15:34:21Z target -> up
2026-11-23T15:34:45Z Kuma started (pid 3287)
2026-11-23T15:36:15Z SCENARIO 4 END
```

Every alert the pager received in this window:

```
2026-11-23T15:28:18Z [target-default] [🔴 Down] Request failed with status code 503
2026-11-23T15:28:49Z [target-retries-2] [🔴 Down] Request failed with status code 503
2026-11-23T15:31:47Z [target-default] [✅ Up] 200 - OK
2026-11-23T15:31:48Z [target-retries-2] [✅ Up] 200 - OK
```

**Scenario 3 (restart mid-outage): no duplicate page.** I expected a second DOWN when
Kuma came back, because `sendNotification` sends on a first beat that is DOWN. It
didn't happen. Monitor 1's heartbeat history (`logs/heartbeats.csv`) shows why: the
first beat after the restart (15:30:07) was stored as DOWN with `important = 0`, so
Kuma carried the previous state across the restart and didn't treat it as a new
event. My prediction from reading the code was wrong; the behaviour is the one you'd
want. The checks simply stopped for 49 seconds (last beat 15:29:18, next 15:30:07).

**Scenario 4 (outage while Kuma is down): no alert, and no trace.** The target was
down for 90 seconds while Kuma was stopped. Nothing paged, which is expected. What I
didn't expect is the record. Monitor 1's history goes straight from UP at 15:32:27
to UP at 15:34:45. There is no DOWN beat, no "unknown" marker and no gap entry; the
outage left no evidence in Kuma at all:

```
(1, 1, 0, '2026-11-23 15:32:27.383', '200 - OK')
(1, 1, 0, '2026-11-23 15:34:45.059', '200 - OK')
```

(I read this from the `heartbeat` table directly. I did not check how the web UI
draws the 2 minutes 18 seconds with no beats.)

### Resource use

After 17 minutes with two monitors, Kuma's RSS was 187,772 KB (about 183 MB,
`ps -o rss -C uptime-kuma`), and the data directory was 2.2 MB.

### Clean-up

```
$ kill $(pgrep -x uptime-kuma) 987 991
```

Kuma, the target and the receiver are stopped. No accounts were created anywhere; the
only "notification service" was the local receiver. No cost.
