from cartography.intel.modal.functions import transform
from cartography.intel.modal.sandboxes import transform_tunnels


def test_function_transform_extracts_canonical_web_hostname():
    [function] = transform(
        [
            {
                "id": "function-1",
                "name": "web",
                "app_id": "app-1",
                "web_url": "https://Web.Modal.Test./path",
                "is_web_endpoint": True,
            }
        ],
        [],
        "main",
    )

    assert function["web_url"] == "https://Web.Modal.Test./path"
    assert function["web_hostname"] == "web.modal.test"


def test_tunnel_transform_normalizes_both_hostnames():
    [tunnel] = transform_tunnels(
        [
            {
                "id": "sandbox-1",
                "tunnels": [
                    {
                        "container_port": 8080,
                        "host": " TLS.Modal.Test. ",
                        "unencrypted_host": " Clear.Modal.Test. ",
                    }
                ],
            }
        ],
        "main",
    )

    assert tunnel["host"] == " TLS.Modal.Test. "
    assert tunnel["host_normalized"] == "tls.modal.test"
    assert tunnel["unencrypted_host"] == " Clear.Modal.Test. "
    assert tunnel["unencrypted_host_normalized"] == "clear.modal.test"
