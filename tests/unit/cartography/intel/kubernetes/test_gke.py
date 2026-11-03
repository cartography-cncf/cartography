import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.auth.credentials import Scoped
from googleapiclient.errors import HttpError

from cartography.intel.gcp.gke import transform_gke_clusters
from cartography.intel.gcp.gke import transform_node_pools
from cartography.intel.gcp.gke_utils import instance_id_from_provider_id
from cartography.intel.gcp.gke_utils import parse_cluster_ref
from cartography.intel.kubernetes.clusters import get_service_account_oidc
from cartography.intel.kubernetes.gke_auth import connect
from cartography.intel.kubernetes.gke_auth import get_cluster
from cartography.intel.kubernetes.gke_auth import get_credentials
from cartography.intel.kubernetes.gke_auth import SCOPES
from cartography.intel.kubernetes.gke_auth import select_endpoint
from cartography.intel.kubernetes.nodes import transform_nodes
from cartography.intel.kubernetes.util import gcp_forwarding_rule_match_keys
from cartography.intel.kubernetes.util import get_gke_network_scope
from cartography.intel.kubernetes.util import GKENetworkScope

RESOURCE = "projects/example-project/locations/us-central1/clusters/example"
DNS_CLUSTER = {
    "resource_name": RESOURCE,
    "controlPlaneEndpointsConfig": {
        "dnsEndpointConfig": {
            "endpoint": "example.gke.goog",
            "allowExternalTraffic": True,
        }
    },
}


def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp, json.dumps({"error": {"code": status}}).encode())


@pytest.mark.parametrize(
    "reference",
    [
        RESOURCE,
        RESOURCE.replace("locations", "zones"),
        "https://container.googleapis.com/v1/" + RESOURCE,
        "gke_example-project_us-central1_example",
    ],
)
def test_cluster_reference(reference):
    # Act
    ref = parse_cluster_ref(reference)

    # Assert
    assert ref.resource_name == RESOURCE


@pytest.mark.parametrize(
    "reference",
    [
        "example",
        "https://attacker.example/" + RESOURCE,
        RESOURCE + "/extra",
        "gke_example",
        "projects/a/locations/us-central1/clusters/../example",
    ],
)
def test_invalid_cluster_reference(reference):
    # Act and assert
    with pytest.raises(ValueError):
        parse_cluster_ref(reference)


def test_compute_provider_id():
    # Act and assert
    assert (
        instance_id_from_provider_id("gce://example-project/us-central1-a/node")
        == "projects/example-project/zones/us-central1-a/instances/node"
    )
    assert instance_id_from_provider_id("aws:///us-east-1a/i-123") is None
    assert instance_id_from_provider_id(None) is None


def test_transform_nodes_links_gke_node_pool_only_with_gke_metadata():
    # Arrange
    node = SimpleNamespace(
        metadata=SimpleNamespace(
            name="node", labels={"cloud.google.com/gke-nodepool": "pool"}
        ),
        spec=SimpleNamespace(provider_id="gce://example-project/us-central1-a/node"),
        status=None,
    )

    # Act
    gke = transform_nodes([node], "cluster", RESOURCE)[0]
    plain = transform_nodes([node], "cluster")[0]

    # Assert
    assert gke["gke_node_pool_id"] == f"{RESOURCE}/nodePools/pool"
    assert plain["gke_node_pool_id"] is None
    assert plain["gke_node_pool"] == "pool"


def test_endpoint_selection_never_falls_back_to_allocated_ip():
    # Arrange
    cluster = {
        "controlPlaneEndpointsConfig": {
            "dnsEndpointConfig": {
                "endpoint": "example.gke.goog",
                "allowExternalTraffic": True,
            },
            "ipEndpointsConfig": {"enabled": False},
        },
        "privateClusterConfig": {"publicEndpoint": "192.0.2.1"},
    }

    # Act and assert
    assert select_endpoint(cluster, "dns") == ("https://example.gke.goog", True)
    with pytest.raises(ValueError, match="disabled"):
        select_endpoint(cluster, "public")
    cluster["controlPlaneEndpointsConfig"]["dnsEndpointConfig"][
        "allowExternalTraffic"
    ] = False
    with pytest.raises(ValueError):
        select_endpoint(cluster, "dns")


def test_native_client_refreshes_token_per_request():
    # Arrange
    credentials = MagicMock(valid=True, token="first")

    # Act
    with connect(DNS_CLUSTER, credentials) as client:
        config = client.core.api_client.configuration
        first = config.auth_settings()["BearerToken"]["value"]
        credentials.token = "second"
        second = config.auth_settings()["BearerToken"]["value"]

        # Assert
        assert first == "Bearer first"
        assert second == "Bearer second"
        assert config.verify_ssl is True
        assert client.core.api_client is client.rbac.api_client
        assert client.name == "gke_example-project_us-central1_example"
        assert (
            client.tls_diagnostics["kubeconfig_tls_configuration_status"] == "public_ca"
        )


@pytest.mark.parametrize("status", [403, 404])
def test_get_cluster_skips_unreadable_cluster(status):
    # Arrange
    container = MagicMock()
    container.projects.return_value.locations.return_value.clusters.return_value.get.return_value.execute.side_effect = _http_error(
        status
    )

    # Act
    with patch(
        "cartography.intel.kubernetes.gke_auth.build_client", return_value=container
    ):
        result = get_cluster(RESOURCE, MagicMock())

    # Assert
    assert result is None


def test_get_cluster_keeps_requested_project_id():
    # Arrange
    container = MagicMock()
    container.projects.return_value.locations.return_value.clusters.return_value.get.return_value.execute.return_value = {
        "selfLink": "https://container.googleapis.com/v1/projects/111122223333/locations/us-central1/clusters/example",
    }

    # Act
    with patch(
        "cartography.intel.kubernetes.gke_auth.build_client", return_value=container
    ):
        result = get_cluster("gke_example-project_us-central1_example", MagicMock())

    # Assert
    assert result is not None
    assert result["resource_name"] == RESOURCE


def test_control_plane_fields_dns_endpoint_is_public_access():
    # Arrange
    cluster = {
        "name": "example",
        "selfLink": "https://container.googleapis.com/v1/" + RESOURCE,
        "networkConfig": {"datapathProvider": "ADVANCED_DATAPATH"},
        "controlPlaneEndpointsConfig": {
            "dnsEndpointConfig": {
                "endpoint": "example.gke.goog",
                "allowExternalTraffic": True,
            },
            "ipEndpointsConfig": {"enabled": False},
        },
        "privateClusterConfig": {
            "enablePrivateEndpoint": True,
            "publicEndpoint": "192.0.2.1",
        },
    }

    # Act
    transformed = transform_gke_clusters({"clusters": [cluster]})[0]

    # Assert
    assert transformed["network_policy"] == "DATAPLANE_V2"
    assert transformed["resource_name"] == RESOURCE
    assert transformed["ip_endpoints_enabled"] is False
    assert transformed["public_ip_endpoint_enabled"] is False
    assert transformed["dns_endpoint_enabled"] is True
    assert transformed["control_plane_public_access"] is True


def test_control_plane_fields_fall_back_to_private_cluster_config():
    # Arrange
    cluster = {
        "name": "example",
        "selfLink": "https://container.googleapis.com/v1/" + RESOURCE,
        "privateClusterConfig": {"enablePrivateEndpoint": True},
    }

    # Act
    transformed = transform_gke_clusters({"clusters": [cluster]})[0]

    # Assert
    assert transformed["dns_endpoint_enabled"] is None
    assert transformed["control_plane_public_access"] is False


def test_oidc_discovery_reads_raw_json_without_following_jwks_uri():
    # Arrange
    response = MagicMock(
        data=b'{"issuer":"https://issuer.example","jwks_uri":"https://keys.example/jwks","extra":"not-collected"}'
    )
    with connect(DNS_CLUSTER, MagicMock(valid=True, token="test-token")) as client:
        with patch.object(
            client.core.api_client, "request", return_value=response
        ) as request:
            # Act
            result = get_service_account_oidc(client)

            # Assert
            assert result == {
                "issuer": "https://issuer.example",
                "jwks_uri": "https://keys.example/jwks",
            }
            assert request.call_count == 1
            assert (
                request.call_args.args[1]
                == "https://example.gke.goog/.well-known/openid-configuration"
            )
            response.release_conn.assert_called_once()


def test_get_credentials_uses_provided_source_without_adc():
    # Arrange
    source = MagicMock()

    # Act
    with patch("cartography.intel.kubernetes.gke_auth.google.auth.default") as adc:
        credentials = get_credentials(source=source)

    # Assert
    assert credentials is source
    adc.assert_not_called()


def test_get_credentials_impersonates_from_provided_source():
    # Arrange
    source = MagicMock()

    # Act
    with patch("cartography.intel.kubernetes.gke_auth.google.auth.default") as adc:
        credentials = get_credentials(
            "reader@example-project.iam.gserviceaccount.com", source
        )

    # Assert
    adc.assert_not_called()
    assert credentials.service_account_email == (
        "reader@example-project.iam.gserviceaccount.com"
    )


def test_gke_clients_use_config_credentials_instead_of_adc():
    # Arrange
    from cartography.config import Config
    from cartography.intel.kubernetes import _get_clients

    source = MagicMock()
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        gke_clusters=[RESOURCE],
        gke_credentials=source,
    )

    # Act
    with (
        patch("cartography.intel.kubernetes.gke_auth.google.auth.default") as adc,
        patch(
            "cartography.intel.kubernetes.gke_auth.get_cluster", return_value=None
        ) as get_cluster_mock,
    ):
        clients = list(_get_clients(config))

    # Assert
    assert clients == []
    adc.assert_not_called()
    get_cluster_mock.assert_called_once_with(RESOURCE, source)


def test_get_credentials_scopes_unscoped_source():
    # Arrange
    source = MagicMock(spec=Scoped, requires_scopes=True)

    # Act
    with patch("cartography.intel.kubernetes.gke_auth.google.auth.default") as adc:
        credentials = get_credentials(source=source)

    # Assert
    adc.assert_not_called()
    assert source.with_scopes.call_args.args == (SCOPES,)
    assert credentials is source.with_scopes.return_value


def test_forwarding_rule_match_keys_split_private_and_public_addresses():
    # Arrange
    scope = GKENetworkScope(
        "example-project", "projects/example-project/global/networks/vpc"
    )

    # Act
    keys = gcp_forwarding_rule_match_keys(["10.0.0.2", "34.120.0.10", "bad"], scope)
    no_gke = gcp_forwarding_rule_match_keys(["10.0.0.2"], None)

    # Assert
    assert keys == {
        "gcp_project_id": "example-project",
        "gcp_network": "projects/example-project/global/networks/vpc",
        "gcp_public_lb_ips": ["34.120.0.10"],
        "gcp_private_lb_ips": ["10.0.0.2"],
    }
    assert no_gke["gcp_public_lb_ips"] == no_gke["gcp_private_lb_ips"] == []


@pytest.mark.parametrize(
    "network",
    [
        {"networkConfig": {"network": "projects/host/global/networks/shared"}},
        {
            "networkConfig": {
                "network": "https://www.googleapis.com/compute/v1/projects/host/global/networks/shared"
            }
        },
    ],
)
def test_gke_network_scope_keeps_shared_vpc_host_project(network):
    # Arrange
    client = SimpleNamespace(gke_cluster={"resource_name": RESOURCE, **network})

    # Act
    scope = get_gke_network_scope(client)

    # Assert
    assert scope == GKENetworkScope(
        "example-project", "projects/host/global/networks/shared"
    )


def test_transform_node_pools_resolves_default_service_account():
    # Arrange
    response = {
        "clusters": [
            {
                "selfLink": "https://container.googleapis.com/v1/" + RESOURCE,
                "nodePools": [
                    {"name": "default-sa", "config": {"serviceAccount": "default"}},
                    {"name": "no-sa", "config": {}},
                    {
                        "name": "custom",
                        "config": {
                            "serviceAccount": "nodes@example-project.iam.gserviceaccount.com"
                        },
                    },
                ],
            },
        ],
    }

    # Act
    pools = {
        p["name"]: p["service_account"] for p in transform_node_pools(response, "123")
    }

    # Assert
    assert pools == {
        "default-sa": "123-compute@developer.gserviceaccount.com",
        "no-sa": "123-compute@developer.gserviceaccount.com",
        "custom": "nodes@example-project.iam.gserviceaccount.com",
    }
