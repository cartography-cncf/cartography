from cartography.intel.tenable.assets import transform
from cartography.intel.tenable.assets import transform_aws
from cartography.intel.tenable.assets import transform_azure
from cartography.intel.tenable.assets import transform_gcp
from cartography.intel.tenable.assets import transform_networks
from cartography.intel.tenable.assets import transform_sources
from cartography.intel.tenable.assets import transform_tags
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import AWS_EC2_INSTANCE_ID_1
from tests.data.tenable.assets import AZURE_VM_ID_2
from tests.data.tenable.assets import NETWORK_ID
from tests.data.tenable.assets import SCOPED_ASSET_ID_1
from tests.data.tenable.assets import SCOPED_AWS_EC2_INSTANCE_ID_1
from tests.data.tenable.assets import SCOPED_AZURE_VM_ID_2
from tests.data.tenable.assets import SCOPED_NETWORK_ID
from tests.data.tenable.assets import SCOPED_TAG_ID_1
from tests.data.tenable.assets import TAG_ID_1
from tests.data.tenable.assets import tenable_id
from tests.data.tenable.assets import TENABLE_TENANT_ID

# ---------------------------------------------------------------------------
# transform()
# ---------------------------------------------------------------------------


def test_transform_maps_all_fields():
    result = transform(ASSETS_DATA, TENABLE_TENANT_ID)

    assert len(result) == 2

    asset1 = result[0]
    assert asset1["id"] == SCOPED_ASSET_ID_1
    assert asset1["asset_uuid"] == ASSET_ID_1
    assert asset1["has_agent"] is True
    assert asset1["has_plugin_results"] is True
    assert asset1["is_licensed"] is True
    assert asset1["is_public"] is False
    assert asset1["types"] == ["host", "cloud"]
    assert asset1["system_types"] == ["aws-ec2-instance"]
    assert asset1["operating_systems"] == ["Oracle Linux 8.4"]
    assert asset1["serial_number"] is None
    assert asset1["tenable_agent_days_since_active"] == 2
    # Timestamps
    assert asset1["created_at_timestamps"] == "2024-09-24T15:01:25.000Z"
    assert asset1["updated_at_timestamps"] == "2024-12-16T09:45:50.000Z"
    assert asset1["first_seen_timestamps"] == "2024-09-24T15:01:25.000Z"
    assert asset1["last_seen_timestamps"] == "2024-12-16T09:45:50.000Z"
    # Scan
    assert asset1["first_scan_time"] == "2024-09-24T15:01:25.000Z"
    assert asset1["last_scan_time"] == "2024-12-16T09:45:50.000Z"
    assert asset1["last_scan_id"] == "scan-id-1"
    # Network
    assert asset1["network_id"] == NETWORK_ID
    assert asset1["network_node_id"] == SCOPED_NETWORK_ID
    assert asset1["fqdn"] == "server1.example.com"
    assert asset1["fqdns"] == ["server1.example.com"]
    assert asset1["ipv4s"] == ["192.168.1.10", "172.26.114.163"]
    assert asset1["hostnames"] == ["server1"]
    # Cloud identifier
    assert asset1["aws_ec2_instance_id"] == AWS_EC2_INSTANCE_ID_1
    assert asset1["aws_node_id"] == SCOPED_AWS_EC2_INSTANCE_ID_1
    assert asset1["azure_vm_id"] is None
    assert asset1["azure_node_id"] is None
    assert asset1["gcp_instance_id"] is None
    assert asset1["gcp_node_id"] is None
    # Ratings
    assert asset1["acr_score"] == 5
    assert asset1["aes_score"] == 600


def test_transform_fqdn_is_first_of_fqdns():
    raw = [
        {
            "id": "asset-x",
            "network": {"fqdns": ["first.example.com", "second.example.com"]},
        }
    ]
    result = transform(raw, TENABLE_TENANT_ID)
    assert result[0]["fqdn"] == "first.example.com"


def test_transform_fqdn_none_when_fqdns_empty():
    raw = [{"id": "asset-x", "network": {"fqdns": []}}]
    result = transform(raw, TENABLE_TENANT_ID)
    assert result[0]["fqdn"] is None


def test_transform_list_fields_default_to_empty_list():
    raw = [{"id": "asset-x"}]
    result = transform(raw, TENABLE_TENANT_ID)
    asset = result[0]
    assert asset["types"] == []
    assert asset["system_types"] == []
    assert asset["operating_systems"] == []
    assert asset["fqdns"] == []
    assert asset["ipv4s"] == []
    assert asset["ipv6s"] == []
    assert asset["hostnames"] == []
    assert asset["mac_addresses"] == []


def test_transform_optional_scalars_default_to_none():
    raw = [{"id": "asset-x"}]
    result = transform(raw, TENABLE_TENANT_ID)
    asset = result[0]
    assert asset["has_agent"] is None
    assert asset["serial_number"] is None
    assert asset["network_id"] is None
    assert asset["aws_ec2_instance_id"] is None
    assert asset["azure_vm_id"] is None
    assert asset["gcp_instance_id"] is None
    assert asset["acr_score"] is None
    assert asset["aes_score"] is None


def test_transform_empty_input():
    assert transform([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_networks()
# ---------------------------------------------------------------------------


def test_transform_networks_basic():
    result = transform_networks(ASSETS_DATA, TENABLE_TENANT_ID)
    # Both assets share NETWORK_ID — only one network node produced
    assert len(result) == 1
    assert result[0] == {
        "id": SCOPED_NETWORK_ID,
        "network_id": NETWORK_ID,
        "name": "Default",
    }


def test_transform_networks_deduplicates():
    raw = [
        {"id": "a1", "network": {"network_id": "net-1", "network_name": "Net1"}},
        {"id": "a2", "network": {"network_id": "net-1", "network_name": "Net1"}},
        {"id": "a3", "network": {"network_id": "net-2", "network_name": "Net2"}},
    ]
    result = transform_networks(raw, TENABLE_TENANT_ID)
    ids = [r["id"] for r in result]
    assert ids == [tenable_id("net-1"), tenable_id("net-2")]


def test_transform_networks_skips_missing_network_id():
    raw = [
        {"id": "a1", "network": {}},
        {"id": "a2"},
        {"id": "a3", "network": {"network_id": "net-1", "network_name": "N"}},
    ]
    result = transform_networks(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("net-1")
    assert result[0]["network_id"] == "net-1"


def test_transform_networks_empty_input():
    assert transform_networks([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_sources()
# ---------------------------------------------------------------------------


def test_transform_sources_basic():
    result = transform_sources(ASSETS_DATA, TENABLE_TENANT_ID)
    # ASSET_ID_1 has one source, ASSET_ID_2 has one source
    assert len(result) == 2

    src1 = next(r for r in result if r["asset_id"] == SCOPED_ASSET_ID_1)
    assert src1["id"] == tenable_id(f"{ASSET_ID_1}::NESSUS_AGENT")
    assert src1["name"] == "NESSUS_AGENT"
    assert src1["source_first_seen"] == "2024-09-24T15:01:25.000Z"
    assert src1["source_last_seen"] == "2024-12-16T09:45:50.000Z"

    src2 = next(r for r in result if r["asset_id"] == tenable_id(ASSET_ID_2))
    assert src2["id"] == tenable_id(f"{ASSET_ID_2}::NESSUS_SCAN")
    assert src2["name"] == "NESSUS_SCAN"


def test_transform_sources_no_sources():
    raw = [{"id": "asset-x"}]
    assert transform_sources(raw, TENABLE_TENANT_ID) == []


def test_transform_sources_multiple_per_asset():
    raw = [
        {
            "id": "asset-x",
            "sources": [
                {
                    "name": "SRC_A",
                    "first_seen": "2024-01-01",
                    "last_seen": "2024-06-01",
                },
                {
                    "name": "SRC_B",
                    "first_seen": "2024-02-01",
                    "last_seen": "2024-07-01",
                },
            ],
        }
    ]
    result = transform_sources(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    ids = {r["id"] for r in result}
    assert ids == {tenable_id("asset-x::SRC_A"), tenable_id("asset-x::SRC_B")}


# ---------------------------------------------------------------------------
# transform_tags()
# ---------------------------------------------------------------------------


def test_transform_tags_basic():
    result = transform_tags(ASSETS_DATA, TENABLE_TENANT_ID)
    # Only ASSET_ID_1 has a tag
    assert len(result) == 1
    tag = result[0]
    assert tag["id"] == SCOPED_TAG_ID_1
    assert tag["tag_uuid"] == TAG_ID_1
    assert tag["tag_key"] == "Environment"
    assert tag["tag_value"] == "Production"
    assert tag["added_by"] == "admin@example.com"
    assert tag["added_at"] == "2024-10-01T00:00:00.000Z"
    assert tag["asset_id"] == SCOPED_ASSET_ID_1


def test_transform_tags_no_tags():
    raw = [{"id": "asset-x", "tags": []}]
    assert transform_tags(raw, TENABLE_TENANT_ID) == []


def test_transform_tags_multiple_per_asset():
    raw = [
        {
            "id": "asset-x",
            "tags": [
                {
                    "uuid": "t1",
                    "key": "Env",
                    "value": "Prod",
                    "added_by": None,
                    "added_at": None,
                },
                {
                    "uuid": "t2",
                    "key": "Team",
                    "value": "Ops",
                    "added_by": None,
                    "added_at": None,
                },
            ],
        }
    ]
    result = transform_tags(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {tenable_id("t1"), tenable_id("t2")}
    assert all(r["asset_id"] == tenable_id("asset-x") for r in result)


# ---------------------------------------------------------------------------
# transform_aws()
# ---------------------------------------------------------------------------


def test_transform_aws_basic():
    result = transform_aws(ASSETS_DATA, TENABLE_TENANT_ID)
    assert len(result) == 1
    aws = result[0]
    assert aws["id"] == SCOPED_AWS_EC2_INSTANCE_ID_1
    assert aws["ec2_instance_id"] == AWS_EC2_INSTANCE_ID_1
    assert aws["owner_id"] == "123456789012"
    assert aws["region"] == "us-east-1"
    assert aws["availability_zone"] == "us-east-1a"
    assert aws["vpc_id"] == "vpc-12345678"
    assert aws["subnet_id"] == "subnet-12345678"
    assert aws["ec2_instance_type"] == "t3.medium"
    assert aws["ec2_instance_state_name"] == "running"
    assert aws["ec2_instance_group_name"] == "launch-wizard-1"
    assert aws["ec2_name"] == "test-server-1"
    assert aws["ec2_instance_ami_id"] == "ami-0abcdef1234567890"


def test_transform_aws_deduplicates():
    raw = [
        {
            "id": "a1",
            "cloud": {"aws": {"ec2_instance_id": "i-111", "region": "us-east-1"}},
        },
        {
            "id": "a2",
            "cloud": {"aws": {"ec2_instance_id": "i-111", "region": "us-east-1"}},
        },
        {
            "id": "a3",
            "cloud": {"aws": {"ec2_instance_id": "i-222", "region": "us-west-2"}},
        },
    ]
    result = transform_aws(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {tenable_id("i-111"), tenable_id("i-222")}


def test_transform_aws_skips_missing_instance_id():
    raw = [
        {"id": "a1", "cloud": {"aws": {}}},
        {"id": "a2"},
        {"id": "a3", "cloud": {"aws": {"ec2_instance_id": "i-999"}}},
    ]
    result = transform_aws(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("i-999")
    assert result[0]["ec2_instance_id"] == "i-999"


def test_transform_aws_empty_input():
    assert transform_aws([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_azure()
# ---------------------------------------------------------------------------


def test_transform_azure_basic():
    result = transform_azure(ASSETS_DATA, TENABLE_TENANT_ID)
    assert len(result) == 1
    az = result[0]
    assert az["id"] == SCOPED_AZURE_VM_ID_2
    assert az["vm_id"] == AZURE_VM_ID_2
    assert az["resource_id"] == (
        "/subscriptions/sub-123/resourceGroups/rg-prod/"
        "providers/Microsoft.Compute/virtualMachines/test-vm"
    )


def test_transform_azure_deduplicates():
    raw = [
        {"id": "a1", "cloud": {"azure": {"vm_id": "vm-aaa", "resource_id": "/res/1"}}},
        {"id": "a2", "cloud": {"azure": {"vm_id": "vm-aaa", "resource_id": "/res/1"}}},
        {"id": "a3", "cloud": {"azure": {"vm_id": "vm-bbb", "resource_id": "/res/2"}}},
    ]
    result = transform_azure(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {
        tenable_id("vm-aaa"),
        tenable_id("vm-bbb"),
    }


def test_transform_azure_skips_missing_vm_id():
    raw = [
        {"id": "a1", "cloud": {"azure": {}}},
        {"id": "a2", "cloud": {"azure": {"vm_id": "vm-xyz"}}},
    ]
    result = transform_azure(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("vm-xyz")
    assert result[0]["vm_id"] == "vm-xyz"


def test_transform_azure_empty_input():
    assert transform_azure([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_gcp()
# ---------------------------------------------------------------------------


def test_transform_gcp_basic():
    raw = [
        {
            "id": "asset-g",
            "cloud": {
                "gcp": {
                    "instance_id": "gcp-inst-1",
                    "project_id": "my-project",
                    "zone": "us-central1-a",
                }
            },
        }
    ]
    result = transform_gcp(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    gcp = result[0]
    assert gcp["id"] == tenable_id("gcp-inst-1")
    assert gcp["instance_id"] == "gcp-inst-1"
    assert gcp["project_id"] == "my-project"
    assert gcp["zone"] == "us-central1-a"


def test_transform_gcp_deduplicates():
    raw = [
        {
            "id": "a1",
            "cloud": {
                "gcp": {"instance_id": "inst-1", "project_id": "p1", "zone": "z1"}
            },
        },
        {
            "id": "a2",
            "cloud": {
                "gcp": {"instance_id": "inst-1", "project_id": "p1", "zone": "z1"}
            },
        },
        {
            "id": "a3",
            "cloud": {
                "gcp": {"instance_id": "inst-2", "project_id": "p2", "zone": "z2"}
            },
        },
    ]
    result = transform_gcp(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {
        tenable_id("inst-1"),
        tenable_id("inst-2"),
    }


def test_transform_gcp_skips_missing_instance_id():
    raw = [
        {"id": "a1", "cloud": {"gcp": {}}},
        {"id": "a2", "cloud": {"gcp": {"instance_id": "inst-ok"}}},
    ]
    result = transform_gcp(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("inst-ok")
    assert result[0]["instance_id"] == "inst-ok"


def test_transform_gcp_not_present_in_assets_data():
    # ASSETS_DATA has no GCP assets
    assert transform_gcp(ASSETS_DATA, TENABLE_TENANT_ID) == []
