#!/usr/bin/env bash
# Daily incremental backup of the app data directory (SQLite DB + attachments).
#
# Each run produces a full-looking snapshot at backups/YYYY-MM-DD/, but files
# identical to the previous day's snapshot are hardlinked rather than copied
# (rsync --link-dest), so unchanged data costs no extra disk space -- only
# what actually changed since yesterday is physically new on disk. Deleting
# an old snapshot never breaks a newer one: the filesystem only frees a
# file's data once its last hardlink is removed.
#
# The SQLite file itself is never copied directly (the app runs in WAL mode
# and may be writing to it) -- it's read through sqlite3's online backup API
# first, which takes a transactionally consistent snapshot regardless of
# concurrent writers, then that consistent copy is what gets compared/linked.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data/app-data"
BACKUP_ROOT="${BACKUP_ROOT:-$PROJECT_ROOT/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE="${DATE:-$(date +%Y-%m-%d)}"
SNAPSHOT_DIR="$BACKUP_ROOT/$DATE"

if [ ! -f "$DATA_DIR/mechanic_shop.db" ]; then
    echo "No database found at $DATA_DIR/mechanic_shop.db -- nothing to back up." >&2
    exit 1
fi

# Most recent prior snapshot (if any), used as the rsync --link-dest base.
PREV_SNAPSHOT="$(find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -name '20*' 2>/dev/null \
    | sort | tail -n 1 || true)"

mkdir -p "$SNAPSHOT_DIR"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

echo "[$(date -Iseconds)] Backing up to $SNAPSHOT_DIR"

# Consistent DB snapshot via SQLite's own backup API (safe under concurrent writers).
python3 -c "
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
src.close()
dst.close()
" "$DATA_DIR/mechanic_shop.db" "$STAGING/mechanic_shop.db"

# The staged DB copy above is regenerated fresh every run, so its mtime is
# always "now" even when its content is byte-identical to yesterday's --
# rsync's --link-dest hardlink decision is a quick-check (size+mtime) and
# does NOT fall back to content comparison here even with -c/--checksum
# (verified empirically), so it would treat every day as "changed" and
# never hardlink. Compare content ourselves instead and hardlink by hand.
echo "-- database --"
if [ -n "$PREV_SNAPSHOT" ] && cmp -s "$STAGING/mechanic_shop.db" "$PREV_SNAPSHOT/mechanic_shop.db"; then
    ln "$PREV_SNAPSHOT/mechanic_shop.db" "$SNAPSHOT_DIR/mechanic_shop.db"
    echo "unchanged -- hardlinked to $PREV_SNAPSHOT/mechanic_shop.db"
else
    cp "$STAGING/mechanic_shop.db" "$SNAPSHOT_DIR/mechanic_shop.db"
    echo "changed -- new copy written"
fi

if [ -d "$DATA_DIR/attachments" ]; then
    echo "-- attachments --"
    mkdir -p "$SNAPSHOT_DIR/attachments"
    # Uploaded attachments are never rewritten in place (new uploads get a
    # fresh unique filename), so their mtimes are stable day to day and
    # rsync's default quick-check --link-dest hardlinking works correctly
    # here, unlike the regenerated DB file above.
    ATTACH_ARGS=(-a --itemize-changes)
    if [ -n "$PREV_SNAPSHOT" ] && [ -d "$PREV_SNAPSHOT/attachments" ]; then
        ATTACH_ARGS+=(--link-dest="$PREV_SNAPSHOT/attachments")
    fi
    rsync "${ATTACH_ARGS[@]}" "$DATA_DIR/attachments/" "$SNAPSHOT_DIR/attachments/"
fi

# Retention: prune snapshots older than RETENTION_DAYS. Safe with hardlinks --
# a file's data is only freed once its last referencing snapshot is gone.
find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -name '20*' -mtime "+$RETENTION_DAYS" \
    -exec rm -rf {} \;

echo "[$(date -Iseconds)] Backup complete: $SNAPSHOT_DIR"
