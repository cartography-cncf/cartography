TAILSCALE_SERVICES = [
    {
        "name": "web-server",
        "addrs": ["100.100.100.1", "fd7a:115c:a1e0::1"],
        "comment": "Production web server",
        "ports": ["tcp:443", "tcp:80"],
        "tags": ["tag:byod"],
    },
    {
        "name": "database",
        "addrs": ["100.100.100.2", "fd7a:115c:a1e0::2"],
        "comment": "PostgreSQL cluster",
        "ports": ["tcp:5432"],
        "tags": [],
    },
]
