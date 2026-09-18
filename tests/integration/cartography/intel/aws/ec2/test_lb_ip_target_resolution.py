"""Synthetic regressions for resolving registered IPs to ENI identities."""

from dataclasses import replace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from cartography.analysis.aws.analysis import AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER_V2
from cartography.analysis.aws.analysis import AWS_ECS_ASSET_EXPOSURE
from cartography.analysis.aws.analysis import AWS_LB_CONTAINER_EXPOSURE
from cartography.client.core.tx import load_matchlinks
from cartography.intel.aws import ecs
from cartography.intel.aws.ec2 import load_balancer_v2s as elbv2
from cartography.intel.aws.ec2.network_interfaces import load_network_data
from cartography.intel.aws.ec2.network_interfaces import (
    transform_network_interface_data,
)
from cartography.intel.aws.ec2.subnets import load_subnets
from cartography.models.aws.ec2.loadbalancerv2 import (
    LoadBalancerV2ToEC2InstanceMatchLink,
)
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import make_target_node_matcher
from cartography.util import run_typed_analysis_job
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

ACCOUNT = "000000000000"
OTHER_ACCOUNT = "111111111111"
REGION = "us-east-1"
IP = "10.0.0.10"
LB = "lb.example.invalid"
TG = "synthetic-target-group"


def _load_workload(session, name, account, vpc, registered=False, region=REGION):
    create_test_account(session, account, 1)
    load_subnets(
        session, [{"SubnetId": f"subnet-{name}", "VpcId": vpc}], region, account, 1
    )
    network = transform_network_interface_data(
        [
            {
                "NetworkInterfaceId": f"eni-{name}",
                "Description": "Synthetic test interface",
                "InterfaceType": "interface",
                "MacAddress": "02:00:00:00:00:01",
                "RequesterManaged": False,
                "SourceDestCheck": True,
                "Status": "in-use",
                "SubnetId": f"subnet-{name}",
                "PrivateIpAddresses": [{"PrivateIpAddress": IP, "Primary": True}],
            }
        ],
        region,
    )
    load_network_data(session, region, account, 1, **network._asdict())
    ecs.load_ecs_services(
        session,
        "cluster",
        [
            {
                "serviceArn": f"service-{name}",
                "serviceName": name,
                "clusterArn": "cluster",
                "loadBalancers": [{"targetGroupArn": TG}] if registered else [],
            }
        ],
        region,
        account,
        1,
    )
    ecs.load_ecs_tasks(
        session,
        "cluster",
        [
            {
                "taskArn": f"task-{name}",
                "clusterArn": "cluster",
                "serviceName": name,
                "networkInterfaceId": f"eni-{name}",
            }
        ],
        region,
        account,
        1,
    )
    ecs.load_ecs_containers(
        session,
        [{"containerArn": f"container-{name}", "taskArn": f"task-{name}"}],
        region,
        account,
        1,
    )


def _analyze(session, tag):
    for job in (
        AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER_V2,
        AWS_ECS_ASSET_EXPOSURE,
        AWS_LB_CONTAINER_EXPOSURE,
    ):
        run_typed_analysis_job(job, session, {"UPDATE_TAG": tag})


@pytest.mark.parametrize(
    "workloads,vpc,expected",
    [
        # Reused IPs in another account, another VPC, and another region.
        (
            [
                ("local", ACCOUNT, "vpc-local", False, REGION),
                ("other-account", OTHER_ACCOUNT, "vpc-other", False, REGION),
                ("other-vpc", ACCOUNT, "vpc-other", False, REGION),
                ("other-region", ACCOUNT, "vpc-local", False, "us-west-2"),
            ],
            "vpc-local",
            {"local"},
        ),
        # Shared VPC: ownership is not a network boundary.
        (
            [("shared", OTHER_ACCOUNT, "vpc-local", False, REGION)],
            "vpc-local",
            {"shared"},
        ),
        # Cross-VPC identity comes from an explicit ECS registration, not IP uniqueness.
        (
            [
                ("remote", ACCOUNT, "vpc-remote", True, REGION),
                ("unrelated", OTHER_ACCOUNT, "vpc-unrelated", False, REGION),
            ],
            "vpc-local",
            {"remote"},
        ),
        (
            [("unresolved", OTHER_ACCOUNT, "vpc-remote", False, REGION)],
            "vpc-local",
            set(),
        ),
        ([("missing-context", ACCOUNT, "vpc-local", False, REGION)], None, set()),
        # Conflicting identity evidence must not produce a fan-out.
        (
            [
                ("first", ACCOUNT, "vpc-local", False, REGION),
                ("second", ACCOUNT, "vpc-local", False, REGION),
            ],
            "vpc-local",
            set(),
        ),
        (
            [
                ("first", ACCOUNT, "vpc-one", True, REGION),
                ("second", ACCOUNT, "vpc-two", True, REGION),
            ],
            "vpc-local",
            set(),
        ),
    ],
)
def test_ip_target_resolution_and_exposure_converge(
    neo4j_session, workloads, vpc, expected
):
    # Arrange: load real schemas and reproduce the previous address-only matcher.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, ACCOUNT, 1)
    data = [
        {
            "DNSName": LB,
            "LoadBalancerName": "synthetic-lb",
            "CreatedTime": "2026-01-01",
            "Type": "network",
            "Scheme": "internet-facing",
            "Listeners": [{"ListenerArn": "synthetic-listener", "Port": 443}],
            "TargetGroups": [
                {
                    "TargetGroupArn": TG,
                    "TargetType": "ip",
                    "VpcId": vpc,
                    "Targets": [IP],
                    "Port": 443,
                    "Protocol": "TCP",
                }
            ],
        }
    ]
    elbv2.load_load_balancer_v2s(neo4j_session, data, REGION, ACCOUNT, 1)
    for workload in workloads:
        _load_workload(neo4j_session, *workload)
    _, _, _, targets = elbv2._transform_load_balancer_v2_data(data)
    old_matcher = replace(
        LoadBalancerV2ToEC2InstanceMatchLink(),
        target_node_label="AWSEC2PrivateIp",
        target_node_matcher=make_target_node_matcher(
            {"private_ip_address": PropertyRef("TargetId")}
        ),
    )
    load_matchlinks(
        neo4j_session,
        old_matcher,
        targets,
        lastupdated=1,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=ACCOUNT,
    )
    _analyze(neo4j_session, 1)
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSECSContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, f"container-{w[0]}") for w in workloads}

    # Act: normal successful IP sync followed by the existing exposure analyses.
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=data):
        elbv2.sync_load_balancer_v2_expose(
            neo4j_session,
            MagicMock(),
            [REGION],
            ACCOUNT,
            2,
            {"AWS_ID": ACCOUNT, "UPDATE_TAG": 2},
        )
    _analyze(neo4j_session, 2)

    # Assert: both the source edges and all derived exposure converge.
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSEC2PrivateIp",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, f"eni-{name}:{IP}") for name in expected}
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSECSContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, f"container-{name}") for name in expected}
    assert check_nodes(
        neo4j_session, "AWSECSContainer", ["id", "exposed_internet"]
    ) == {(f"container-{w[0]}", True if w[0] in expected else None) for w in workloads}
    for record in neo4j_session.run(
        "MATCH (c:AWSECSContainer) RETURN c.id AS id, c.exposed_internet_type AS types"
    ):
        assert record["types"] == (
            ["elbv2"] if record["id"] in {f"container-{n}" for n in expected} else None
        )
    for record in neo4j_session.run(
        "MATCH (:AWSLoadBalancerV2)-[r:EXPOSE]->(:AWSEC2PrivateIp) RETURN r"
    ):
        assert record["r"]["_sub_resource_id"] == ACCOUNT
        assert record["r"]["target_group_arn"] == TG
        assert record["r"]["lastupdated"] == 2


def test_partial_ip_sync_preserves_edges_until_successful_cleanup(neo4j_session):
    # Arrange: legacy wrong edge plus a relationship owned by another sync scope.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, ACCOUNT, 1)
    data = [
        {
            "DNSName": LB,
            "LoadBalancerName": "synthetic-lb",
            "CreatedTime": "2026-01-01",
            "Type": "network",
            "Scheme": "internet-facing",
            "Listeners": [{"ListenerArn": "synthetic-listener", "Port": 443}],
            "TargetGroups": [
                {
                    "TargetGroupArn": TG,
                    "TargetType": "ip",
                    "VpcId": "vpc-local",
                    "Targets": [IP],
                }
            ],
        }
    ]
    elbv2.load_load_balancer_v2s(neo4j_session, data, REGION, ACCOUNT, 1)
    _load_workload(neo4j_session, "remote", OTHER_ACCOUNT, "vpc-remote")
    neo4j_session.run(
        """
        MATCH (lb:AWSLoadBalancerV2 {id: $lb}), (ip:AWSEC2PrivateIp {id: $ip})
        CREATE (lb)-[:EXPOSE {_sub_resource_label: 'AWSAccount', _sub_resource_id: $account, lastupdated: 1}]->(ip)
        CREATE (other:AWSLoadBalancerV2 {id: 'other.example.invalid'})
        CREATE (other)-[:EXPOSE {_sub_resource_label: 'AWSAccount', _sub_resource_id: $other_account, lastupdated: 1}]->(ip)
        """,
        lb=LB,
        ip=f"eni-remote:{IP}",
        account=ACCOUNT,
        other_account=OTHER_ACCOUNT,
    )
    _analyze(neo4j_session, 1)

    # Act: the first region completes, but the second is unavailable.
    with patch.object(
        elbv2,
        "get_loadbalancer_v2_data",
        side_effect=[data, elbv2.ELBV2TransientRegionFailure("synthetic outage")],
    ):
        elbv2.sync_load_balancer_v2_expose(
            neo4j_session,
            MagicMock(),
            [REGION, "us-west-2"],
            ACCOUNT,
            2,
            {"AWS_ID": ACCOUNT, "UPDATE_TAG": 2},
        )
    _analyze(neo4j_session, 2)

    # Assert: preserve last-known state on an incomplete inventory.
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSEC2PrivateIp",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, f"eni-remote:{IP}"), ("other.example.invalid", f"eni-remote:{IP}")}
    assert check_nodes(neo4j_session, "AWSECSContainer", ["exposed_internet"]) == {
        (True,)
    }

    # Act: a later successful inventory removes only the owning scope's stale edge.
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=data):
        elbv2.sync_load_balancer_v2_expose(
            neo4j_session,
            MagicMock(),
            [REGION],
            ACCOUNT,
            3,
            {"AWS_ID": ACCOUNT, "UPDATE_TAG": 3},
        )
    _analyze(neo4j_session, 3)

    # Assert: the foreign edge remains; the wrong ECS exposure and flags are gone.
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSEC2PrivateIp",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("other.example.invalid", f"eni-remote:{IP}")}
    assert (
        check_rels(
            neo4j_session,
            "AWSLoadBalancerV2",
            "id",
            "AWSECSContainer",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_nodes(
        neo4j_session, "AWSECSContainer", ["exposed_internet", "exposed_internet_type"]
    ) == {(None, None)}


def test_ecs_regional_failure_preserves_cross_vpc_exposure(neo4j_session):
    # Arrange: a valid cross-VPC target and an unrelated account sharing its IP.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, ACCOUNT, 1)
    data = [
        {
            "DNSName": LB,
            "LoadBalancerName": "synthetic-lb",
            "CreatedTime": "2026-01-01",
            "Type": "network",
            "Scheme": "internet-facing",
            "Listeners": [{"ListenerArn": "synthetic-listener", "Port": 443}],
            "TargetGroups": [
                {
                    "TargetGroupArn": TG,
                    "TargetType": "ip",
                    "VpcId": "vpc-local",
                    "Targets": [IP],
                }
            ],
        }
    ]
    elbv2.load_load_balancer_v2s(neo4j_session, data, REGION, ACCOUNT, 1)
    _load_workload(neo4j_session, "remote", ACCOUNT, "vpc-remote", registered=True)
    _load_workload(neo4j_session, "other", OTHER_ACCOUNT, "vpc-other")
    _, _, _, targets = elbv2._transform_load_balancer_v2_data(data)
    elbv2._load_load_balancer_v2_ip_targets(neo4j_session, targets, ACCOUNT, 1)
    _analyze(neo4j_session, 1)

    failed_client = MagicMock()
    healthy_client = MagicMock()
    healthy_client.get_paginator.return_value.paginate.return_value = [{}]
    healthy_client.describe_clusters.return_value = {"clusters": []}
    failed_client.describe_clusters.return_value = {
        "clusters": [{"clusterArn": "cluster"}]
    }

    def paginator(operation):
        result = MagicMock()
        if operation == "list_services":
            result.paginate.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "AccessDeniedException",
                        "Message": "Synthetic denial",
                    }
                },
                operation,
            )
        else:
            result.paginate.return_value = [{"clusterArns": ["cluster"]}]
        return result

    failed_client.get_paginator.side_effect = paginator
    session = MagicMock()
    session.client.side_effect = lambda service, **kwargs: (
        failed_client if kwargs["region_name"] == REGION else healthy_client
    )

    # Act: ECS partially succeeds, then ELBV2 and derived exposure run normally.
    ecs.sync(
        neo4j_session,
        session,
        [REGION, "us-west-2"],
        ACCOUNT,
        2,
        {"AWS_ID": ACCOUNT, "UPDATE_TAG": 2},
    )
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=data):
        elbv2.sync_load_balancer_v2_expose(
            neo4j_session,
            session,
            [REGION],
            ACCOUNT,
            2,
            {"AWS_ID": ACCOUNT, "UPDATE_TAG": 2},
        )
    _analyze(neo4j_session, 2)

    # Assert: continue other regions without erasing prior identity or exposure.
    healthy_client.get_paginator.assert_called_with("list_clusters")
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSEC2PrivateIp",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, f"eni-remote:{IP}")}
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "AWSECSContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {(LB, "container-remote")}
    assert check_nodes(
        neo4j_session, "AWSECSContainer", ["id", "exposed_internet"]
    ) == {
        ("container-remote", True),
        ("container-other", None),
    }

    # Act: successful empty ECS inventory allows normal cleanup on the next sync.
    session.client.side_effect = None
    session.client.return_value = healthy_client
    ecs.sync(
        neo4j_session,
        session,
        [REGION, "us-west-2"],
        ACCOUNT,
        3,
        {"AWS_ID": ACCOUNT, "UPDATE_TAG": 3},
    )
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=data):
        elbv2.sync_load_balancer_v2_expose(
            neo4j_session,
            session,
            [REGION],
            ACCOUNT,
            3,
            {"AWS_ID": ACCOUNT, "UPDATE_TAG": 3},
        )
    _analyze(neo4j_session, 3)

    # Assert: stale exposure converges and the other account survives cleanup.
    assert (
        check_rels(
            neo4j_session,
            "AWSLoadBalancerV2",
            "id",
            "AWSEC2PrivateIp",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "AWSLoadBalancerV2",
            "id",
            "AWSECSContainer",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_nodes(
        neo4j_session, "AWSECSContainer", ["id", "exposed_internet"]
    ) == {
        ("container-other", None),
    }
