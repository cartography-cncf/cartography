from unittest.mock import patch

import cartography.intel.aws.ecs
import tests.data.aws.ecs
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

    expected_nodes = {
        (
            CLUSTER_ARN,
            "test_cluster",
            "ACTIVE",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSCluster)
        RETURN n.id, n.name, n.status
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.status"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


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

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
            "ACTIVE",
            100000,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainerInstance)
        RETURN n.id, n.ec2_instance_id, n.status, n.version
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.ec2_instance_id"],
            n["n.status"],
            n["n.version"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:ECSCluster)-[:HAS_CONTAINER_INSTANCE]->(n:ECSContainerInstance)
        RETURN count(n.id) AS c
        """,
    )
    for n in nodes:
        assert n["c"] == 1


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

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "test_service",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "ACTIVE",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSService)
        RETURN n.id, n.name, n.cluster_arn, n.status
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.cluster_arn"],
            n["n.status"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:ECSCluster)-[:HAS_SERVICE]->(n:ECSService)
        RETURN count(n.id) AS c
        """,
    )
    for n in nodes:
        assert n["c"] == 1


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
    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "service:test_service",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSTask)
        RETURN n.id, n.task_definition_arn, n.cluster_arn, n.group
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.task_definition_arn"],
            n["n.cluster_arn"],
            n["n.group"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",  # noqa:E501
            "test-task_container",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainer)
        RETURN n.id, n.name, n.image, n.image_digest
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.image"],
            n["n.image_digest"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:ECSTask)-[:HAS_CONTAINER]->(n:ECSContainer)
        RETURN count(n.id) AS c
        """,
    )
    for n in nodes:
        assert n["c"] == 1


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
    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "test_family",
            "ACTIVE",
            4,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSTaskDefinition)
        RETURN n.id, n.family, n.status, n.revision
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.family"],
            n["n.status"],
            n["n.revision"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0-test",
            "test",
            "test/test:latest",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainerDefinition)
        RETURN n.id, n.name, n.image
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.image"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:ECSTaskDefinition)-[:HAS_CONTAINER_DEFINITION]->(n:ECSContainerDefinition)
        RETURN count(n.id) AS c
        """,
    )
    for n in nodes:
        assert n["c"] == 1


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
