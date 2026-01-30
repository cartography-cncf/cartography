from unittest.mock import patch

import cartography.intel.aws.ecs
import tests.data.aws.ecs
from cartography.util import run_analysis_job
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
        "ECSCluster",
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
        "ECSContainerInstance",
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
        "ECSCluster",
        "id",
        "ECSContainerInstance",
        "id",
        "HAS_CONTAINER_INSTANCE",
        rel_direction_right=True,
    ) == {
        (
            CLUSTER_ARN,
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
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
        "ECSService",
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
        "ECSCluster",
        "id",
        "ECSService",
        "id",
        "HAS_SERVICE",
        rel_direction_right=True,
    ) == {
        (
            CLUSTER_ARN,
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
        ),
    }


def test_load_ecs_tasks(neo4j_session, *args):
    # Arrange
    data = tests.data.aws.ecs.GET_ECS_TASKS
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
        "ECSTask",
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
        "ECSContainer",
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
        "ECSTask",
        "id",
        "ECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }


def test_transform_ecs_tasks(neo4j_session):
    """Test that ECS tasks with network interface attachments are transformed correctly."""
    # Arrange
    neo4j_session.run(
        """
        MERGE (ni:NetworkInterface{id: $NetworkInterfaceId})
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
        "ECSTask",
        "id",
        "NetworkInterface",
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
        "ECSTaskDefinition",
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
        "ECSContainerDefinition",
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
        "ECSTaskDefinition",
        "id",
        "ECSContainerDefinition",
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

    # Create ECRImage node for the container image
    neo4j_session.run(
        """
        MERGE (img:ECRImage{id: $ImageDigest})
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
        "ECSTask",
        "id",
        "ECSContainer",
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
        "ECSTask",
        "id",
        "ECSTaskDefinition",
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
        "ECSContainerInstance",
        "id",
        "ECSTask",
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
        "ECSTaskDefinition",
        "id",
        "ECSContainerDefinition",
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
        "ECSCluster",
        "id",
        "ECSContainerInstance",
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
        "ECSTask",
        "id",
        "ECSContainer",
        "id",
        "HAS_CONTAINER",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
        ),
    }, "ECSContainers to ECSTasks"

    # # 7. ECSService to ECSTaskDefinitions
    assert check_rels(
        neo4j_session,
        "ECSService",
        "id",
        "ECSTaskDefinition",
        "id",
        "HAS_TASK_DEFINITION",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        ),
    }, "ECSService to ECSTaskDefinitions"

    # 8. ECSTasks to ECSClusters (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "ECSCluster",
        "id",
        "ECSTask",
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
        "ECSCluster",
        "id",
        "ECSService",
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
        "ECSCluster",
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
        "ECSTaskDefinition",
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
        "ECSContainerDefinition",
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
        "ECSContainer",
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
        "ECSContainerInstance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
        ),
    }, "ECSContainerInstances to AWSAccount"

    # 15. ECSServices to AWSAccount (sub-resource relationship)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "ECSService",
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
        "ECSTaskDefinition",
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
        "ECSTaskDefinition",
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

    # 18. ECSContainers to ECRImage (HAS_IMAGE relationship)
    assert check_rels(
        neo4j_session,
        "ECSContainer",
        "id",
        "ECRImage",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }, "ECSContainers to ECRImage (HAS_IMAGE)"

    # ECSService to ECSTasks
    assert check_rels(
        neo4j_session,
        "ECSService",
        "id",
        "ECSTask",
        "id",
        "HAS_TASK",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
        ),
    }, "ECSService to ECSTasks"

    # Verify that all expected nodes were created
    assert check_nodes(
        neo4j_session,
        "ECSCluster",
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
        "ECSTask",
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
        "ECSTaskDefinition",
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
        "ECSContainer",
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
        "ECSContainerDefinition",
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
        "ECSContainerInstance",
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
        "ECSService",
        ["id", "name", "cluster_arn"],
    ) == {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "test_service",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        ),
    }, "ECSServices"


def test_resolve_container_image_manifests_direct_image(neo4j_session):
    """
    Test that containers referencing direct platform images get resolvedImageDigest set correctly.
    When imageDigest points to an ECRImage with type='image', resolvedImageDigest should equal imageDigest.
    """
    # Arrange: Create ECR image node (direct platform image)
    direct_digest = tests.data.aws.ecs.DIRECT_IMAGE_DIGEST
    neo4j_session.run(
        """
        MERGE (img:ECRImage {id: $digest})
        SET img.digest = $digest,
            img.type = 'image',
            img.architecture = 'amd64',
            img.lastupdated = $update_tag
        """,
        digest=direct_digest,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create ECS container pointing to the direct image
    container_data = [tests.data.aws.ecs.ECS_CONTAINERS_FOR_RESOLUTION[0]]
    cartography.intel.aws.ecs.load_ecs_containers(
        neo4j_session,
        container_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Run resolution via analysis job
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    run_analysis_job(
        "container_image_resolution.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert: resolved_image_digest should equal image_digest for direct images
    result = neo4j_session.run(
        """
        MATCH (c:ECSContainer {name: 'direct-image-container'})
        RETURN c.image_digest as image_digest,
               c.resolved_image_digest as resolved_image_digest,
               c.manifest_list_digest as manifest_list_digest
        """,
    ).single()

    assert result is not None
    assert result["image_digest"] == direct_digest
    assert result["resolved_image_digest"] == direct_digest
    assert (
        result["manifest_list_digest"] is None
    ), "manifest_list_digest should be null for direct images"


def test_resolve_container_image_manifests_manifest_list(neo4j_session):
    """
    Test that containers referencing manifest lists get resolvedImageDigest set to the platform image.
    When imageDigest points to an ECRImage with type='manifest_list', the resolution should follow
    the CONTAINS_IMAGE relationship to find the platform-specific image.
    """
    # Arrange: Create ECR manifest list and platform images
    manifest_list_digest = tests.data.aws.ecs.MANIFEST_LIST_DIGEST
    amd64_digest = tests.data.aws.ecs.PLATFORM_IMAGE_AMD64_DIGEST
    arm64_digest = tests.data.aws.ecs.PLATFORM_IMAGE_ARM64_DIGEST

    # Create manifest list
    neo4j_session.run(
        """
        MERGE (ml:ECRImage {id: $digest})
        SET ml.digest = $digest,
            ml.type = 'manifest_list',
            ml.lastupdated = $update_tag
        """,
        digest=manifest_list_digest,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create platform images
    neo4j_session.run(
        """
        MERGE (img:ECRImage {id: $digest})
        SET img.digest = $digest,
            img.type = 'image',
            img.architecture = $arch,
            img.lastupdated = $update_tag
        """,
        digest=amd64_digest,
        arch="amd64",
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:ECRImage {id: $digest})
        SET img.digest = $digest,
            img.type = 'image',
            img.architecture = $arch,
            img.lastupdated = $update_tag
        """,
        digest=arm64_digest,
        arch="arm64",
        update_tag=TEST_UPDATE_TAG,
    )

    # Create CONTAINS_IMAGE relationships
    neo4j_session.run(
        """
        MATCH (ml:ECRImage {digest: $ml_digest})
        MATCH (img:ECRImage {digest: $img_digest})
        MERGE (ml)-[:CONTAINS_IMAGE]->(img)
        """,
        ml_digest=manifest_list_digest,
        img_digest=amd64_digest,
    )
    neo4j_session.run(
        """
        MATCH (ml:ECRImage {digest: $ml_digest})
        MATCH (img:ECRImage {digest: $img_digest})
        MERGE (ml)-[:CONTAINS_IMAGE]->(img)
        """,
        ml_digest=manifest_list_digest,
        img_digest=arm64_digest,
    )

    # Create ECS container pointing to the manifest list
    container_data = [tests.data.aws.ecs.ECS_CONTAINERS_FOR_RESOLUTION[1]]
    cartography.intel.aws.ecs.load_ecs_containers(
        neo4j_session,
        container_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Run resolution via analysis job
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    run_analysis_job(
        "container_image_resolution.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert: resolved_image_digest should be the platform image, manifest_list_digest should be the manifest list
    result = neo4j_session.run(
        """
        MATCH (c:ECSContainer {name: 'manifest-list-container'})
        RETURN c.image_digest as image_digest,
               c.resolved_image_digest as resolved_image_digest,
               c.manifest_list_digest as manifest_list_digest
        """,
    ).single()

    assert result is not None
    assert result["image_digest"] == manifest_list_digest
    # Should resolve to amd64 (preferred) since it's first in ORDER BY
    assert result["resolved_image_digest"] == amd64_digest
    assert result["manifest_list_digest"] == manifest_list_digest


def test_resolve_container_image_manifests_no_ecr_image(neo4j_session):
    """
    Test that containers with no matching ECRImage don't get modified.
    This handles cases where containers use non-ECR images (e.g., Docker Hub).
    """
    # Arrange: Create ECS container with digest that has no matching ECRImage
    container_data = [
        {
            "containerArn": "arn:aws:ecs:us-east-1:000000000000:container/test_cluster/no_ecr_task/no-ecr-container-id",
            "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/test_cluster/no_ecr_task",
            "name": "no-ecr-container",
            "image": "nginx:latest",
            "imageDigest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "lastStatus": "RUNNING",
            "healthStatus": "HEALTHY",
            "cpu": "256",
            "memory": "512",
        }
    ]
    cartography.intel.aws.ecs.load_ecs_containers(
        neo4j_session,
        container_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Run resolution via analysis job (should not fail, just skip this container)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    run_analysis_job(
        "container_image_resolution.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Container should exist but resolved_image_digest should be null
    result = neo4j_session.run(
        """
        MATCH (c:ECSContainer {name: 'no-ecr-container'})
        RETURN c.image_digest as image_digest,
               c.resolved_image_digest as resolved_image_digest,
               c.manifest_list_digest as manifest_list_digest
        """,
    ).single()

    assert result is not None
    assert (
        result["image_digest"]
        == "sha256:9999999999999999999999999999999999999999999999999999999999999999"
    )
    assert result["resolved_image_digest"] is None, "Should not resolve non-ECR images"
    assert result["manifest_list_digest"] is None
