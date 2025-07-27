from datetime import datetime, timezone


class Clock:
    """Clock class."""

    def now(self) -> datetime:
        """Return the current datetime."""
        return datetime.now(timezone.utc).replace(microsecond=0)


clock = Clock()
