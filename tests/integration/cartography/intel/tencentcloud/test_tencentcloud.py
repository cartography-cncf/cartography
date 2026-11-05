from unittest.mock import patch

import pytest
from tencentcloud.common.common_client import CommonClient

import cartography.intel.tencentcloud
from cartography.config import Config
from tests.data.tencentcloud.api import FakeTencentCloudAPI
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = "100000000001"


@pytest.fixture(autouse=True)
def _empty_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _property_by_id(neo4j_session, label: str, prop: str) -> dict:
    """Map each node's id to one property. Use for list properties, which check_nodes()
    cannot put in a set."""
    result = neo4j_session.run(
        f"MATCH (n:{label}) RETURN n.id AS id, n.{prop} AS value"
    )
    return {record["id"]: record["value"] for record in result}


def _sync(neo4j_session, api: FakeTencentCloudAPI, update_tag: int) -> None:
    """Run the module entry point with only the Tencent Cloud network boundary faked.

    No regions are configured, so the sync discovers them through DescribeRegions.
    """
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        tencentcloud_secret_id="AKIDtest",
        tencentcloud_secret_key="test-secret-key",
    )
    with (
        patch.object(
            CommonClient,
            "call_json",
            autospec=True,
            side_effect=api.call_json,
        ),
        patch(
            "cartography.intel.tencentcloud.cos.requests.get",
            side_effect=api.requests_get,
        ),
    ):
        cartography.intel.tencentcloud.start_tencentcloud_ingestion(
            neo4j_session,
            config,
        )


def test_sync_loads_the_account_that_owns_the_key(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "TencentCloudAccount", ["id", "app_id"]) == {
        (ACCOUNT_ID, "1250000000"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {(ACCOUNT_ID,)}


def test_sync_links_cam_users_to_their_groups(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCAMUser",
        ["id", "name", "email", "console_login"],
    ) == {
        ("100000000011", "alice", "alice@example.com", True),
        ("100000000012", "ci-bot", None, False),
    }
    assert check_rels(
        neo4j_session,
        "TencentCloudCAMUser",
        "name",
        "TencentCloudCAMGroup",
        "name",
        "MEMBER_OF",
    ) == {("alice", "admins")}


def test_sync_links_access_keys_to_their_users(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCAMAccessKey",
        ["id", "status", "last_used_date"],
    ) == {("test-access-key-ci-bot", "Active", "2026-10-30")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCAMAccessKey",
        "id",
        "TencentCloudCAMUser",
        "name",
        "OWNED_BY",
    ) == {("test-access-key-ci-bot", "ci-bot")}


def test_sync_records_who_each_role_trusts(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert _property_by_id(
        neo4j_session, "TencentCloudCAMRole", "trusted_services"
    ) == {
        "4611686018427397921": ["cvm.qcloud.com"],
        "4611686018427397922": [],
    }
    assert _property_by_id(
        neo4j_session,
        "TencentCloudCAMRole",
        "trusted_principals",
    ) == {
        "4611686018427397921": [],
        "4611686018427397922": ["qcs::cam::uin/200000000001:root"],
    }


def test_sync_attaches_custom_and_preset_policies_to_principals(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCAMPolicy",
        ["id", "name", "type"],
    ) == {
        ("100000000001:30001", "cos-read-logs", "custom"),
        ("100000000001:1", "AdministratorAccess", "preset"),
        ("100000000001:4", "ReadOnlyAccess", "preset"),
    }
    assert check_rels(
        neo4j_session,
        "TencentCloudCAMUser",
        "name",
        "TencentCloudCAMPolicy",
        "name",
        "POLICY",
    ) == {("ci-bot", "cos-read-logs")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCAMGroup",
        "name",
        "TencentCloudCAMPolicy",
        "name",
        "POLICY",
    ) == {("admins", "AdministratorAccess")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCAMRole",
        "name",
        "TencentCloudCAMPolicy",
        "name",
        "POLICY",
    ) == {
        ("cvm-app-role", "cos-read-logs"),
        ("cross-account-auditor", "ReadOnlyAccess"),
    }


def test_sync_reads_custom_policy_documents(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCAMPolicy",
        ["name", "policy_document"],
    ) == {
        (
            "cos-read-logs",
            '{"version":"2.0","statement":[{"effect":"allow",'
            '"action":["name/cos:GetObject"],"resource":["*"]}]}',
        ),
        ("AdministratorAccess", None),
        ("ReadOnlyAccess", None),
    }


def test_sync_links_subnets_to_their_vpc(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudVPC",
        ["id", "region", "cidr_block"],
    ) == {("vpc-prod0001", "ap-guangzhou", "10.0.0.0/16")}
    assert _property_by_id(
        neo4j_session,
        "TencentCloudVPC",
        "assistant_cidr_blocks",
    ) == {"vpc-prod0001": ["172.16.0.0/16"]}
    assert check_rels(
        neo4j_session,
        "TencentCloudSubnet",
        "id",
        "TencentCloudVPC",
        "id",
        "PART_OF_VPC",
    ) == {("subnet-web00001", "vpc-prod0001")}


def test_sync_loads_security_group_rules_in_evaluation_order(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudSecurityGroupRule",
        ["id", "action", "protocol", "fromport", "toport", "cidr_block"],
    ) == {
        ("sg-web00001/ingress/0", "ACCEPT", "TCP", 443, 443, "0.0.0.0/0"),
        ("sg-web00001/ingress/1", "DROP", "TCP", 22, 22, "0.0.0.0/0"),
        ("sg-web00001/egress/0", "ACCEPT", "ALL", 0, 65535, "0.0.0.0/0"),
    }
    assert check_rels(
        neo4j_session,
        "TencentCloudSecurityGroupRule",
        "id",
        "TencentCloudSecurityGroup",
        "id",
        "MEMBER_OF_SECURITY_GROUP",
    ) == {
        ("sg-web00001/ingress/0", "sg-web00001"),
        ("sg-web00001/ingress/1", "sg-web00001"),
        ("sg-web00001/egress/0", "sg-web00001"),
    }


def test_sync_labels_only_accepting_ingress_rules_as_inbound_permissions(
    neo4j_session,
):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "IpPermissionInbound", ["id"]) == {
        ("sg-web00001/ingress/0",),
    }
    assert check_nodes(neo4j_session, "IpPermissionEgress", ["id"]) == {
        ("sg-web00001/egress/0",),
    }


def test_sync_links_cvm_instance_to_its_network(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCVMInstance",
        ["id", "region", "state", "public_ip_address", "private_ip_address"],
    ) == {("ins-web00001", "ap-guangzhou", "RUNNING", "203.0.113.10", "10.0.1.10")}
    assert _property_by_id(
        neo4j_session,
        "TencentCloudCVMInstance",
        "public_ip_addresses",
    ) == {"ins-web00001": ["203.0.113.10"]}
    assert check_rels(
        neo4j_session,
        "TencentCloudCVMInstance",
        "id",
        "TencentCloudVPC",
        "id",
        "PART_OF_VPC",
    ) == {("ins-web00001", "vpc-prod0001")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCVMInstance",
        "id",
        "TencentCloudSubnet",
        "id",
        "PART_OF_SUBNET",
    ) == {("ins-web00001", "subnet-web00001")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCVMInstance",
        "id",
        "TencentCloudSecurityGroup",
        "id",
        "MEMBER_OF_SECURITY_GROUP",
    ) == {("ins-web00001", "sg-web00001")}


def test_sync_links_cvm_instance_to_its_cam_role(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "TencentCloudCVMInstance",
        "id",
        "TencentCloudCAMRole",
        "name",
        "ASSUMES",
    ) == {("ins-web00001", "cvm-app-role")}


def test_sync_attaches_disks_only_to_their_instance(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCBSDisk",
        ["id", "disk_state", "encrypt", "kms_key_id"],
    ) == {
        ("disk-web00001", "ATTACHED", False, None),
        ("disk-orphan01", "UNATTACHED", True, "kms-key00001"),
    }
    assert check_rels(
        neo4j_session,
        "TencentCloudCBSDisk",
        "id",
        "TencentCloudCVMInstance",
        "id",
        "ATTACHED_TO",
    ) == {("disk-web00001", "ins-web00001")}


def test_sync_links_load_balancer_to_its_cvm_backends(neo4j_session):
    # CLB answers UnsupportedRegion in ap-singapore; the sync skips that region.

    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCLBLoadBalancer",
        ["id", "load_balancer_type", "ip_address"],
    ) == {("lb-web00001", "OPEN", "203.0.113.20")}
    assert _property_by_id(neo4j_session, "TencentCloudCLBLoadBalancer", "vips") == {
        "lb-web00001": ["203.0.113.20"],
    }
    assert check_rels(
        neo4j_session,
        "TencentCloudCLBLoadBalancer",
        "id",
        "TencentCloudCVMInstance",
        "id",
        "EXPOSE",
    ) == {("lb-web00001", "ins-web00001")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCLBLoadBalancer",
        "id",
        "TencentCloudSecurityGroup",
        "id",
        "MEMBER_OF_SECURITY_GROUP",
    ) == {("lb-web00001", "sg-web00001")}
    assert check_rels(
        neo4j_session,
        "TencentCloudCLBLoadBalancer",
        "id",
        "TencentCloudVPC",
        "id",
        "PART_OF_VPC",
    ) == {("lb-web00001", "vpc-prod0001")}


def test_sync_records_cos_bucket_anonymous_access_from_acls(neo4j_session):
    # The locked-down bucket's ACL read is denied, so its exposure is unknown.

    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "TencentCloudCOSBucket",
        ["id", "region", "anonymous_access"],
    ) == {
        ("app-logs-1250000000", "ap-guangzhou", False),
        ("public-assets-1250000000", "ap-singapore", True),
        ("locked-down-1250000000", "ap-guangzhou", None),
    }
    assert _property_by_id(
        neo4j_session,
        "TencentCloudCOSBucket",
        "anonymous_actions",
    ) == {
        "app-logs-1250000000": None,
        "public-assets-1250000000": ["READ"],
        "locked-down-1250000000": None,
    }


def test_sync_connects_every_resource_to_the_account(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    result = neo4j_session.run(
        """
        MATCH (:TencentCloudAccount {id: $account_id})-[:RESOURCE]->(n)
        WITH [label IN labels(n) WHERE label STARTS WITH 'TencentCloud'][0] AS label
        RETURN label, count(*) AS count
        """,
        account_id=ACCOUNT_ID,
    )
    assert {(record["label"], record["count"]) for record in result} == {
        ("TencentCloudCAMUser", 2),
        ("TencentCloudCAMAccessKey", 1),
        ("TencentCloudCAMGroup", 1),
        ("TencentCloudCAMRole", 2),
        ("TencentCloudCAMPolicy", 3),
        ("TencentCloudVPC", 1),
        ("TencentCloudSubnet", 1),
        ("TencentCloudSecurityGroup", 1),
        ("TencentCloudSecurityGroupRule", 3),
        ("TencentCloudCVMInstance", 1),
        ("TencentCloudCBSDisk", 2),
        ("TencentCloudCLBLoadBalancer", 1),
        ("TencentCloudCOSBucket", 3),
    }


def test_sync_projects_resources_into_the_ontology(neo4j_session):
    # Act
    _sync(neo4j_session, FakeTencentCloudAPI(), TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_state", "_ont_public_ip_address"],
    ) == {("ins-web00001", "running", "203.0.113.10")}
    assert check_rels(
        neo4j_session,
        "APIKey",
        "id",
        "UserAccount",
        "name",
        "OWNED_BY",
    ) == {("test-access-key-ci-bot", "ci-bot")}
    assert check_rels(
        neo4j_session,
        "ComputeInstance",
        "id",
        "PermissionRole",
        "name",
        "ASSUMES",
    ) == {("ins-web00001", "cvm-app-role")}


def test_sync_removes_instances_deleted_since_the_last_sync(neo4j_session):
    # Arrange
    api = FakeTencentCloudAPI()
    _sync(neo4j_session, api, TEST_UPDATE_TAG)
    api.instances = []

    # Act
    _sync(neo4j_session, api, TEST_UPDATE_TAG + 1)

    # Assert
    assert check_nodes(neo4j_session, "TencentCloudCVMInstance", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "TencentCloudCBSDisk",
            "id",
            "TencentCloudCVMInstance",
            "id",
            "ATTACHED_TO",
        )
        == set()
    )
