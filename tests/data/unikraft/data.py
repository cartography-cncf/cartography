ACCOUNT_QUOTAS_RESPONSE = {
    "status": "success",
    "op_time_us": 100,
    "data": {
        "quotas": [
            {
                "uuid": "acct-0001",
                "status": "success",
                "message": "",
            },
        ],
    },
}

INSTANCES_RESPONSE = [
    {
        "uuid": "inst-0001",
        "name": "cartography-test-instance",
        "created_at": "2026-01-01T00:00:00Z",
        "state": "running",
        "private_fqdn": "cartography-test-instance.internal",
        "image": "cartography-test:latest",
        "memory_mb": 128,
        "vcpus": 1,
        "args": "",
        "restart_policy": "never",
        "start_count": 1,
        "restart_count": 0,
        "started_at": "2026-01-01T00:00:01Z",
        "stopped_at": None,
        "uptime_ms": 3600000,
        "tags": ["test"],
        "status": "success",
        "message": "",
        "private_ip": "10.0.0.2",
        "gateway": "10.0.0.1",
        "nameserver": "10.0.0.1",
    },
]

VOLUMES_RESPONSE = [
    {
        "uuid": "vol-0001",
        "name": "cartography-test-volume",
        "created_at": "2026-01-01T00:00:00Z",
        "state": "available",
        "size_mb": 1024,
        "persistent": True,
        "tags": ["test"],
        "status": "success",
        "message": "",
        "quota_policy": "static",
        "filesystem": "ext4",
        "access_mode": "rwo",
        "mounted_by": [
            {
                "uuid": "inst-0001",
                "name": "cartography-test-instance",
                "readonly": False,
            },
        ],
    },
]

CERTIFICATES_RESPONSE = [
    {
        "uuid": "cert-0001",
        "name": "cartography-test-cert",
        "created_at": "2026-01-01T00:00:00Z",
        "common_name": "www.example.com",
        "subject": "CN=www.example.com",
        "issuer": "Let's Encrypt",
        "serial_number": "0123456789",
        "not_before": "2026-01-01T00:00:00Z",
        "not_after": "2026-04-01T00:00:00Z",
        "state": "valid",
        "status": "success",
        "message": "",
    },
]

SERVICE_GROUPS_RESPONSE = [
    {
        "uuid": "svc-0001",
        "name": "cartography-test-service",
        "created_at": "2026-01-01T00:00:00Z",
        "persistent": True,
        "autoscale": False,
        "soft_limit": 1,
        "hard_limit": 3,
        "status": "success",
        "message": "",
        "services": [{"port": 443, "destination_port": 8080, "handlers": ["tls"]}],
        "domains": [
            {
                "fqdn": "www.example.com",
                "certificate": {"uuid": "cert-0001"},
            },
        ],
        "instances": [{"uuid": "inst-0001", "name": "cartography-test-instance"}],
    },
]
