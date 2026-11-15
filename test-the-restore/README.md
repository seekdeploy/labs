# Test the restore, not the backup

Build for [Test the restore, not the backup](https://seekanddeploy.io/news/test-the-restore) by Petra Lindqvist.

## What this is

A restore drill for PostgreSQL 16. It builds a database with realistic data
(pgbench tables plus a small shop schema with roles, grants, a trigger, a
view, a materialized view, jsonb and an extension). It backs that database up
two ways, deletes the server's data directory, restores from each backup into
an empty cluster, times every step, and proves the restored data matches the
original.

The two backup methods:

- **Logical:** `pg_dumpall --globals-only` (roles) plus `pg_dump -Fc` (the
  database), restored with `pg_restore -j 4`.
- **Physical:** `pg_basebackup -Ft -z -X stream`, checked with
  `pg_verifybackup`, restored by unpacking the tarballs into an empty data
  directory.

"Matches" means `sql/fingerprint.sql` produces identical output on both
sides. That covers row counts and an md5 over every row of every table,
sequence positions, object counts, extensions, roles and table grants.

## Requirements

- Linux x86_64. It was run on Ubuntu 24.04.5 in a cloud container with 4 vCPUs
  (Intel Xeon @ 2.30GHz), 15 GiB RAM and local disk.
- PostgreSQL 16.15 server and client binaries in `/usr/lib/postgresql/16/bin`
  (Ubuntu's `postgresql-16` package).
- bash 5, GNU tar, bc.
- About 4 GB of free disk at the default scale, or about 10 GB at `SCALE=150`.

## Run it

Postgres won't run as root, so run the scripts as an unprivileged user that
can write to `$WORK` (default `/var/tmp/ttr`):

```bash
# as the postgres user (or any non-root user)
./scripts/drill.sh 3            # seed, back up, wipe, restore both ways, verify; 3 times
SCALE=150 ./scripts/drill.sh 1  # one larger run (~2.4 GB database)
cat /var/tmp/ttr/timings.csv    # run,step,seconds
```

Each step also works on its own: `seed.sh`, `backup.sh`, `wipe.sh`,
`restore-logical.sh`, `restore-physical.sh`, `verify.sh logical|physical`.
`drill.sh` stops the server when it finishes. Everything lives under `$WORK`,
so `rm -rf /var/tmp/ttr` removes it all.

## Results (medians of 3 runs, 503 MB database)

| Step | Seconds |
|---|---|
| `pg_dump -Fc` | 3.72 |
| `pg_basebackup` (gzip) | 8.59 |
| unpack + `pg_verifybackup` | 2.80 |
| Logical restore: globals + `pg_restore -j4` + `vacuumdb -z` | 0.02 + 3.13 + 0.99 = **4.14** |
| Physical restore: unpack + start | 2.47 + 0.72 = **3.19** |

At `SCALE=150` (2,447 MB, one run), the logical restore took 31.86 s and the
physical restore took 10.43 s. Raw output is in [`output/`](output/).

## What broke

1. **`pg_verifybackup` can't read a tar-format backup on PG 16.** It printed
   1,294 "present in the manifest but not on disk" errors. The docs say a tar
   backup "can be checked after extracting it". Fix: unpack to a scratch
   directory and verify that.
2. **The globals restore stopped on `role "postgres" already exists`.** The
   pg_dumpall docs call this error "certain" and "harmless". Fix: allow exactly
   that one error and fail on any other.
3. **The logical restore "failed" verification on a materialized view.** The
   view was stale on the original server, and `pg_restore` re-ran its query,
   so the restored copy was fresher than the original. The backup was fine;
   my check was wrong. Fix: check the restored view against its own query.
   The physical restore matched exactly, stale view included.

The full detail, with real output, is in [RUN-LOG.md](RUN-LOG.md).
