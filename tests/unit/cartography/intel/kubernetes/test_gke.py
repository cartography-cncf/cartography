from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.gcp.gke import get_gke_clusters
from cartography.intel.gcp.gke import transform_gke_clusters
from cartography.intel.gcp.gke_utils import instance_id_from_provider_id
from cartography.intel.gcp.gke_utils import parse_cluster_ref
from cartography.intel.kubernetes.gke import match_load_balancers
from cartography.intel.kubernetes.gke import match_workload_policies
from cartography.intel.kubernetes.gke import principal_members
from cartography.intel.kubernetes.gke_auth import connect
from cartography.intel.kubernetes.gke_auth import select_endpoint

RESOURCE = "projects/example-project/locations/us-central1/clusters/example"
POOL = "projects/111122223333/locations/global/workloadIdentityPools/example-project.svc.id.goog"
SA = {
    "id": "cluster/ns/app",
    "namespace": "ns",
    "name": "app",
    "uid": "sa-uid",
    "gcp_service_account": "app@example-project.iam.gserviceaccount.com",
}


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


@pytest.mark.parametrize("selector", sorted(principal_members(SA, POOL, RESOURCE)))
def test_wif_documented_selectors(selector):
    # Arrange
    binding = {
        "id": "binding",
        "raw_members": [selector],
        "role": "roles/storage.objectViewer",
        "has_condition": False,
        "lastupdated": 10,
    }
    # Act
    grants, impersonations = match_workload_policies([SA], [binding], POOL, RESOURCE)
    # Assert
    assert grants == [
        {
            "source_id": SA["id"],
            "target_id": "binding",
            "matched_members": [selector],
            "policy_lastupdated": 10,
        }
    ]
    assert impersonations == []


def test_wif_exact_matching_and_conditions():
    # Arrange
    subject = f"principal://iam.googleapis.com/{POOL}/subject/ns/ns/sa/app"
    bindings = [
        {
            "id": "good",
            "raw_members": [subject],
            "role": "roles/iam.workloadIdentityUser",
            "service_account_emails": [SA["gcp_service_account"]],
            "has_condition": False,
        },
        {
            "id": "conditional",
            "raw_members": [subject],
            "role": "roles/iam.workloadIdentityUser",
            "service_account_emails": [SA["gcp_service_account"]],
            "has_condition": True,
        },
        {
            "id": "wrong-gsa",
            "raw_members": [subject],
            "role": "roles/iam.workloadIdentityUser",
            "service_account_emails": ["other@example-project.iam.gserviceaccount.com"],
            "has_condition": False,
        },
        {"id": "wrong-sa", "raw_members": [subject + "-other"]},
        {
            "id": "wrong-project",
            "raw_members": [subject.replace("111122223333", "444455556666")],
        },
        {"id": "pool-only", "wif_pools": [POOL]},
    ]
    # Act
    grants, impersonations = match_workload_policies([SA], bindings, POOL, RESOURCE)
    # Assert
    assert {r["target_id"] for r in grants} == {"good", "conditional", "wrong-gsa"}
    assert len(impersonations) == 1
    assert impersonations[0]["target_id"] == SA["gcp_service_account"]


def test_wif_same_subject_across_clusters_but_uid_and_cluster_selectors_differ():
    # Arrange
    other = {**SA, "id": "other/ns/app", "uid": "other-uid"}
    other_resource = RESOURCE.replace("clusters/example", "clusters/other")
    # Act
    shared = principal_members(SA, POOL, RESOURCE) & principal_members(
        other, POOL, other_resource
    )
    # Assert
    assert len(shared) == 4
    assert not any(
        "kubernetes.cluster/" in m or "serviceaccount.uid/" in m for m in shared
    )


def test_lb_project_network_and_status_address():
    # Arrange
    resources = [
        {"id": "svc", "load_balancer_ips": ["10.0.0.2", "2001:db8::1", "invalid"]}
    ]
    network = "projects/host-project/global/networks/shared"
    rules = [
        {
            "id": "internal",
            "ip_address": "10.0.0.2",
            "project_id": "example-project",
            "network": network,
            "load_balancing_scheme": "INTERNAL",
        },
        {
            "id": "wrong-network",
            "ip_address": "10.0.0.2",
            "project_id": "example-project",
            "network": network + "-other",
            "load_balancing_scheme": "INTERNAL",
        },
        {
            "id": "wrong-project",
            "ip_address": "10.0.0.2",
            "project_id": "other",
            "network": network,
            "load_balancing_scheme": "INTERNAL",
        },
        {
            "id": "external-v6",
            "ip_address": "2001:db8:0:0:0:0:0:1",
            "project_id": "example-project",
            "load_balancing_scheme": "EXTERNAL_MANAGED",
        },
        {"id": "unknown", "ip_address": "10.0.0.2", "project_id": "example-project"},
    ]
    # Act
    result = match_load_balancers(resources, rules, "example-project", network)
    # Assert
    assert {r["target_id"] for r in result} == {"internal", "external-v6"}
    assert {
        r["target_id"]
        for r in match_load_balancers(resources, rules, "example-project", None)
    } == {"external-v6"}


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


def test_native_client_initial_token_refresh_and_isolation():
    # Arrange
    cluster = {
        "resource_name": RESOURCE,
        "controlPlaneEndpointsConfig": {
            "dnsEndpointConfig": {
                "endpoint": "example.gke.goog",
                "allowExternalTraffic": True,
            }
        },
    }
    credentials = MagicMock(valid=True, token="first")
    # Act
    with connect(cluster, credentials) as client:
        config = client.core.api_client.configuration
        first = config.auth_settings()["BearerToken"]["value"]
        credentials.token = "second"
        second = config.auth_settings()["BearerToken"]["value"]
        # Assert
        assert first == "Bearer first"
        assert second == "Bearer second"
        assert config.verify_ssl is True
        assert client.core.api_client is client.rbac.api_client
        assert (
            client.tls_diagnostics["kubeconfig_tls_configuration_status"] == "public_ca"
        )


def test_partial_zone_listing_is_not_authoritative():
    # Arrange
    api = MagicMock()
    with patch(
        "cartography.intel.gcp.gke.gcp_api_execute_with_retry",
        return_value={"missingZones": ["us-central1-a"]},
    ):
        # Act and assert
        with pytest.raises(RuntimeError, match="incomplete"):
            get_gke_clusters(api, "example-project")


def test_gke_dataplane_and_endpoint_fields():
    # Arrange
    cluster = {
        "name": "example",
        "selfLink": "https://container.googleapis.com/v1/" + RESOURCE,
        "networkConfig": {"datapathProvider": "ADVANCED_DATAPATH"},
        "controlPlaneEndpointsConfig": {"ipEndpointsConfig": {"enabled": False}},
        "privateClusterConfig": {"publicEndpoint": "192.0.2.1"},
    }
    # Act
    transformed = transform_gke_clusters({"clusters": [cluster]})[0]
    # Assert
    assert transformed["network_policy"] == "DATAPLANE_V2"
    assert transformed["public_ip_endpoint_enabled"] is False
    assert transformed["resource_name"] == RESOURCE


def test_oidc_discovery_reads_raw_json_without_following_jwks_uri():
    # Arrange
    from cartography.intel.kubernetes.clusters import get_service_account_oidc

    cluster = {
        "resource_name": RESOURCE,
        "controlPlaneEndpointsConfig": {
            "dnsEndpointConfig": {
                "endpoint": "example.gke.goog",
                "allowExternalTraffic": True,
            }
        },
    }
    response = MagicMock(
        data=b'{"issuer":"https://issuer.example","jwks_uri":"https://keys.example/jwks","extra":"not-collected"}'
    )
    with connect(cluster, MagicMock(valid=True, token="test-token")) as client:
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


def test_shared_vip_disambiguates_protocol_and_port():
    # Arrange
    resource = {
        "id": "service",
        "load_balancer_ips": ["192.0.2.1"],
        "load_balancer_listeners": ["TCP:443"],
    }
    base = {
        "project_id": "example-project",
        "ip_address": "192.0.2.1",
        "load_balancing_scheme": "EXTERNAL",
    }
    rules = [
        {**base, "id": "https", "ip_protocol": "TCP", "port_range": "443-443"},
        {**base, "id": "http", "ip_protocol": "TCP", "ports": ["80"]},
        {**base, "id": "quic", "ip_protocol": "UDP", "ports": ["443"]},
    ]
    # Act
    result = match_load_balancers([resource], rules, "example-project", None)
    # Assert
    assert result == [{"source_id": "service", "target_id": "https"}]
