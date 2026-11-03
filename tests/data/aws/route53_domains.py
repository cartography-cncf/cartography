from datetime import datetime
from datetime import timezone

LIST_DOMAINS_RESPONSE = [
    {
        "DomainName": "example.com",
        "AutoRenew": True,
        "TransferLock": True,
        "Expiry": datetime(2027, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "DomainName": "orphan.test",
        "AutoRenew": False,
        "TransferLock": False,
        "Expiry": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    },
]
