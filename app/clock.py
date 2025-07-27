from datetime import datetime, timezone


class Clock:
    """Clock class."""

    def now(self, full: bool = False) -> datetime:
        """Get current time

        Args:
            full (bool, optional): Get full datetime. Defaults to False.

        Returns:
            datetime:
        """

        return (
            datetime.now(timezone.utc)
            if full
            else datetime.now(timezone.utc).replace(microsecond=0)
        )


clock = Clock()
