-- M14: never let a delayed/equal-time watchdog replace newer alert status.
-- Atomic D1 batch will roll back any opened/updated/recovered event INSERTs
-- that occurred earlier in the same batch when this monotonicity check aborts.
CREATE TRIGGER IF NOT EXISTS monitor_watchdog_state_no_rewind
BEFORE UPDATE OF last_checked_utc ON monitor_watchdog_state
FOR EACH ROW
WHEN NEW.last_checked_utc <= OLD.last_checked_utc
BEGIN
 SELECT RAISE(ABORT, 'STALE_MONITOR_WATCHDOG');
END;
