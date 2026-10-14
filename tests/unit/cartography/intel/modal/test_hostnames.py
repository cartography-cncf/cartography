from cartography.intel.modal.functions import transform
from cartography.intel.modal.sandboxes import transform_tunnels


def test_function_transform_extracts_canonical_web_hostname():
    # Arrange
    functions = [
        {
            "id": "function-1",
            "name": "web",
            "app_id": "app-1",
            "web_url": "https://Web.Modal.Example.COM./path",
            "is_web_endpoint": True,
        }
    ]

    # Act
    [function] = transform(functions, [], "main")

    # Assert
    assert function["web_url"] == "https://Web.Modal.Example.COM./path"
    assert function["web_hostname"] == "web.modal.example.com"


def test_tunnel_transform_normalizes_both_hostnames():
    # Arrange
    sandboxes = [
        {
            "id": "sandbox-1",
            "tunnels": [
                {
                    "container_port": 8080,
                    "host": " TLS.Modal.Example.COM. ",
                    "unencrypted_host": " Clear.Modal.Example.COM. ",
                }
            ],
        }
    ]

    # Act
    [tunnel] = transform_tunnels(sandboxes, "main")

    # Assert
    assert tunnel["host"] == " TLS.Modal.Example.COM. "
    assert tunnel["host_normalized"] == "tls.modal.example.com"
    assert tunnel["unencrypted_host"] == " Clear.Modal.Example.COM. "
    assert tunnel["unencrypted_host_normalized"] == "clear.modal.example.com"
