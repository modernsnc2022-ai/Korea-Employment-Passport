-- M13: database-level fail-closed anti-rewind for overlapping source Cron invocations.
-- An older/equal schedule stamp MUST abort the entire D1 batch: no phantom review
-- inserts, no stale source checkpoint and no stale success reset.
-- D1 worker API batch() runs an atomic transaction and rolls back on SQL failure.
CREATE TRIGGER IF NOT EXISTS monitor_source_snapshot_no_rewind
BEFORE UPDATE OF checked_at_utc ON monitor_source_snapshot
FOR EACH ROW
WHEN NEW.checked_at_utc <= OLD.checked_at_utc
BEGIN
 SELECT RAISE(ABORT, 'STALE_MONITOR_SNAPSHOT');
END;
