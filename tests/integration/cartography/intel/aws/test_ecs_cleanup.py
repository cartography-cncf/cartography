"""Incomplete ECS collection must not be treated as successful emptiness."""

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


@pytest.mark.parametrize("failure", ["list_clusters", "list_services", "timeout"])
def test_incomplete_ecs_inventory_preserves_state_until_success(neo4j_session, failure):
    # Arrange: two accounts with independent ECS workloads and target registrations.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    for name, account in (("selected", ACCOUNT), ("other", OTHER_ACCOUNT)):
        create_test_account(neo4j_session, account, 1)
        load(
            neo4j_session,
            ELBV2TargetGroupSchema(),
            [{"TargetGroupArn": f"target-group-{name}"}],
            Region=REGION,
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
            REGION,
            account,
            1,
        )
        ecs.load_ecs_tasks(
            neo4j_session,
            "cluster",
            [{"taskArn": f"task-{name}", "clusterArn": "cluster", "serviceName": name}],
            REGION,
            account,
            1,
        )
        ecs.load_ecs_containers(
            neo4j_session,
            [{"containerArn": f"container-{name}", "taskArn": f"task-{name}"}],
            REGION,
            account,
            1,
        )

    failed_client = MagicMock()
    healthy_client = MagicMock()
    healthy_client.get_paginator.return_value.paginate.return_value = [{}]
    healthy_client.describe_clusters.return_value = {"clusters": []}
    failed_client.describe_clusters.return_value = {
        "clusters": [{"clusterArn": "cluster"}]
    }

    def paginator(operation):
        result = MagicMock()
        if operation == failure or (
            failure == "timeout" and operation == "list_clusters"
        ):
            result.paginate.side_effect = (
                ReadTimeoutError(endpoint_url="https://ecs.example.invalid")
                if failure == "timeout"
                else ClientError(
                    {
                        "Error": {
                            "Code": "AccessDeniedException",
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

    # Assert: collection continues without deleting workloads or their relationships.
    healthy_client.get_paginator.assert_called_with("list_clusters")
    for label, prefix in (
        ("AWSECSService", "service"),
        ("AWSECSTask", "task"),
        ("AWSECSContainer", "container"),
    ):
        assert check_nodes(neo4j_session, label, ["id"]) == {
            (f"{prefix}-selected",),
            (f"{prefix}-other",),
        }
    assert check_rels(
        neo4j_session,
        "AWSELBV2TargetGroup",
        "id",
        "AWSECSService",
        "id",
        "TARGETS",
        rel_direction_right=True,
    ) == {
        ("target-group-selected", "service-selected"),
        ("target-group-other", "service-other"),
    }
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSService",
        "id",
        "WORKLOAD_PARENT",
        rel_direction_right=True,
    ) == {
        ("task-selected", "service-selected"),
        ("task-other", "service-other"),
    }
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {
        ("task-selected", "container-selected"),
        ("task-other", "container-other"),
    }

    # Act: a later successful empty inventory permits normal account cleanup.
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
