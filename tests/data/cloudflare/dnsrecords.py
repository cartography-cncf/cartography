from typing import Any
from typing import Dict
from typing import List

CLOUDFLARE_DNSRECORDS: List[Dict[str, Any]] = [
    {
        "comment": None,
        "content": "1.2.3.4",
        "name": "simpson.corp",
        "proxied": False,
        "settings": {},
        "tags": [],
        "ttl": 1,
        "type": "A",
        "id": "2b534a38-8658-48c0-8d6d-f9277d689c75",
        "created_on": "2014-01-01T05:20:00.12345Z",
        "proxiable": True,
    },
    {
        "comment": None,
        "content": "simpson.corp",
        "name": "www.simpson.corp",
        "proxied": True,
        "settings": {},
        "tags": [],
        "ttl": 1,
        "type": "CNAME",
        "id": "922f7919-e12b-4f46-800f-74b433724d29",
        "created_on": "2014-01-01T05:20:00.12345Z",
        "proxiable": True,
    },
]
