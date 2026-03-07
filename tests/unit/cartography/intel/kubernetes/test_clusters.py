import json
from datetime import datetime
from datetime import timezone
from types import SimpleNamespace

from cartography.intel.kubernetes.clusters import transform_kubernetes_cluster
from cartography.intel.kubernetes.util import get_kubeconfig_tls_diagnostics


def _write_kubeconfig(tmp_path, config_dict):
    config_path = tmp_path / "kubeconfig.json"
    config_path.write_text(json.dumps(config_dict))
    return str(config_path)


def test_get_kubeconfig_tls_diagnostics_with_certificate_authority_data(tmp_path):
    kubeconfig = _write_kubeconfig(
        tmp_path,
        {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "cluster-1",
                    "cluster": {
                        "server": "https://kubernetes.example.com",
                        "certificate-authority-data": "base64-ca-data",
                    },
                }
            ],
            "contexts": [
                {
                    "name": "context-1",
                    "context": {"cluster": "cluster-1", "user": "user-1"},
                }
            ],
            "users": [{"name": "user-1", "user": {"token": "token-value"}}],
        },
    )

    result = get_kubeconfig_tls_diagnostics("context-1", kubeconfig)

    assert result["api_server_url"] == "https://kubernetes.example.com"
    assert result["kubeconfig_insecure_skip_tls_verify"] is None
    assert result["kubeconfig_has_certificate_authority_data"] is True
    assert result["kubeconfig_has_certificate_authority_file"] is False
    assert result["kubeconfig_ca_file_path"] is None
    assert result["kubeconfig_has_client_certificate"] is False
    assert result["kubeconfig_has_client_key"] is False
    assert result["kubeconfig_tls_configuration_status"] == "valid_config"


def test_get_kubeconfig_tls_diagnostics_with_certificate_authority_file(tmp_path):
    kubeconfig = _write_kubeconfig(
        tmp_path,
        {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "cluster-1",
                    "cluster": {
                        "server": "https://kubernetes.example.com",
                        "certificate-authority": "/tmp/ca.crt",
                    },
                }
            ],
            "contexts": [
                {
                    "name": "context-1",
                    "context": {"cluster": "cluster-1", "user": "user-1"},
                }
            ],
            "users": [{"name": "user-1", "user": {"token": "token-value"}}],
        },
    )

    result = get_kubeconfig_tls_diagnostics("context-1", kubeconfig)

    assert result["kubeconfig_has_certificate_authority_data"] is False
    assert result["kubeconfig_has_certificate_authority_file"] is True
    assert result["kubeconfig_ca_file_path"] == "/tmp/ca.crt"
    assert result["kubeconfig_tls_configuration_status"] == "valid_config"


def test_get_kubeconfig_tls_diagnostics_insecure_skip_tls(tmp_path):
    kubeconfig = _write_kubeconfig(
        tmp_path,
        {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "cluster-1",
                    "cluster": {
                        "server": "https://kubernetes.example.com",
                        "insecure-skip-tls-verify": True,
                    },
                }
            ],
            "contexts": [
                {
                    "name": "context-1",
                    "context": {"cluster": "cluster-1", "user": "user-1"},
                }
            ],
            "users": [
                {
                    "name": "user-1",
                    "user": {
                        "client-certificate": "/tmp/client.crt",
                        "client-key": "/tmp/client.key",
                    },
                }
            ],
        },
    )

    result = get_kubeconfig_tls_diagnostics("context-1", kubeconfig)

    assert result["kubeconfig_insecure_skip_tls_verify"] is True
    assert result["kubeconfig_has_client_certificate"] is True
    assert result["kubeconfig_has_client_key"] is True
    assert result["kubeconfig_tls_configuration_status"] == "insecure_skip_tls"


def test_get_kubeconfig_tls_diagnostics_missing_ca_material(tmp_path):
    kubeconfig = _write_kubeconfig(
        tmp_path,
        {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "cluster-1",
                    "cluster": {"server": "https://kubernetes.example.com"},
                }
            ],
            "contexts": [
                {
                    "name": "context-1",
                    "context": {"cluster": "cluster-1", "user": "user-1"},
                }
            ],
            "users": [
                {
                    "name": "user-1",
                    "user": {
                        "client-certificate-data": "base64-client-cert",
                        "client-key-data": "base64-client-key",
                    },
                }
            ],
        },
    )

    result = get_kubeconfig_tls_diagnostics("context-1", kubeconfig)

    assert result["kubeconfig_has_certificate_authority_data"] is False
    assert result["kubeconfig_has_certificate_authority_file"] is False
    assert result["kubeconfig_has_client_certificate"] is True
    assert result["kubeconfig_has_client_key"] is True
    assert result["kubeconfig_tls_configuration_status"] == "missing_ca_material"


def test_get_kubeconfig_tls_diagnostics_unknown_context(tmp_path):
    kubeconfig = _write_kubeconfig(
        tmp_path,
        {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [],
            "contexts": [],
            "users": [],
        },
    )

    result = get_kubeconfig_tls_diagnostics("missing-context", kubeconfig)

    assert result["kubeconfig_tls_configuration_status"] == "unknown"
    assert result["api_server_url"] is None


def test_transform_kubernetes_cluster_merges_tls_diagnostics(monkeypatch):
    fake_diagnostics = {
        "api_server_url": "https://kubernetes.example.com",
        "kubeconfig_insecure_skip_tls_verify": False,
        "kubeconfig_has_certificate_authority_data": True,
        "kubeconfig_has_certificate_authority_file": False,
        "kubeconfig_ca_file_path": None,
        "kubeconfig_has_client_certificate": True,
        "kubeconfig_has_client_key": True,
        "kubeconfig_tls_configuration_status": "valid_config",
    }
    client = SimpleNamespace(
        name="context-1",
        config_file="/tmp/kubeconfig",
        external_id="arn:aws:eks:us-east-1:123456789012:cluster/context-1",
    )
    namespace = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="cluster-uid-1",
            creation_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
    )
    version = SimpleNamespace(
        git_version="v1.31.0",
        major="1",
        minor="31",
        go_version="go1.22.0",
        compiler="gc",
        platform="linux/amd64",
    )

    transformed = transform_kubernetes_cluster(
        client,
        namespace,
        version,
        fake_diagnostics,
    )

    assert len(transformed) == 1
    cluster = transformed[0]
    assert cluster["id"] == "cluster-uid-1"
    assert cluster["name"] == "context-1"
    assert cluster["api_server_url"] == "https://kubernetes.example.com"
    assert cluster["kubeconfig_has_certificate_authority_data"] is True
    assert cluster["kubeconfig_tls_configuration_status"] == "valid_config"
