from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.nodes import _scaleway_instance_id
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.nodes import transform_csi_node_ids
from cartography.intel.kubernetes.nodes import transform_nodes
from tests.data.kubernetes.nodes import RAW_CSI_NODES
from tests.data.kubernetes.nodes import RAW_SCALEWAY_NODES
from tests.data.kubernetes.nodes import SCALEWAY_INSTANCE_ID

MODULE = "cartography.intel.kubernetes.nodes"
OTHER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_transform_csi_node_ids_keeps_only_nodes_with_registered_drivers():
    assert transform_csi_node_ids(RAW_CSI_NODES) == {
        "my-scaleway-node": {
            "csi.scaleway.com": f"fr-par-2/{SCALEWAY_INSTANCE_ID}",
        },
    }


@pytest.mark.parametrize(
    "provider_id,csi_node_ids,expected",
    [
        # Kapsule / Scaleway cloud controller manager
        (
            f"scaleway://instance/fr-par-1/{SCALEWAY_INSTANCE_ID}",
            None,
            SCALEWAY_INSTANCE_ID,
        ),
        # Self-managed node: only the CSI driver knows the instance
        (
            "k3s://my-node",
            {"csi.scaleway.com": f"fr-par-2/{SCALEWAY_INSTANCE_ID}"},
            SCALEWAY_INSTANCE_ID,
        ),
        (
            None,
            {"csi.scaleway.com": f"fr-par-2/{SCALEWAY_INSTANCE_ID.upper()}"},
            SCALEWAY_INSTANCE_ID,
        ),
        # providerID wins over the CSI driver
        (
            f"scaleway://instance/fr-par-1/{SCALEWAY_INSTANCE_ID}",
            {"csi.scaleway.com": f"fr-par-1/{OTHER_ID}"},
            SCALEWAY_INSTANCE_ID,
        ),
        # Not a Scaleway Instance
        (f"scaleway://baremetal/fr-par-2/{SCALEWAY_INSTANCE_ID}", None, None),
        ("aws:///us-east-1a/i-0123456789abcdef0", None, None),
        (None, {"ebs.csi.aws.com": "i-0123456789abcdef0"}, None),
        (None, {"csi.scaleway.com": "not-a-server-id"}, None),
        (None, None, None),
    ],
)
def test_scaleway_instance_id(provider_id, csi_node_ids, expected):
    assert _scaleway_instance_id(provider_id, csi_node_ids) == expected


def test_transform_nodes_without_csi_data_leaves_scaleway_fields_empty():
    node = transform_nodes(RAW_SCALEWAY_NODES, "cluster")[0]

    assert node["csi_node_ids"] is None
    assert node["scaleway_instance_id"] is None


@pytest.mark.parametrize("status", [401, 403])
def test_forbidden_csinodes_still_syncs_nodes(status, caplog):
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"

    with (
        patch(f"{MODULE}.get_nodes", return_value=RAW_SCALEWAY_NODES),
        patch(f"{MODULE}.get_csi_nodes", side_effect=ApiException(status=status)),
        patch(f"{MODULE}.load_nodes") as mock_load,
        patch(f"{MODULE}.cleanup") as mock_cleanup,
        caplog.at_level("WARNING"),
    ):
        sync_nodes(MagicMock(), client, 1, {"CLUSTER_ID": "cluster-id"})

    loaded = mock_load.call_args.args[1]
    assert [node["name"] for node in loaded] == ["my-scaleway-node"]
    assert loaded[0]["scaleway_instance_id"] is None
    mock_cleanup.assert_called_once()
    assert any("list csinodes" in r.message for r in caplog.records)


def test_other_csinodes_errors_raise_without_load_or_cleanup():
    client = SimpleNamespace(name="my-cluster", gke_cluster=None)

    with (
        patch(f"{MODULE}.get_nodes", return_value=RAW_SCALEWAY_NODES),
        patch(f"{MODULE}.get_csi_nodes", side_effect=ApiException(status=500)),
        patch(f"{MODULE}.load_nodes") as mock_load,
        patch(f"{MODULE}.cleanup") as mock_cleanup,
        pytest.raises(ApiException),
    ):
        sync_nodes(MagicMock(), client, 1, {"CLUSTER_ID": "cluster-id"})

    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
