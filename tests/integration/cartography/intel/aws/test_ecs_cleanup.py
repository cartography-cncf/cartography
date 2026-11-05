"""Transient failures preserve inventory; access-denial policy is unchanged."""

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ReadTimeoutError

from cartography.client.core.tx import load
from cartography.intel.aws import ecs
from cartography.models.aws.ec2.loadbalancerv2 import ELBV2TargetGroupSchema
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

ACCOUNT = "000000000000"
OTHER_ACCOUNT = "111111111111"
REGION = "us-east-1"


@pytest.mark.parametrize("operation", ["list_clusters", "list_services"])
@pytest.mark.parametrize("failure", ["timeout", "server_error", "access_denied"])
def test_ecs_cleanup_after_regional_failure(neo4j_session, operation, failure):
    # Arrange: independent workloads in two regions and a separate account.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    for name, account, region in (
        ("selected", ACCOUNT, REGION),
        ("healthy", ACCOUNT, "us-west-2"),
        ("other", OTHER_ACCOUNT, REGION),
    ):
        create_test_account(neo4j_session, account, 1)
        load(
            neo4j_session,
            ELBV2TargetGroupSchema(),
            [{"TargetGroupArn": f"target-group-{name}"}],
            Region=region,
            AWS_ID=account,
            lastupdated=1,
        )
        ecs.load_ecs_services(
            neo4j_session,
            "cluster",
            [
                {
                    "serviceArn": f"service-{name}",
                    "serviceName": name,
                    "clusterArn": "cluster",
                    "loadBalancers": [{"targetGroupArn": f"target-group-{name}"}],
                }
            ],
            region,
            account,
            1,
        )
        ecs.load_ecs_tasks(
            neo4j_session,
            "cluster",
            [{"taskArn": f"task-{name}", "clusterArn": "cluster", "serviceName": name}],
            region,
            account,
            1,
        )
        ecs.load_ecs_containers(
            neo4j_session,
            [{"containerArn": f"container-{name}", "taskArn": f"task-{name}"}],
            region,
            account,
            1,
        )

    failed_client = MagicMock()
    healthy_client = MagicMock()
    healthy_pages = {
        "list_clusters": {"clusterArns": ["cluster-healthy"]},
        "list_container_instances": {"containerInstanceArns": []},
        "list_tasks": {"taskArns": []},
        "list_services": {"serviceArns": []},
    }
    healthy_paginators = {}
    for api_name, page in healthy_pages.items():
        healthy_paginators[api_name] = MagicMock()
        healthy_paginators[api_name].paginate.return_value = [page]
    healthy_client.get_paginator.side_effect = healthy_paginators.__getitem__
    healthy_client.describe_clusters.return_value = {
        "clusters": [{"clusterArn": "cluster-healthy"}]
    }
    failed_client.describe_clusters.return_value = {
        "clusters": [{"clusterArn": "cluster"}]
    }

    def paginator(api_operation):
        result = MagicMock()
        if api_operation == operation:
            result.paginate.side_effect = (
                ReadTimeoutError(endpoint_url="https://ecs.example.invalid")
                if failure == "timeout"
                else ClientError(
                    {
                        "Error": {
                            "Code": (
                                "InternalServerErrorException"
                                if failure == "server_error"
                                else "AccessDeniedException"
                            ),
                            "Message": "Synthetic denial",
                        }
                    },
                    operation,
                )
            )
        else:
            result.paginate.return_value = [{"clusterArns": ["cluster"]}]
        return result

    failed_client.get_paginator.side_effect = paginator
    provider = MagicMock()
    provider.client.side_effect = lambda service, **kwargs: (
        failed_client if kwargs["region_name"] == REGION else healthy_client
    )

    # Act: one region fails while another finishes successfully.
    ecs.sync(
        neo4j_session,
        provider,
        [REGION, "us-west-2"],
        ACCOUNT,
        2,
        {"AWS_ID": ACCOUNT, "UPDATE_TAG": 2},
    )

    # Assert: transient failures preserve data; denied scopes keep existing cleanup
    # behavior, so a permanently denied region cannot block account cleanup forever.
    expected = (
        {"selected", "healthy", "other"} if failure != "access_denied" else {"other"}
    )
    assert ("cluster-healthy", "us-west-2", 2) in check_nodes(
        neo4j_session, "AWSECSCluster", ["id", "region", "lastupdated"]
    )
    assert (ACCOUNT, "cluster-healthy") in check_rels(
        neo4j_session, "AWSAccount", "id", "AWSECSCluster", "id", "RESOURCE"
    )
    for label, prefix in (
        ("AWSECSService", "service"),
        ("AWSECSTask", "task"),
        ("AWSECSContainer", "container"),
    ):
        assert check_nodes(neo4j_session, label, ["id"]) == {
            (f"{prefix}-{name}",) for name in expected
        }
    assert check_rels(
        neo4j_session,
        "AWSELBV2TargetGroup",
        "id",
        "AWSECSService",
        "id",
        "TARGETS",
        rel_direction_right=True,
    ) == {(f"target-group-{name}", f"service-{name}") for name in expected}
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSService",
        "id",
        "WORKLOAD_PARENT",
        rel_direction_right=True,
    ) == {(f"task-{name}", f"service-{name}") for name in expected}
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {(f"task-{name}", f"container-{name}") for name in expected}

    # Act: a later successful empty inventory permits normal account cleanup.
    healthy_paginators["list_clusters"].paginate.return_value = [{"clusterArns": []}]
    healthy_client.describe_clusters.return_value = {"clusters": []}
    provider.client.side_effect = None
    provider.client.return_value = healthy_client
    ecs.sync(
        neo4j_session,
        provider,
        [REGION, "us-west-2"],
        ACCOUNT,
        3,
        {"AWS_ID": ACCOUNT, "UPDATE_TAG": 3},
    )

    # Assert: stale data is removed only from the selected account.
    for label, prefix in (
        ("AWSECSService", "service"),
        ("AWSECSTask", "task"),
        ("AWSECSContainer", "container"),
    ):
        assert check_nodes(neo4j_session, label, ["id"]) == {(f"{prefix}-other",)}
    assert check_rels(
        neo4j_session,
        "AWSELBV2TargetGroup",
        "id",
        "AWSECSService",
        "id",
        "TARGETS",
        rel_direction_right=True,
    ) == {
        ("target-group-other", "service-other"),
    }
