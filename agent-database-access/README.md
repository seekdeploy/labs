# Give an agent a database without losing your data

Build for [Give an agent a database without losing your data](https://seekanddeploy.io/news/agent-database-access) by Petra Lindqvist.

## What this is

Four layers of protection for a PostgreSQL 16 database that a coding agent can
reach, each tested against the same list of statements an agent might run:

1. **Least-privilege roles** (`sql/roles.sql`): `agent_ro`, which reads what it
   needs but not customers' email, and `agent_rw`, which may insert and update
   one table. Both have timeouts.
2. **A blast-radius guard** (`sql/guard.sql`): a statement-level trigger that
   refuses any single `UPDATE` or `DELETE` touching more than 1,000 rows of
   `orders`, whoever runs it.
3. **A read replica** and **a throwaway branch** (`scripts/replica.sh`,
   `scripts/branch.sh`): somewhere for the agent to read that can't be written
   to, and somewhere it can write that doesn't matter.
4. **Point-in-time recovery** (`scripts/pitr.sh`): a 900-row bad `UPDATE` that
   every layer above allows, undone by restoring a base backup plus archived
   WAL to a second server and copying only the damaged rows back.

No AI model was run. The "agent" is the fixed list of SQL statements in
`sql/probes.txt`, run as each role inside a transaction that is rolled back.

## Requirements

- Linux x86_64. It was run on Ubuntu 24.04 in a cloud container with 4 vCPUs
  and 15 GiB RAM.
- PostgreSQL 16.15 server and client in `/usr/lib/postgresql/16/bin`.
- bash 5, bc.
- About 2 GB of free disk.
- Run as a non-root user that can write to `$WORK` (default `/var/tmp/ada`).

## Run it

```bash
./scripts/drill.sh 3        # everything, three times from scratch
cat /var/tmp/ada/timings.csv
```

`drill.sh` refuses to start if a server from an earlier run is still running.
It stops all three servers (primary, replica, PITR copy) when it exits, even on
failure. Delete `$WORK` afterwards.

## Results (3 runs, 279 MB database, all verified)

| Role | Blocked | Got through |
|---|---:|---:|
| `agent_ro` | 13 of 15 | 2 reads |
| `agent_rw`, no guard | 10 of 15 | 5 |
| `agent_rw`, with guard | 11 of 15 | 4 |

What got through for `agent_rw` with the guard on: reading orders, reading
customer names, updating one order, and updating 900 orders. Without the guard it could also
mark 100,000 orders refunded. The only thing that stopped it updating all
1,000,000 was the 5-second statement timeout.

| Step | Median (s) |
|---|---:|
| Replica: base backup | 1.45 |
| Replica catch-up after 50,000 inserts | 0.016 |
| Branch: `CREATE DATABASE … TEMPLATE` | 1.03 |
| PITR: base backup | 1.20 |
| PITR: restore + replay to target | 1.70 |
| Surgical repair of 900 rows | 0.04 |

Replica and primary ran on the same machine, so the catch-up figure has no
network in it.

## What broke

1. **A probe passed only by luck.** `UPDATE orders SET status = 'refunded'`
   with no `WHERE` was "blocked" for `agent_rw` only by the statement timeout,
   and the same mistake on 10% of rows went through. Fix: `sql/guard.sql`.
2. **A server socket vanished mid-run.** One full run failed when the
   primary's socket file disappeared. A server from an earlier manual step was
   still running when I deleted its directory. I couldn't reproduce the exact
   mechanism. Fix: `drill.sh` checks for leftover servers and stops everything
   on exit.
3. **Two sloppy checks.** A count of "good orders" matched two pre-existing
   random rows, and the PITR log accumulated across runs. Both are fixed.

The full detail, with real output, is in [RUN-LOG.md](RUN-LOG.md).
