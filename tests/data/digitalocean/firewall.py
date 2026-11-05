from typing import Any

FIREWALLS_RESPONSE: dict[str, Any] = {
    "firewalls": [
        {
            "id": "9321bbf2-6ca7-4944-b060-866226df3771",
            "name": "Test Firewall",
            "status": "succeeded",
            "inbound_rules": [
                {
                    "protocol": "icmp",
                    "ports": "0",
                    "sources": {"addresses": ["1.2.3.4"]},
                    "action": "allow",
                },
                {
                    "protocol": "tcp",
                    "ports": "1-64293",
                    "sources": {
                        "addresses": ["::/0", "0.0.0.0/0"],
                        "tags": ["frontend"],
                        "droplet_ids": [568030246],
                    },
                    "action": "allow",
                },
                {
                    "protocol": "tcp",
                    "ports": "22",
                    "sources": {"addresses": ["10.0.0.0/8"]},
                    # action intentionally omitted
                },
                {
                    "protocol": "tcp",
                    "ports": "80",
                    "sources": {"addresses": ["192.168.1.0/24"]},
                    "action": None,
                },
                {
                    "protocol": "tcp",
                    "ports": "443",
                    "sources": {"addresses": ["203.0.113.0/24"]},
                    "action": "",
                },
                {
                    "protocol": "tcp",
                    "ports": "8080",
                    "sources": {"addresses": ["198.51.100.0/24"]},
                    "action": "deny",
                },
            ],
            "outbound_rules": [
                {
                    "protocol": "tcp",
                    "ports": "0",
                    "destinations": {
                        "addresses": ["0.0.0.0/0", "::/0"],
                        "load_balancer_uids": ["test-load-balancer-uuid"],
                        "droplet_ids": [568030246],
                    },
                    "action": "allow",
                },
            ],
            "created_at": "2026-04-29T20:58:31Z",
            "droplet_ids": [568030246],
            "tags": [],
            "pending_changes": [],
        },
    ],
    "links": {},
    "meta": {"total": 1},
}
