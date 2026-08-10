import copy
from unittest.mock import patch

import cartography.intel.aws.ecs
import tests.data.aws.ecs
from cartography.analysis.aws.analysis import AWS_ECS_ASSET_EXPOSURE
from cartography.intel.aws import AWS_ECS_ASSET_EXPOSURE_DEPS
from cartography.util import run_typed_analysis_and_ensure_deps
from cartography.util import run_typed_analysis_job
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
CLUSTER_ARN = "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster"


def test_load_ecs_clusters(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_CLUSTERS
    cartography.intel.aws.ecs.load_ecs_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "AWSECSCluster",
        ["id", "name", "status"],
    ) == {
        (
            CLUSTER_ARN,
            "test_cluster",
            "ACTIVE",
        ),
    }


def test_load_ecs_container_instances(neo4j_session, *args):
    cartography.intel.aws.ecs.load_ecs_clusters(
        neo4j_session,
        tests.data.aws.ecs.GET_ECS_CLUSTERS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Create AWSEC2Instance node so the IS_INSTANCE relationship can be created
    neo4j_session.run(
        """
        MERGE (i:AWSEC2Instance{id: $InstanceId})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = $aws_update_tag
        """,
        InstanceId="i-00000000000000000",
        aws_update_tag=TEST_UPDATE_TAG,
    )
    data = tests.data.aws.ecs.GET_ECS_CONTAINER_INSTANCES
    cartography.intel.aws.ecs.load_ecs_container_instances(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "AWSECSContainerInstance",
        ["id", "ec2_instance_id", "status", "version"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
            "ACTIVE",
            100000,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSECSCluster",
        "id",
        "AWSECSContainerInstance",
        "id",
        "HAS_CONTAINER_INSTANCE",
        rel_direction_right=True,
    ) == {
        (
            CLUSTER_ARN,
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSECSContainerInstance",
        "id",
        "AWSEC2Instance",
        "id",
        "IS_INSTANCE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
        ),
    }


def test_load_ecs_services(neo4j_session, *args):
    cartography.intel.aws.ecs.load_ecs_clusters(
        neo4j_session,
        tests.data.aws.ecs.GET_ECS_CLUSTERS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.aws.ecs.GET_ECS_SERVICES
    cartography.intel.aws.ecs.load_ecs_services(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "AWSECSService",
        ["id", "name", "cluster_arn", "status"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "test_service",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "ACTIVE",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSECSCluster",
        "id",
        "AWSECSService",
        "id",
        "HAS_SERVICE",
        rel_direction_right=True,
    ) == {
        (
            CLUSTER_ARN,
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
        ),
    }


def test_load_ecs_services_target_group_registrations(neo4j_session, *args):
    # Seed AWSAccount and ECS cluster
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $update_tag, aws :Tenant
        """,
        aws_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ecs.load_ecs_clusters(
        neo4j_session,
        tests.data.aws.ecs.GET_ECS_CLUSTERS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Seed an AWSELBV2TargetGroup node matching the ARN in GET_ECS_SERVICES fixture
    tg_arn = "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/test_group/0000000000090000"
    neo4j_session.run(
        """
        MERGE (tg:AWSELBV2TargetGroup{id: $tg_arn})
        ON CREATE SET tg.firstseen = timestamp()
        SET tg.lastupdated = $update_tag
        """,
        tg_arn=tg_arn,
        update_tag=TEST_UPDATE_TAG,
    )

    # Load ECS services (this also loads the TG→AWSECSService matchlinks)
    cartography.intel.aws.ecs.load_ecs_services(
        neo4j_session,
        CLUSTER_ARN,
        tests.data.aws.ecs.GET_ECS_SERVICES,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert the TARGETS edge exists with the right properties
    result = neo4j_session.run(
        """
        MATCH (tg:AWSELBV2TargetGroup {id: $tg_arn})-[r:TARGETS]->(svc:AWSECSService)
        RETURN svc.id AS svc_id, r.container_name AS container_name, r.container_port AS container_port
        """,
        tg_arn=tg_arn,
    )
    records = [dict(r) for r in result]
    assert len(records) == 1
    assert (
        records[0]["svc_id"]
        == "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service"
    )
    assert records[0]["container_name"] == "test_container"
    assert records[0]["container_port"] == 8080


def test_load_ecs_tasks(neo4j_session, *args):
    # Arrange
    data = copy.deepcopy(tests.data.aws.ecs.GET_ECS_TASKS)
    data = cartography.intel.aws.ecs.transform_ecs_tasks(data)
    containers = cartography.intel.aws.ecs._get_containers_from_tasks(data)

    # Act
    cartography.intel.aws.ecs.load_ecs_tasks(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ecs.load_ecs_containers(
        neo4j_session,
        containers,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSECSTask",
        ["id", "task_definition_arn", "cluster_arn", "group"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "service:test_service",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "AWSECSContainer",
        ["id", "name", "image", "image_digest"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",  # noqa:E501
            "test-task_container",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
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
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "AWSECSContainer",
        [
            "id",
            "architecture",
            "architecture_normalized",
            "architecture_source",
        ],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
            "x86_64",
            "amd64",
            "runtime_api_exact",
        ),
    }


def test_load_ecs_tasks_with_live_redacted_payload(neo4j_session):
    # The neo4j integration fixture is module-scoped, so isolate this test's data.
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    try:
        from unittest.mock import MagicMock

        task_definitions = copy.deepcopy(
            tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS_LIVE_REDACTED
        )
        task_definition_architecture = (
            cartography.intel.aws.ecs._get_task_definition_architecture(
                task_definitions
            )
        )
        assert task_definition_architecture == {}

        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        boto3_session = MagicMock()
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }
        internal_tooling_cluster_arn = (
            "arn:aws:ecs:us-east-1:000000000000:cluster/internal-tooling"
        )

        with (
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_cluster_arns",
                return_value=[internal_tooling_cluster_arn],
            ),
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_clusters",
                return_value=[
                    {
                        "clusterArn": internal_tooling_cluster_arn,
                        "clusterName": "internal-tooling",
                        "status": "ACTIVE",
                    }
                ],
            ),
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_container_instances",
                return_value=[],
            ),
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_services",
                return_value=[],
            ),
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_tasks",
                return_value=copy.deepcopy(
                    tests.data.aws.ecs.GET_ECS_TASKS_LIVE_REDACTED
                ),
            ),
            patch.object(
                cartography.intel.aws.ecs,
                "get_ecs_task_definitions",
                return_value=copy.deepcopy(
                    tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS_LIVE_REDACTED
                ),
            ),
        ):
            cartography.intel.aws.ecs.sync(
                neo4j_session,
                boto3_session,
                [TEST_REGION],
                TEST_ACCOUNT_ID,
                TEST_UPDATE_TAG,
                common_job_parameters,
            )

        assert check_nodes(
            neo4j_session,
            "AWSECSTask",
            ["id", "service_name", "network_interface_id"],
        ) == {
            (
                "arn:aws:ecs:us-east-1:000000000000:task/internal-tooling/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "sublime",
                "eni-00000000000000000",
            ),
        }

        assert check_nodes(
            neo4j_session,
            "AWSECSContainer",
            ["name", "architecture", "architecture_normalized", "architecture_source"],
        ) == {
            ("sublime", "x86_64", "amd64", "runtime_api_exact"),
        }
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n;")


def test_ecs_container_architecture_fallback_from_task_definition(neo4j_session):
    tasks = copy.deepcopy(tests.data.aws.ecs.GET_ECS_TASKS)
    tasks[0]["attributes"] = []
    task_definitions = copy.deepcopy(tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS)
    from unittest.mock import MagicMock

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    boto3_session = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    with (
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_cluster_arns",
            return_value=[CLUSTER_ARN],
        ),
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_clusters",
            return_value=tests.data.aws.ecs.GET_ECS_CLUSTERS,
        ),
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_container_instances",
            return_value=[],
        ),
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_services",
            return_value=[],
        ),
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_tasks",
            return_value=tasks,
        ),
        patch.object(
            cartography.intel.aws.ecs,
            "get_ecs_task_definitions",
            return_value=task_definitions,
        ),
    ):
        cartography.intel.aws.ecs.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
    assert check_nodes(
        neo4j_session,
        "AWSECSContainer",
        [
            "id",
            "architecture",
            "architecture_normalized",
            "architecture_source",
        ],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
            "X86_64",
            "amd64",
            "task_definition_hint",
        ),
    }


def test_transform_ecs_tasks(neo4j_session):
    """Test that ECS tasks with network interface attachments are transformed correctly."""
    # Arrange
    neo4j_session.run(
        """
        MERGE (ni:AWSNetworkInterface{id: $NetworkInterfaceId})
        ON CREATE SET ni.firstseen = timestamp()
        SET ni.lastupdated = $aws_update_tag
        """,
        NetworkInterfaceId="eni-00000000000000000",
        aws_update_tag=TEST_UPDATE_TAG,
    )

    task_data = tests.data.aws.ecs.GET_ECS_TASKS
    task_data = cartography.intel.aws.ecs.transform_ecs_tasks(task_data)

    # Act
    cartography.intel.aws.ecs.load_ecs_tasks(
        neo4j_session,
        CLUSTER_ARN,
        task_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSNetworkInterface",
        "id",
        "NETWORK_INTERFACE",
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "eni-00000000000000000",
        ),
    }


def test_load_ecs_task_definitions(neo4j_session, *args):
    # Arrange
    data = tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS
    container_defs = (
        cartography.intel.aws.ecs._get_container_defs_from_task_definitions(data)
    )

    # Act
    cartography.intel.aws.ecs.load_ecs_task_definitions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ecs.load_ecs_container_definitions(
        neo4j_session,
        container_defs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSECSTaskDefinition",
        ["id", "family", "status", "revision"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "test_family",
            "ACTIVE",
            4,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "AWSECSContainerDefinition",
        ["id", "name", "image"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
            "test",
            "test/test:latest",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSECSTaskDefinition",
        "id",
        "AWSECSContainerDefinition",
        "id",
        "HAS_CONTAINER_DEFINITION",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
        ),
    }


@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_cluster_arns",
    return_value=[CLUSTER_ARN],
)
@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_clusters",
    return_value=tests.data.aws.ecs.GET_ECS_CLUSTERS,
)
@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_container_instances",
    return_value=tests.data.aws.ecs.GET_ECS_CONTAINER_INSTANCES,
)
@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_services",
    return_value=tests.data.aws.ecs.GET_ECS_SERVICES,
)
@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_tasks",
    return_value=tests.data.aws.ecs.GET_ECS_TASKS,
)
@patch.object(
    cartography.intel.aws.ecs,
    "get_ecs_task_definitions",
    return_value=tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS,
)
def test_sync_ecs_comprehensive(
    mock_get_task_definitions,
    mock_get_tasks,
    mock_get_services,
    mock_get_container_instances,
    mock_get_clusters,
    mock_get_cluster_arns,
    neo4j_session,
):
    """
    Comprehensive test for cartography.intel.aws.ecs.sync() function.
    Tests all relationships using check_rels() style as recommended in AGENTS.md.
    """
    # Arrange
    from unittest.mock import MagicMock

    boto3_session = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create AWSRole nodes for task and execution roles
    neo4j_session.run(
        """
        MERGE (role:AWSPrincipal:AWSRole{arn: $RoleArn})
        ON CREATE SET role.firstseen = timestamp()
        SET role.lastupdated = $aws_update_tag, role.roleid = $RoleId, role.name = $RoleName
        """,
        RoleArn="arn:aws:iam::000000000000:role/test-ecs_task_execution",
        RoleId="test-ecs_task_execution",
        RoleName="test-ecs_task_execution",
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Create AWSEC2Instance node for container instance relationship
    neo4j_session.run(
        """
        MERGE (i:AWSEC2Instance{id: $InstanceId})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = $aws_update_tag
        """,
        InstanceId="i-00000000000000000",
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Create AWSECRImage node for the container image
    neo4j_session.run(
        """
        MERGE (img:AWSECRImage{id: $ImageDigest})
        ON CREATE SET img.firstseen = timestamp()
        SET img.lastupdated = $aws_update_tag, img.digest = $ImageDigest
        """,
        ImageDigest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.aws.ecs.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Test all relationships using check_rels() style

    # 1. ECSTasks attached to ECSContainers
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }, "ECSTasks attached to ECSContainers"

    # 2. ECSTasks to ECSTaskDefinitions
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSTaskDefinition",
        "id",
        "HAS_TASK_DEFINITION",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        ),
    }, "ECSTasks attached to ECSTaskDefinitions"

    # 3. ECSTasks to ECSContainerInstances
    assert check_rels(
        neo4j_session,
        "AWSECSContainerInstance",
        "id",
        "AWSECSTask",
        "id",
        "HAS_TASK",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
        ),
    }, "ECSTasks attached to ECSContainerInstances"

    # 4. ECSTaskDefinitions attached to ECSContainerDefinitions
    assert check_rels(
        neo4j_session,
        "AWSECSTaskDefinition",
        "id",
        "AWSECSContainerDefinition",
        "id",
        "HAS_CONTAINER_DEFINITION",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
        ),
    }, "ECSTaskDefinitions attached to ECSContainerDefinitions"

    # 5. ECSContainerInstances to ECSClusters
    assert check_rels(
        neo4j_session,
        "AWSECSCluster",
        "id",
        "AWSECSContainerInstance",
        "id",
        "HAS_CONTAINER_INSTANCE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
        ),
    }, "ECSContainerInstances to ECSClusters"

    # 6. ECSContainers to ECSTasks
    assert check_rels(
        neo4j_session,
        "AWSECSTask",
        "id",
        "AWSECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }, "ECSContainers to ECSTasks"

    # # 7. AWSECSService to ECSTaskDefinitions
    assert check_rels(
        neo4j_session,
        "AWSECSService",
        "id",
        "AWSECSTaskDefinition",
        "id",
        "HAS_TASK_DEFINITION",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        ),
    }, "AWSECSService to ECSTaskDefinitions"

    # 8. ECSTasks to ECSClusters (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSCluster",
        "id",
        "AWSECSTask",
        "id",
        "HAS_TASK",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
        ),
    }, "ECSClusters to ECSTasks"

    # 9. ECSServices to ECSClusters (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSCluster",
        "id",
        "AWSECSService",
        "id",
        "HAS_SERVICE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
        ),
    }, "ECSClusters to ECSServices"

    # # 10. ECSClusters to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSCluster",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster"),
    }, "ECSClusters to AWSAccount"

    # 11. ECSTaskDefinitions to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSTaskDefinition",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        ),
    }, "ECSTaskDefinitions to AWSAccount"

    # 12. ECSContainerDefinitions to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSContainerDefinition",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
        ),
    }, "ECSContainerDefinitions to AWSAccount"

    # 13. ECSContainers to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSContainer",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }, "ECSContainers to AWSAccount"

    # 14. ECSContainerInstances to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSContainerInstance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
        ),
    }, "ECSContainerInstances to AWSAccount"

    # 15. ECSContainerInstances to AWSEC2Instance (IS_INSTANCE relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSContainerInstance",
        "id",
        "AWSEC2Instance",
        "id",
        "IS_INSTANCE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
        ),
    }, "ECSContainerInstances to AWSEC2Instance"

    # 16. ECSServices to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSECSService",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
        ),
    }, "ECSServices to AWSAccount"

    # 16. ECSTaskDefinitions to AWSRole (HAS_TASK_ROLE relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSTaskDefinition",
        "id",
        "AWSRole",
        "arn",
        "HAS_TASK_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:iam::000000000000:role/test-ecs_task_execution",
        ),
    }, "ECSTaskDefinitions to AWSRole (HAS_TASK_ROLE)"

    # 17. ECSTaskDefinitions to AWSRole (HAS_EXECUTION_ROLE relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSTaskDefinition",
        "id",
        "AWSRole",
        "arn",
        "HAS_EXECUTION_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:iam::000000000000:role/test-ecs_task_execution",
        ),
    }, "ECSTaskDefinitions to AWSRole (HAS_EXECUTION_ROLE)"

    # 18. ECSContainers to AWSECRImage (HAS_IMAGE relationship)
    assert check_rels(
        neo4j_session,
        "AWSECSContainer",
        "id",
        "AWSECRImage",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }, "ECSContainers to AWSECRImage (HAS_IMAGE)"

    # AWSECSService to ECSTasks
    assert check_rels(
        neo4j_session,
        "AWSECSService",
        "id",
        "AWSECSTask",
        "id",
        "HAS_TASK",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
        ),
    }, "AWSECSService to ECSTasks"

    # Verify that all expected nodes were created
    assert check_nodes(
        neo4j_session,
        "AWSECSCluster",
        ["id", "name", "status"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "test_cluster",
            "ACTIVE",
        ),
    }, "ECSClusters"

    assert check_nodes(
        neo4j_session,
        "AWSECSTask",
        ["id", "task_definition_arn", "cluster_arn"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        ),
    }, "ECSTasks"

    assert check_nodes(
        neo4j_session,
        "AWSECSTaskDefinition",
        ["id", "family", "status"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "test_family",
            "ACTIVE",
        ),
    }, "ECSTaskDefinitions"

    assert check_nodes(
        neo4j_session,
        "AWSECSContainer",
        ["id", "name", "image"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
            "test-task_container",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
        ),
    }, "ECSContainers"

    assert check_nodes(
        neo4j_session,
        "AWSECSContainerDefinition",
        ["id", "name", "image"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
            "test",
            "test/test:latest",
        ),
    }, "ECSContainerDefinitions"

    assert check_nodes(
        neo4j_session,
        "AWSECSContainerInstance",
        ["id", "ec2_instance_id", "status"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
            "ACTIVE",
        ),
    }, "ECSContainerInstances"

    assert check_nodes(
        neo4j_session,
        "AWSECSService",
        ["id", "name", "cluster_arn"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "test_service",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        ),
    }, "ECSServices"


def _build_ecs_direct_exposure_chain(neo4j_session, suffix):
    """
    Build 0.0.0.0/0 -> IpPermissionInbound -> SecurityGroup <- ENI (public IP) <- Task -> Container
    with per-test-unique node ids (the module-scoped neo4j_session is shared across tests with no
    per-test cleanup). Returns the container id.
    """
    container_id = (
        f"arn:aws:ecs:us-east-1:000000000000:container/cluster/task-{suffix}/web"
    )
    neo4j_session.run(
        """
        MERGE (r:AWSIpRange{id: '0.0.0.0/0'}) SET r.lastupdated = $tag
        MERGE (perm:AWSIpPermissionInbound{id: 'perm-' + $suffix}) SET perm.lastupdated = $tag
        MERGE (sg:AWSEC2SecurityGroup{id: 'sg-' + $suffix, groupid: 'sg-' + $suffix}) SET sg.lastupdated = $tag
        MERGE (ni:AWSNetworkInterface{id: 'eni-' + $suffix}) SET ni.lastupdated = $tag, ni.public_ip = '52.9.8.7'
        MERGE (task:AWSECSTask{id: 'arn:aws:ecs:us-east-1:000000000000:task/cluster/task-' + $suffix})
            SET task.lastupdated = $tag
        MERGE (c:AWSECSContainer{id: $container_id}) SET c.lastupdated = $tag, c.name = 'web'
        MERGE (r)-[:MEMBER_OF_IP_RULE]->(perm)
        MERGE (perm)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        MERGE (ni)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        MERGE (task)-[:NETWORK_INTERFACE]->(ni)
        MERGE (task)-[:HAS_CONTAINER]->(c)
        """,
        tag=TEST_UPDATE_TAG,
        suffix=suffix,
        container_id=container_id,
    )
    return container_id


def _get_container_exposure(neo4j_session, container_id):
    return neo4j_session.run(
        "MATCH (c:AWSECSContainer{id: $container_id}) "
        "RETURN c.exposed_internet AS exposed, c.exposed_internet_type AS types",
        container_id=container_id,
    ).single()


def test_ecs_direct_internet_exposure(neo4j_session):
    """
    aws_ecs_asset_exposure marks an ECS container as directly internet-exposed when its task's ENI
    has a public IP and a security group that allows inbound from 0.0.0.0/0.
    """
    container_id = _build_ecs_direct_exposure_chain(neo4j_session, "direct")

    run_typed_analysis_job(
        AWS_ECS_ASSET_EXPOSURE,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    result = _get_container_exposure(neo4j_session, container_id)
    assert result["exposed"] is True
    assert "direct" in result["types"]


def test_ecs_direct_exposure_skipped_when_security_group_not_synced(neo4j_session):
    """
    A partial sync that omits ec2:security_group must NOT recompute ECS exposure: the security-group
    data in the graph may be stale, so the guard skips the job rather than marking a false positive.
    A subsequent run that does include the security-group sync then marks the container exposed.
    """
    container_id = _build_ecs_direct_exposure_chain(neo4j_session, "guard")

    # Partial sync: everything the job needs except ec2:security_group -> job is skipped.
    partial_syncs = AWS_ECS_ASSET_EXPOSURE_DEPS - {"ec2:security_group"}
    run_typed_analysis_and_ensure_deps(
        AWS_ECS_ASSET_EXPOSURE,
        AWS_ECS_ASSET_EXPOSURE_DEPS,
        partial_syncs,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        neo4j_session,
    )
    skipped = _get_container_exposure(neo4j_session, container_id)
    assert skipped["exposed"] is None
    assert skipped["types"] is None

    # Full dependency set present -> job runs and marks the container exposed.
    run_typed_analysis_and_ensure_deps(
        AWS_ECS_ASSET_EXPOSURE,
        AWS_ECS_ASSET_EXPOSURE_DEPS,
        set(AWS_ECS_ASSET_EXPOSURE_DEPS),
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        neo4j_session,
    )
    ran = _get_container_exposure(neo4j_session, container_id)
    assert ran["exposed"] is True
    assert "direct" in ran["types"]
