# Run log: test-the-restore

- **Writer:** Petra Lindqvist
- **Started:** 2026-11-15
- **Environment:** Ubuntu 24.04.5 LTS, x86_64, Linux 6.18 kernel, 4 vCPU
  (Intel Xeon @ 2.30GHz), 15 GiB RAM, cloud container (SeekDeploy writer
  session). The database ran on the container's local disk under
  `/var/tmp/ttr`, as the `postgres` OS user.
- **Versions:** PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1): server,
  pg_dump, pg_dumpall, pg_restore, pg_basebackup, pg_verifybackup, pgbench.
  GNU tar 1.35, GNU bash 5.2.21.
- **Timings:** wall-clock seconds from `date +%s.%N` around each step
  (`scripts/timed.sh`). Three full runs at pgbench scale 20 and one at
  scale 150, all on the machine above. Nothing else was running in the
  container.

## Log

All times are UTC. Full raw output for each run is in `output/`.

### 2026-11-15 02:5x: check what's installed

```text
$ which psql pg_dump pg_ctl pgbench pg_basebackup
/usr/bin/psql
/usr/bin/pg_dump
/usr/bin/pgbench
/usr/bin/pg_basebackup
$ apt list --installed | grep postgres
postgresql-16/now 16.15-0ubuntu0.24.04.1 amd64 [installed,local]
postgresql-client-16/now 16.15-0ubuntu0.24.04.1 amd64 [installed,local]
$ id postgres
uid=102(postgres) gid=104(postgres) groups=104(postgres),101(ssl-cert)
```

`pg_ctl` isn't on PATH. It lives in `/usr/lib/postgresql/16/bin`, so
`scripts/env.sh` puts that directory first on PATH. The scripts run as
`postgres` because the server refuses to start as root.

### 2026-11-15 02:56: first full pass (`drill.sh 1`), failed at verify_base

```text
1,dump_globals,0.02
1,dump_custom,4.02
1,basebackup,9.20
pg_verifybackup: error: "pg_wal.tar.gz" is present on disk but not in the manifest
pg_verifybackup: error: "base.tar.gz" is present on disk but not in the manifest
pg_verifybackup: error: "base/16384/4166" is present in the manifest but not on disk
pg_verifybackup: error: "base/5/2699" is present in the manifest but not on disk
... (1,294 lines like this in total)
```

I expected `pg_verifybackup -n <dir>` to check the tar backup. It looked for
loose files and found two tarballs instead. See "What broke" #1. Full output:
`output/run0.txt`.

### 2026-11-15 02:57: second pass, failed at restore_globals

```text
1,basebackup,8.69
backup successfully verified
1,verify_base,2.38
73M	base
4.0K	globals.sql
32M	shop.dump
wiped: ls: cannot access '/var/tmp/ttr/data': No such file or directory
psql:/var/tmp/ttr/backups/globals.sql:20: ERROR:  role "postgres" already exists
```

Line 20 of `globals.sql` is `CREATE ROLE postgres;`. See "What broke" #2.
Full output: `output/run1.txt`.

### 2026-11-15 02:58: third pass, logical restore verification failed

```text
globals restored; expected errors: 1
1,restore_globals,0.02
1,restore_custom,3.31
1,analyze_after,1.17
--- /var/tmp/ttr/fp/original.txt
+++ /var/tmp/ttr/fp/logical.txt
@@ -1,6 +1,6 @@
 table customers rows=200000 md5=b543a45c10799774ebe6bcb1511c7fed
-table monthly_revenue rows=20 md5=681916d34a89a791e0cbc2b2082e5c70
+table monthly_revenue rows=20 md5=cdd1739c33eaa385b11c126bcda8578b
 table orders rows=1000000 md5=4666d70293bfc31b71fca02f3a8ff2f5
VERIFY logical: DIFFERENT
```

Every base table matched. Only the materialized view differed. Full output:
`output/run2.txt`. See "What broke" #3 for the investigation.

### 2026-11-15 02:59: investigating the materialized view

On the logical restore:

```text
$ pg_restore -l backups/shop.dump | grep -i monthly_revenue
225; 1259 16527 MATERIALIZED VIEW public monthly_revenue postgres
3500; 0 16527 MATERIALIZED VIEW DATA public monthly_revenue postgres
$ psql -d shop -f sql/matview-check.sql      # logical restore
matview_stored    cdd1739c33eaa385b11c126bcda8578b
matview_query_now cdd1739c33eaa385b11c126bcda8578b
```

Then I wiped it and did the physical restore from the same backup set
(`output/run2b-physical.txt`):

```text
1,restore_unpack,2.29
1,restore_start,0.82
VERIFY physical: identical (26 facts checked)
matview_stored    681916d34a89a791e0cbc2b2082e5c70
matview_query_now cdd1739c33eaa385b11c126bcda8578b
```

The physical copy has the original's stale view (681916…). Run against the
same data, the view's query gives cdd173…, which is what the logical restore
stored.

My first attempt at this check failed for a boring reason: I'd used `\x27`
escapes inside a single-quoted `su -c` string, and psql got literal
backslashes (`ERROR: syntax error at or near "\"`). I moved the queries into
`sql/matview-check.sql`.

### 2026-11-15 03:00: three full runs at scale 20 (`drill.sh 3`), all verified

```text
=== run 1 of 3 ===
1,seed_pgbench,2.02
1,seed_shop,15.17
503 MB
1,dump_globals,0.02
1,dump_custom,3.72
1,basebackup,8.48
1,verify_base,2.80
73M	base
4.0K	globals.sql
32M	shop.dump
1,restore_globals,0.02
1,restore_custom,3.13
1,analyze_after,1.13
VERIFY logical: identical (25 facts checked)
VERIFY logical: monthly_revenue matches its query (refreshed by pg_restore)
1,restore_unpack,2.60
1,restore_start,0.72
VERIFY physical: identical (26 facts checked)
```

Runs 2 and 3 were the same apart from timing. Full output is in
`output/drill3.txt`, and all timings are in `output/timings-scale20.csv`.

Medians of the three runs, in seconds:

| Step | median | min | max |
|---|---|---|---|
| seed_pgbench | 2.01 | 1.84 | 2.02 |
| seed_shop | 15.17 | 14.67 | 15.18 |
| dump_globals | 0.02 | 0.02 | 0.02 |
| dump_custom | 3.72 | 3.66 | 3.75 |
| basebackup | 8.59 | 8.48 | 8.61 |
| verify_base | 2.80 | 2.74 | 2.81 |
| restore_globals | 0.02 | 0.02 | 0.04 |
| restore_custom | 3.13 | 3.09 | 3.15 |
| analyze_after | 0.99 | 0.98 | 1.13 |
| restore_unpack | 2.47 | 2.43 | 2.60 |
| restore_start | 0.72 | 0.72 | 0.82 |

### 2026-11-15 03:02: one run at scale 150 (`SCALE=150 drill.sh 1`), verified

```text
1,seed_pgbench,14.14
1,seed_shop,12.83
2447 MB
1,dump_custom,8.14
1,basebackup,27.26
1,verify_base,10.25
179M	base
67M	shop.dump
1,restore_custom,22.97
1,analyze_after,8.87
VERIFY logical: identical (25 facts checked)
VERIFY logical: monthly_revenue matches its query (refreshed by pg_restore)
1,restore_unpack,8.41
1,restore_start,2.02
VERIFY physical: identical (26 facts checked)
```

This is a single run, so treat it as one data point. Full output is in
`output/drill-scale150.txt`.

### 2026-11-15 03:03: cleanup

```text
$ pgrep -a postgres || echo "no postgres processes running"
no postgres processes running
```

`drill.sh` stops the server at the end. I removed `/var/tmp/ttr` afterwards.

## What broke

### 1. pg_verifybackup can't read tar-format backups on PostgreSQL 16

- **Expected:** `pg_verifybackup -n backups/base` would check the
  `pg_basebackup -Ft -z` output. I used `-n` because I assumed it couldn't
  parse WAL inside a tarball but would check the data files.
- **Actual:** 1,296 errors. Every one of the 1,294 files in the manifest was "present in the
  manifest but not on disk", and both tarballs were "present on disk but not
  in the manifest" (`output/run0.txt`).
- **Cause:** the [PostgreSQL 16 docs](https://www.postgresql.org/docs/16/app-pgverifybackup.html)
  say: "The backup must be stored in the 'plain' format; a 'tar' format
  backup can be checked after extracting it."
- **Fix:** `backup.sh` now unpacks `base.tar.gz` and `pg_wal.tar.gz` into a
  scratch directory, runs `pg_verifybackup -m backup_manifest <dir>` (WAL
  parsing included, so no `-n`), and deletes the scratch copy. That adds
  2.8 s at 503 MB and 10.3 s at 2.4 GB, and needs temporary disk space equal
  to the uncompressed backup.

### 2. The globals restore failed on `role "postgres" already exists`

- **Expected:** `psql -v ON_ERROR_STOP=1 -f globals.sql` would recreate the
  `app_rw` and `app_ro` roles in the fresh cluster.
- **Actual:** `psql:/var/tmp/ttr/backups/globals.sql:20: ERROR: role
  "postgres" already exists`, and the drill stopped (`output/run1.txt`).
- **Cause:** `pg_dumpall --globals-only` emits `CREATE ROLE` for every role,
  including the bootstrap superuser that `initdb` already created. The
  [pg_dumpall docs](https://www.postgresql.org/docs/16/app-pg-dumpall.html)
  say the restore "is certain to get a 'role already exists' error for the
  bootstrap superuser ... This error is harmless and should be ignored."
- **Fix:** `restore-logical.sh` runs the globals file without
  `ON_ERROR_STOP`, captures stderr, and fails if there is any error other
  than that one. I didn't want to turn error checking off entirely: a broken
  role restore shows up later as permission errors in the app, which is a
  much worse time to find out.

### 3. Logical restore "differed" from the original, but only in a stale materialized view

- **Expected:** both restores would produce an identical fingerprint.
- **Actual:** the logical restore differed in one line, the md5 of
  `monthly_revenue` (`output/run2.txt`). All base tables, sequences, grants
  and roles matched.
- **Cause:** `sql/schema.sql` creates `monthly_revenue` and then runs an
  `UPDATE` on `orders` (it's there to fire the trigger). The view isn't
  refreshed after that, so it's stale on the original server, as
  materialized views often are in production. `pg_dump` records the view's
  definition plus a "MATERIALIZED VIEW DATA" step, and `pg_restore` runs that
  step as a refresh against the restored tables. So the restored view
  reflects current data. The physical restore copies the files byte for byte,
  so it keeps the stale contents. The investigation entry above shows this.
- **Why it's not staged:** I wrote the seed script to exercise a trigger, not
  to trip the check. I only noticed the ordering when the verification
  failed.
- **Fix:** `verify.sh` now compares a logical restore's materialized view
  with its own query on the restored data, and compares everything else
  exactly. Physical restores still have to match exactly, including the view.
- **What it means:** a logical restore is a rebuild, not a copy. If anything
  depends on a materialized view's current (possibly stale) contents, such as
  reports or reconciliations, the restored system will give different answers
  until you account for that.

## Screenshots

None. All the output here is terminal text.
