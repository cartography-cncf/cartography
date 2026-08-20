from unittest.mock import patch

import cartography.intel.runpod
import cartography.intel.runpod.catalog
import cartography.intel.runpod.clusters
import cartography.intel.runpod.network_volumes
import cartography.intel.runpod.pods
import cartography.intel.runpod.registries
import cartography.intel.runpod.serverless
import cartography.intel.runpod.sshkeys
import cartography.intel.runpod.templates
from cartography.config import Config
from tests.data.runpod.data import CLUSTERS_RESPONSE
from tests.data.runpod.data import DATA_CENTERS_RESPONSE
from tests.data.runpod.data import NETWORK_VOLUMES_RESPONSE
from tests.data.runpod.data import PODS_RESPONSE
from tests.data.runpod.data import REGISTRIES_RESPONSE
from tests.data.runpod.data import SERVERLESS_RESPONSE
from tests.data.runpod.data import SSH_KEYS_RESPONSE
from tests.data.runpod.data import TEMPLATES_RESPONSE
from tests.data.runpod.data import TEST_ACCOUNT_ID
from tests.data.runpod.data import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _config(update_tag: int = TEST_UPDATE_TAG) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        runpod_api_key="test-api-key",
        runpod_account_id=TEST_ACCOUNT_ID,
        update_tag=update_tag,
    )


RUNPOD_PATCHES = [
    (cartography.intel.runpod.sshkeys, "get", SSH_KEYS_RESPONSE),
    (cartography.intel.runpod.registries, "get", REGISTRIES_RESPONSE),
    (cartography.intel.runpod.network_volumes, "get", NETWORK_VOLUMES_RESPONSE),
    (cartography.intel.runpod.templates, "get", TEMPLATES_RESPONSE),
    (cartography.intel.runpod.pods, "get", PODS_RESPONSE),
    (cartography.intel.runpod.serverless, "get", SERVERLESS_RESPONSE),
    (cartography.intel.runpod.clusters, "get", CLUSTERS_RESPONSE),
    (cartography.intel.runpod.catalog, "get", DATA_CENTERS_RESPONSE),
]


def _run_with_patches(neo4j_session, patches, update_tag: int = TEST_UPDATE_TAG):
    patchers = [
        patch.object(module, attr, return_value=value)
        for module, attr, value in patches
    ]
    for patcher in patchers:
        patcher.start()
    try:
        cartography.intel.runpod.start_runpod_ingestion(
            neo4j_session, _config(update_tag)
        )
    finally:
        for patcher in reversed(patchers):
            patcher.stop()


def test_start_runpod_ingestion(neo4j_session):
    _run_with_patches(neo4j_session, RUNPOD_PATCHES)

    assert check_nodes(neo4j_session, "RunPodAccount", ["id"]) == {
        (TEST_ACCOUNT_ID,),
    }
    assert check_nodes(neo4j_session, "RunPodPod", ["id", "name", "status"]) == {
        ("pod-1", "training-pod", "RUNNING"),
    }
    assert check_nodes(
        neo4j_session, "RunPodServerlessEndpoint", ["id", "name", "workers_max"]
    ) == {
        ("endpoint-1", "inference", 3),
    }
    assert check_nodes(
        neo4j_session, "RunPodNetworkVolume", ["id", "name", "size"]
    ) == {
        ("volume-1", "models", 100),
    }
    assert check_nodes(
        neo4j_session, "RunPodTemplate", ["id", "name", "start_ssh"]
    ) == {
        ("template-1", "pytorch-ssh", True),
    }
    assert check_nodes(neo4j_session, "RunPodRegistryCredential", ["id", "name"]) == {
        ("registry-1", "private-registry"),
    }
    assert check_nodes(neo4j_session, "RunPodCluster", ["id", "name", "pod_count"]) == {
        ("cluster-1", "training-cluster", 4),
    }
    assert check_nodes(neo4j_session, "RunPodSSHKey", ["id", "fingerprint"]) == {
        (
            "SHA256:A5BYxvLAy0ksUzsKTRTvd8wPeKvMztUofYShogEc+4E",
            "SHA256:A5BYxvLAy0ksUzsKTRTvd8wPeKvMztUofYShogEc+4E",
        ),
    }
    assert check_nodes(neo4j_session, "RunPodDataCenter", ["id", "country_code"]) == {
        ("EU-SE-1", "SE"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name", "_ont_source"]) == {
        (TEST_ACCOUNT_ID, TEST_ACCOUNT_ID, "runpod"),
    }
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_name", "_ont_state", "_ont_region", "_ont_type", "_ont_source"],
    ) == {
        ("pod-1", "training-pod", "running", "EU-SE-1", "NVIDIA A100", "runpod"),
    }
    assert check_nodes(
        neo4j_session,
        "ComputeCluster",
        ["id", "_ont_name", "_ont_source"],
    ) == {
        ("cluster-1", "training-cluster", "runpod"),
    }
    assert check_nodes(
        neo4j_session,
        "FileStorage",
        ["id", "_ont_name", "_ont_location", "_ont_source"],
    ) == {
        ("volume-1", "models", "EU-SE-1", "runpod"),
    }
    assert check_nodes(neo4j_session, "Secret", ["id", "_ont_name", "_ont_source"]) == {
        ("registry-1", "private-registry", "runpod"),
    }
    assert check_nodes(
        neo4j_session, "ComputeService", ["id", "_ont_name", "_ont_source"]
    ) == {
        ("endpoint-1", "inference", "runpod"),
    }

    assert check_rels(
        neo4j_session,
        "RunPodAccount",
        "id",
        "RunPodPod",
        "id",
        "RESOURCE",
    ) == {(TEST_ACCOUNT_ID, "pod-1")}
    assert check_rels(
        neo4j_session,
        "RunPodPod",
        "id",
        "RunPodNetworkVolume",
        "id",
        "USES_VOLUME",
    ) == {("pod-1", "volume-1")}
    assert check_rels(
        neo4j_session,
        "RunPodPod",
        "id",
        "RunPodTemplate",
        "id",
        "USES_TEMPLATE",
    ) == {("pod-1", "template-1")}
    assert check_rels(
        neo4j_session,
        "RunPodPod",
        "id",
        "RunPodRegistryCredential",
        "id",
        "USES_REGISTRY_CREDENTIAL",
    ) == {("pod-1", "registry-1")}
    assert check_rels(
        neo4j_session,
        "RunPodPod",
        "id",
        "RunPodRegistryCredential",
        "id",
        "USES_SECRET",
    ) == {("pod-1", "registry-1")}
    assert check_rels(
        neo4j_session,
        "RunPodPod",
        "id",
        "RunPodDataCenter",
        "id",
        "RUNS_IN",
    ) == {("pod-1", "EU-SE-1")}
    assert check_rels(
        neo4j_session,
        "RunPodTemplate",
        "id",
        "RunPodRegistryCredential",
        "id",
        "USES_REGISTRY_CREDENTIAL",
    ) == {("template-1", "registry-1")}
    assert check_rels(
        neo4j_session,
        "RunPodNetworkVolume",
        "id",
        "RunPodDataCenter",
        "id",
        "LOCATED_IN",
    ) == {("volume-1", "EU-SE-1")}
    assert check_rels(
        neo4j_session,
        "RunPodServerlessEndpoint",
        "id",
        "RunPodNetworkVolume",
        "id",
        "USES_VOLUME",
    ) == {("endpoint-1", "volume-1")}
    assert check_rels(
        neo4j_session,
        "RunPodServerlessEndpoint",
        "id",
        "RunPodDataCenter",
        "id",
        "RUNS_IN",
    ) == {("endpoint-1", "EU-SE-1")}
    assert check_rels(
        neo4j_session,
        "RunPodCluster",
        "id",
        "RunPodPod",
        "id",
        "HAS_PRIMARY",
    ) == {("cluster-1", "pod-1")}
    assert check_rels(
        neo4j_session,
        "RunPodCluster",
        "id",
        "RunPodTemplate",
        "id",
        "USES_TEMPLATE",
    ) == {("cluster-1", "template-1")}
    assert check_rels(
        neo4j_session,
        "RunPodCluster",
        "id",
        "RunPodDataCenter",
        "id",
        "RUNS_IN",
    ) == {("cluster-1", "EU-SE-1")}


def test_runpod_cleanup_removes_stale_resources(neo4j_session):
    _run_with_patches(neo4j_session, RUNPOD_PATCHES)
    empty_patches = [(module, attr, []) for module, attr, _ in RUNPOD_PATCHES]
    _run_with_patches(neo4j_session, empty_patches, TEST_UPDATE_TAG + 1)

    assert check_nodes(neo4j_session, "RunPodAccount", ["id"]) == {
        (TEST_ACCOUNT_ID,),
    }
    assert check_nodes(neo4j_session, "RunPodPod", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodServerlessEndpoint", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodNetworkVolume", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodTemplate", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodRegistryCredential", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodCluster", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodSSHKey", ["id"]) == set()
    assert check_nodes(neo4j_session, "RunPodDataCenter", ["id"]) == set()
