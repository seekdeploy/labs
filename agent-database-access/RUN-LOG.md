# Run log: agent-database-access

- **Writer:** Petra Lindqvist
- **Started:** 2026-11-23
- **Environment:** Ubuntu 24.04 LTS, x86_64, 4 vCPU (Intel Xeon @ 2.30GHz),
  15 GiB RAM, cloud container (SeekDeploy writer session). All servers ran on
  the container's local disk under `/var/tmp/ada`, as the `postgres` OS user.
- **Versions:** PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1): server,
  psql, pg_basebackup, pgbench. GNU bash 5.2.21.
- **Agent:** none. No AI model was run. `sql/probes.txt` is a fixed list of 15
  statements of the kind an agent might issue. `scripts/probe.sh` runs each one
  as a given role inside `BEGIN … ROLLBACK`, so nothing a probe does persists.
- **Timings:** wall-clock seconds around each step (`scripts/timed.sh`), from
  three full runs of `drill.sh` on the machine above. Primary, replica and PITR
  copy all ran on the same machine.
- **Reused from:** `test-the-restore/` (shop schema, timing helper).

## Log

All times are UTC. Raw output for each step is in `output/`.

### 2026-11-23 15:06: seed and probe the three roles (`output/01-seed-and-probe.txt`)

The database is pgbench scale 5 plus the shop schema: 200,000 customers and
1,000,000 orders, 279 MB. `sql/roles.sql` creates `agent_ro` and `agent_rw`
and revokes everything from PUBLIC. The rows that matter:

```text
postgres             | drop table             | BLOCKED: cannot drop table orders because other objects depend on it
agent_ro             | read customer email    | BLOCKED: permission denied for table customers
agent_ro             | update one order       | BLOCKED: cannot execute UPDATE in a read-only transaction
agent_ro             | write server file      | BLOCKED: permission denied to COPY to a file
agent_ro             | slow query (10 s)      | BLOCKED: canceling statement due to statement timeout
agent_rw             | update one order       | OK
agent_rw             | update every order     | BLOCKED: canceling statement due to statement timeout
agent_rw             | delete one order       | BLOCKED: permission denied for table orders
agent_rw             | drop table             | BLOCKED: must be owner of table orders
agent_rw             | create table           | BLOCKED: permission denied for schema public
```

The owner's `DROP TABLE` was refused only because a view and a materialized
view depend on `orders`. `DROP TABLE … CASCADE` would have worked.

`agent_rw`'s update of every order was stopped by the 5-second
`statement_timeout`, not by a permission. See "What broke" #1.

### 2026-11-23 15:07: partial updates, then the guard (`output/02-guard.txt`)

```text
--- before guard
agent_rw             | update 10% of orders   | OK
agent_rw             | update 900 orders      | OK
--- install guard
guard installed
--- after guard
agent_rw             | update 10% of orders   | BLOCKED: refusing to UPDATE 100000 rows in orders (limit 1000)
agent_rw             | update 900 orders      | OK
postgres             | update every order     | BLOCKED: refusing to UPDATE 1000000 rows in orders (limit 1000)
postgres             | delete one order       | OK
```

The guard applies to every role, the owner included.

### 2026-11-23 15:08: read replica (`output/03-replica.txt`)

```text
1,replica_basebackup,1.96
replica in recovery: true
agent_ro             | read orders            | OK
agent_rw             | update one order       | BLOCKED: cannot execute UPDATE in a read-only transaction
1,replica_catchup,0.011
pg_stat_replication replay_lag: 00:00:00.011556
```

A hot standby refuses writes from every role. The catch-up figure is the time
from the primary's 50,000-row INSERT returning until the replica had replayed
past that LSN, polled every 10 ms. There's no network in it.

### 2026-11-23 15:08: branch (`output/04-branch.txt`)

```text
1,branch_create,1.33
agent_rw             | delete one order       | OK
agent_rw             | truncate orders        | OK
agent_rw             | alter table            | OK
DETAIL:  drop cascades to view customer_totals
drop cascades to materialized view monthly_revenue
branch orders table exists: false
main orders rows: 1050000
1,branch_drop,0.21
```

`createdb -T shop shop_branch` copies the database. It worked here because
nothing else was connected to `shop`. The
[PostgreSQL docs](https://www.postgresql.org/docs/16/manage-ag-templatedbs.html)
say "no other sessions can be connected to the source database while it is
being copied", which rules this approach out against a busy production
database. The copy also doesn't carry database-level GRANTs, which is why
`branch.sh` grants on the branch itself.

### 2026-11-23 15:09: point-in-time recovery (`output/05-pitr.txt`)

```text
orders before mistake: 1070000 rows, md5 ae192a12100ffebcbee24e07afcb78af
recovery target: 2026-11-23 15:09:27.936828+00
agent_rw UPDATE of 900 rows: committed
orders after mistake:  1070000 rows, md5 ef96345fe9613118d993dc46d438a8b6
1,pitr_restore,1.65
orders after PITR:     1070000 rows, md5 ae192a12100ffebcbee24e07afcb78af
VERIFY pitr: orders identical to pre-mistake state
log: recovery stopping before commit of transaction 886, time 2026-11-23 15:09:28.962758+00
```

This worked first time. A whole-server rewind also loses every good write made
after the target, so I added a surgical repair. 100 good orders are inserted
after the mistake. After the PITR copy is up, only the 900 damaged rows are
copied back to the primary, inside a transaction with
`SET LOCAL session_replication_role = replica`. That setting stops the
`orders_touch` trigger restamping `updated_at`, and stops the guard firing.

I designed it that way from the start; it isn't a failure I hit. Per the
[docs](https://www.postgresql.org/docs/16/runtime-config-client.html), that
setting "also disables all foreign key checks", and only superusers and roles
granted it may set it. That's why the repair runs as the owner, never as the
agent.

### 2026-11-23 15:09: surgical repair, first version (`output/05-pitr-surgical-first.txt`)

```text
VERIFY repair: original rows identical to pre-mistake state
good orders written after the mistake still present: 102
log: starting point-in-time recovery to 2026-11-23 15:09:27.936828+00
log: starting point-in-time recovery to 2026-11-23 15:10:26.51437+00
```

The repair verified, but the output showed two sloppy checks. See "What
broke" #3.

### 2026-11-23 15:10: first `drill.sh 3`, failed in run 1

```text
guard installed
agent_rw             | update 10% of orders   | BLOCKED:
agent_rw             | update 900 orders      | BLOCKED:
pg_basebackup: error: connection to server on socket "/var/tmp/ada/sock/.s.PGSQL.5544" failed: No such file or directory
```

See "What broke" #2. This run's output was overwritten by the next run; the
lines above are copied from the terminal.

### 2026-11-23 15:12: attempt to reproduce the vanished socket (`output/07-socket-repro.txt`)

Deliberate. Server A was started, its whole work directory (data and socket
directory) was deleted, and then server B was started on the same path and port:

```text
A up: .s.PGSQL.5599 .s.PGSQL.5599.lock
whole work dir deleted while A runs (as in the drill)
B up 15:12:17: .s.PGSQL.5599 .s.PGSQL.5599.lock
sock dir now: [.s.PGSQL.5599 .s.PGSQL.5599.lock ]
2026-11-23 15:12:31.072 UTC [2732] PANIC:  could not open file "global/pg_control": No such file or directory
```

A crashed about 14 seconds later. B's socket survived the full 150-second
watch, so this did **not** reproduce the failure.

My first reproduction attempt was itself wrong: it kept the socket directory
outside the deleted tree, so B refused to start. Its output isn't kept.

### 2026-11-23 15:15: `drill.sh 3`, all three runs verified (`output/06-drill3.txt`)

Every run printed, among the rest:

```text
VERIFY pitr: orders identical to pre-mistake state
VERIFY repair: original rows identical to pre-mistake state
good orders written after the mistake still present: 100
branch orders table exists: false
main orders rows: 1050000
```

Medians of three runs, in seconds (`output/timings.csv`):

| Step | median | min | max |
|---|---:|---:|---:|
| replica_basebackup | 1.45 | 1.35 | 1.65 |
| replica_start | 0.11 | 0.11 | 0.12 |
| replica_catchup | 0.016 | 0.009 | 0.134 |
| branch_create | 1.03 | 0.90 | 1.19 |
| branch_drop | 0.18 | 0.17 | 0.20 |
| pitr_basebackup | 1.20 | 1.00 | 1.30 |
| pitr_restore | 1.70 | 1.40 | 1.73 |
| surgical_repair | 0.04 | 0.04 | 0.06 |

### Cleanup

```text
$ pgrep -a postgres | grep -v defunct || echo "no postgres running"
no postgres running
```

`/var/tmp/ada` and `/var/tmp/ada-repro` were deleted.

## What broke

### 1. "Blocked" by a timeout, not a permission

- **Expected:** an agent role with `UPDATE` on `orders` could run
  `UPDATE orders SET status = 'refunded'` with no `WHERE`. I added the probe to
  show that.
- **Actual:** `BLOCKED: canceling statement due to statement timeout`. On a
  million rows with a per-row trigger, the update took longer than 5 seconds.
- **Why it matters:** this is luck about table size, not protection. The same
  mistake on 10% of rows (`WHERE id % 10 = 0`, 100,000 rows) went through.
- **Fix:** `sql/guard.sql`, a statement-level trigger that refuses any single
  UPDATE or DELETE on `orders` touching more than 1,000 rows. It then blocked
  the 10% update for `agent_rw` and the full update even for the owner. A
  900-row mistake still passes, which is why the PITR step exists.

### 2. The primary's socket vanished mid-drill (cause not confirmed)

- **What happened:** in the first `drill.sh 3`, at about 15:11:32, two probes
  failed with an empty error. Then `pg_basebackup` reported the socket file
  `/var/tmp/ada/sock/.s.PGSQL.5544` missing. The primary process was still
  running, and its log showed no crash or shutdown.
- **Context:** just before starting the drill I had run `rm -rf /var/tmp/ada`.
  The primary from my previous manual step was still running under it, because
  `pitr.sh` doesn't stop the primary.
- **What I tried:** a deliberate reproduction, logged above. It did not
  reproduce: the orphaned server PANICked within about 14 seconds and the new
  server's socket survived 150 seconds. So I can't say what removed the
  socket.
- **Fix (of the precondition, not a confirmed cause):** `drill.sh` now refuses
  to start while any postgres process for `$WORK` is running. It also stops the
  primary, replica and PITR servers on exit through a `trap`, including after
  a failure. The next three full runs were clean.

### 3. Two sloppy checks of my own

- "Good orders written after the mistake" counted rows with
  `total_cents = 999 AND status = 'paid'`, and two of the original random rows
  match that. The count said 102 instead of 100. It now counts by id above the
  pre-mistake row count.
- `pitr.log` was appended to across runs, so the recovery lines from two runs
  were mixed together. It's now truncated before each restore.

## Screenshots

None. All the output here is terminal text.
