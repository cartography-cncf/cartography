from datetime import datetime
from datetime import timezone

from dateutil.parser import isoparse


def parse_utc_datetime(value: str | None) -> datetime | None:
    """
    A value without an offset is read as UTC. Stored as is, it would become a
    Neo4j LocalDateTime, and comparing that with a zoned DateTime returns null,
    so range filters would silently drop the row.
    """
    if value is None or value == "":
        return None
    parsed = isoparse(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
