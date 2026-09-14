"""Pure prepare/commit/rollback orchestration used by Blender operations."""

from dataclasses import dataclass


class DependencyRollbackError(RuntimeError):
    """The operation failed and one or more recovery actions also failed."""

    def __init__(self, operation_error, rollback_errors):
        self.operation_error = operation_error
        self.rollback_errors = tuple(rollback_errors)
        details = "; ".join(str(error) for error in self.rollback_errors)
        super().__init__(f"{operation_error} / dependency rollback failed: {details}")


class OperationRecovery:
    """One-shot, best-effort recovery shared by all managed operations."""

    def __init__(self):
        self.actions = []
        self.attempted = False
        self.failure = None

    def add(self, action):
        if self.attempted:
            raise RuntimeError("recovery has already been attempted")
        self.actions.append(action)
        return action

    def __call__(self, _snapshot=None):
        if self.attempted:
            if self.failure is not None:
                raise self.failure
            return
        self.attempted = True
        errors = []
        for action in self.actions:
            try:
                action()
            except Exception as error:
                errors.append(error)
        if errors:
            self.failure = DependencyRollbackError(
                RuntimeError("operation state restore failed"), errors)
            raise self.failure


def recover_operation(operation_error, recovery):
    """Run operation recovery and return the complete reportable failure."""
    try:
        recovery()
    except DependencyRollbackError as recovery_error:
        return DependencyRollbackError(
            operation_error, recovery_error.rollback_errors)
    except Exception as recovery_error:
        return DependencyRollbackError(operation_error, (recovery_error,))
    return operation_error


def dependency_union(before, after):
    """Return a stable identity union of pre/post dependency captures."""
    result, seen = [], set()
    for item in tuple(before) + tuple(after):
        if id(item) not in seen:
            seen.add(id(item))
            result.append(item)
    return tuple(result)


@dataclass
class PreparedChange:
    replacement: object
    commit: object
    rollback: object
    discard: object = lambda _replacement: None
    dispose_old: object = lambda: None


def prepare_allocated_change(allocate, build, commit, rollback, discard,
                             dispose_old=lambda: None):
    """Allocate/build safely even when failure precedes PreparedChange return."""
    replacement = allocate()
    try:
        build(replacement)
    except Exception as operation_error:
        try:
            discard(replacement)
        except Exception as discard_error:
            raise DependencyRollbackError(
                operation_error, (discard_error,)) from operation_error
        raise
    return PreparedChange(replacement, commit, rollback, discard, dispose_old)


class DependencyTransaction:
    """Prepare every resource, then atomically commit all resource kinds."""

    def __init__(self, snapshot=None, restore=lambda _snapshot: None):
        self.snapshot, self.restore = snapshot, restore
        self._prepared, self._committed = [], []
        self._restore_attempted = False
        self.cleanup_errors = ()
        self.state = "NEW"

    @property
    def can_rollback(self):
        return self.state in {"NEW", "PREPARED", "SWAPPED"}

    def prepare(self, factories):
        if self.state != "NEW":
            raise RuntimeError(f"prepare is invalid in {self.state}")
        try:
            for factory in factories:
                self._prepared.append(factory())
        except Exception as operation_error:
            errors = self._recover(include_committed=False)
            if errors:
                raise DependencyRollbackError(operation_error, errors) from operation_error
            raise
        self.state = "PREPARED"
        return tuple(self._prepared)

    def commit_swaps(self):
        """Swap prepared resources but retain rollback and old resources."""
        if self.state != "PREPARED":
            raise RuntimeError(f"commit_swaps is invalid in {self.state}")
        try:
            for change in self._prepared:
                self._committed.append(change)
                change.commit(change.replacement)
        except Exception as operation_error:
            errors = self._recover(include_committed=True)
            if errors:
                raise DependencyRollbackError(operation_error, errors) from operation_error
            raise
        self.state = "SWAPPED"
        return tuple(change.replacement for change in self._prepared)

    def finalize(self):
        """Release old resources only after the complete operation succeeds."""
        if self.state != "SWAPPED":
            raise RuntimeError(f"finalize is invalid in {self.state}")
        cleanup_errors = []
        for change in self._prepared:
            try:
                change.dispose_old()
            except Exception as error:
                cleanup_errors.append(error)
        self._prepared.clear()
        self._committed.clear()
        # The committed state is valid.  Keep cleanup diagnostics available,
        # but never roll a successful operation back after old data disposal.
        self.cleanup_errors = tuple(cleanup_errors)
        self.state = "FINALIZED"
        return self.cleanup_errors

    def commit(self, defer_cleanup=False):
        result = self.commit_swaps()
        if not defer_cleanup:
            self.finalize()
        return result

    def rollback(self, operation_error=None):
        """Explicit recovery; raise when any recovery action fails."""
        if not self.can_rollback:
            raise RuntimeError(f"rollback is invalid in {self.state}")
        errors = self._recover(include_committed=True)
        self.state = "ROLLED_BACK"
        if errors:
            raise DependencyRollbackError(
                operation_error or RuntimeError("dependency rollback"), errors)
        return ()

    def _recover(self, include_committed):
        errors = []
        if include_committed:
            for change in reversed(self._committed):
                try:
                    change.rollback()
                except Exception as error:
                    errors.append(error)
        self._committed.clear()
        if not self._restore_attempted:
            self._restore_attempted = True
            try:
                self.restore(self.snapshot)
            except Exception as error:
                errors.append(error)
        # Discard is independent of restore and every replacement is attempted.
        for change in reversed(self._prepared):
            try:
                change.discard(change.replacement)
            except Exception as error:
                errors.append(error)
        self._prepared.clear()
        self.state = "ROLLED_BACK"
        return errors


def run_dependency_transaction(snapshot, restore, mutate, capture_before,
                               capture_after, prepare_change):
    """Production orchestration: mutate, OLD union NEW, prepare, commit."""
    transaction = DependencyTransaction(snapshot, restore)
    before = tuple(capture_before())
    try:
        result = mutate()
        affected = dependency_union(before, capture_after())
        transaction.prepare(lambda item=item: prepare_change(item)
                            for item in affected)
        transaction.commit()
        return result, affected
    except Exception as operation_error:
        if transaction.can_rollback:
            transaction.rollback(operation_error)
        raise
