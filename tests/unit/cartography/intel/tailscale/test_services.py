from cartography.intel.tailscale.services import transform


def test_transform_preserves_prefixed_service_name() -> None:
    result = transform(
        [
            {
                "name": "svc:web-server",
                "addrs": ["100.100.100.1", "fd7a:115c:a1e0::1"],
                "ports": ["tcp:443"],
                "tags": ["tag:prod"],
            }
        ]
    )

    assert result[0]["id"] == "svc:web-server"
    assert result[0]["name"] == "svc:web-server"


def test_transform_adds_prefix_for_bare_service_name() -> None:
    result = transform(
        [
            {
                "name": "web-server",
                "addrs": ["100.100.100.1", "fd7a:115c:a1e0::1"],
                "ports": ["tcp:443"],
                "tags": ["tag:prod"],
            }
        ]
    )

    assert result[0]["id"] == "svc:web-server"
    assert result[0]["name"] == "web-server"
