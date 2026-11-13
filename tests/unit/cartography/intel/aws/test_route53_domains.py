from datetime import datetime
from datetime import timezone

from cartography.intel.aws.route53_domains import transform_registered_domains


def test_transform_registered_domains():
    expiry = datetime(2027, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    raw = [
        {
            "DomainName": "example.com",
            "AutoRenew": True,
            "TransferLock": False,
            "Expiry": expiry,
        },
        {
            # Missing DomainName should be skipped
            "AutoRenew": True,
        },
    ]

    assert transform_registered_domains(raw) == [
        {
            "id": "example.com",
            "name": "example.com",
            "auto_renew": True,
            "transfer_lock": False,
            "expiry": expiry,
        },
    ]
