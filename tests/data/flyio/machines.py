MACHINES_RESPONSE = [
    {
        "id": "90802949c92987",
        "name": "dry-rain-8738",
        "state": "started",
        "region": "lhr",
        "instance_id": "01KJQC1W6NXAK34WQ739F0ERSP",
        "private_ip": "fdaa:10:e286:a7b:34e:c803:57c:2",
        "config": {
            "env": {
                "PORT": "8000",
                "PRIMARY_REGION": "lhr",
            },
            "guest": {
                "cpu_kind": "shared",
                "cpus": 1,
                "memory_mb": 1024,
            },
            "metadata": {
                "fly_process_group": "app",
                "fly_release_id": "YgoYklRLL8Xo3fBPg6AoX28AG",
                "fly_release_version": "35",
            },
            "services": [
                {
                    "protocol": "tcp",
                    "internal_port": 8000,
                    "autostop": True,
                    "autostart": True,
                    "min_machines_running": 0,
                    "ports": [
                        {
                            "port": 80,
                            "handlers": ["http"],
                            "force_https": True,
                        },
                        {
                            "port": 443,
                            "handlers": ["http", "tls"],
                        },
                    ],
                    "force_instance_key": None,
                },
            ],
            "image": "registry.fly.io/nhmhvxo3b9:deployment-01JMWNHS84ZCCV89XYH9SQ48FX",
            "restart": {
                "policy": "on-failure",
                "max_retries": 10,
            },
        },
        "image_ref": {
            "registry": "registry.fly.io",
            "repository": "nhmhvxo3b9",
            "tag": "deployment-01JMWNHS84ZCCV89XYH9SQ48FX",
            "digest": "sha256:b0cbba70b2f1fbb720502cff65ca83bbdbca1e02a78860ce075efdb320eb9802",
            "labels": None,
        },
        "created_at": "2025-06-19T22:51:10Z",
        "updated_at": "2026-07-31T06:44:39Z",
        "host_status": "ok",
        "cordoned": False,
    },
]
