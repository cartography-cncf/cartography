from typing import Any
from typing import Dict
from typing import List

CLOUDFLARE_FIREWALLRULES: List[Dict[str, Any]] = [
    {
        "id": "4b7f36f8b5b8c5d6e7f8a9b0c1d2e3f4",
        "action": "block",
        "description": "Block known bad IPs",
        "filter": {
            "id": "3a1c5f9e7b3a4c5d6e7f8a9b0c1d2e3f",
            "description": "Known bad IPs",
            "expression": "ip.src in {1.2.3.4 5.6.7.8}",
            "paused": False,
            "ref": "FILTER1",
        },
        "paused": False,
        "priority": 1,
        "products": ["waf", "rateLimit"],
        "ref": "RULE1",
    },
    {
        "id": "9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a",
        "action": "challenge",
        "description": "Challenge traffic from suspicious ASNs",
        "filter": {
            "id": "6e5d4c3b2a1f9e8d7c6b5a4f3e2d1c0b",
            "description": None,
            "expression": "ip.geoip.asnum in {64512}",
            "paused": False,
            "ref": None,
        },
        "paused": False,
        "priority": 2,
        "products": [],
        "ref": "RULE2",
    },
    {
        "id": "a1b2c3d4e5f60718293a4b5c6d7e8f90",
        "action": "allow",
        "description": None,
        "filter": None,
        "paused": True,
        "priority": 100,
        "products": ["zoneLockdown"],
        "ref": "RULE3",
    },
]
