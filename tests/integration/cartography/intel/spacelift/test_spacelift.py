from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.spacelift.account import sync_account
from cartography.intel.spacelift.runs import sync_runs
from cartography.intel.spacelift.spaces import sync_spaces
from cartography.intel.spacelift.stacks import sync_stacks
from cartography.intel.spacelift.workerpools import sync_worker_pools
from cartography.intel.spacelift.workers import sync_workers
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.spacelift.spacelift_data import ENTITIES_DATA
from tests.data.spacelift.spacelift_data import RUNS_DATA
from tests.data.spacelift.spacelift_data import SPACES_DATA
from tests.data.spacelift.spacelift_data import STACKS_DATA
from tests.data.spacelift.spacelift_data import WORKER_POOLS_DATA
from tests.data.spacelift.spacelift_data import WORKERS_DATA
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_ENDPOINT = "https://fake.spacelift.io/graphql"
TEST_ACCOUNT_ID = "test-account-123"
TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_AWS_REGION = "us-east-1"


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
@patch("cartography.intel.spacelift.runs.get_entities")
@patch("cartography.intel.spacelift.runs.get_runs")
@patch("cartography.intel.spacelift.workers.get_workers")
@patch("cartography.intel.spacelift.workerpools.get_worker_pools")
@patch("cartography.intel.spacelift.stacks.get_stacks")
@patch("cartography.intel.spacelift.spaces.get_spaces")
@patch("cartography.intel.spacelift.account.get_account")
def test_spacelift_end_to_end(
    mock_get_account,
    mock_get_spaces,
    mock_get_stacks,
    mock_get_worker_pools,
    mock_get_workers,
    mock_get_runs,
    mock_get_entities,
    mock_get_ec2_instances,
    neo4j_session,
):
    """
    End-to-end integration test for Spacelift module.
    Tests syncing of all Spacelift resources and their relationships,
    including Run-[:AFFECTED]->EC2Instance relationships.

    This test uses the real AWS EC2 sync to populate EC2 instances,
    making it more robust than manually creating EC2 nodes.
    """
    # Arrange: Mock all API calls using the mock data file
    mock_get_account.return_value = (
        TEST_ACCOUNT_ID  # get_account now returns just the account_id string
    )
    mock_get_spaces.return_value = SPACES_DATA["data"]["spaces"]
    mock_get_stacks.return_value = STACKS_DATA["data"]["stacks"]
    mock_get_worker_pools.return_value = WORKER_POOLS_DATA["data"]["workerPools"]

    # get_workers returns flattened workers with workerPool field added
    mock_workers_flattened = []
    for pool in WORKERS_DATA["data"]["workerPools"]:
        for worker in pool.get("workers", []):
            worker_copy = worker.copy()
            worker_copy["workerPool"] = pool["id"]
            mock_workers_flattened.append(worker_copy)
    mock_get_workers.return_value = mock_workers_flattened

    # get_runs returns flattened runs with stack field added
    mock_runs_flattened = []
    for stack in RUNS_DATA["data"]["stacks"]:
        for run in stack.get("runs", []):
            run_copy = run.copy()
            run_copy["stack"] = stack["id"]
            mock_runs_flattened.append(run_copy)
    mock_get_runs.return_value = mock_runs_flattened

    # get_entities returns flattened entities from all stacks
    mock_entities_flattened = []
    for stack in ENTITIES_DATA["data"]["stacks"]:
        mock_entities_flattened.extend(stack.get("entities", []))
    mock_get_entities.return_value = mock_entities_flattened

    # Create mock Spacelift session using MagicMock
    spacelift_session = MagicMock()

    # This simulates running AWS sync before Spacelift sync (real-world scenario)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_AWS_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_AWS_REGION],
        TEST_AWS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_AWS_ACCOUNT_ID},
    )

    # Verify EC2 instances were created
    expected_ec2_nodes = {
        ("i-01", "i-01"),
        ("i-02", "i-02"),
        ("i-03", "i-03"),
        ("i-04", "i-04"),
    }
    actual_ec2_nodes = check_nodes(neo4j_session, "EC2Instance", ["id", "instanceid"])
    assert actual_ec2_nodes is not None
    assert expected_ec2_nodes == actual_ec2_nodes

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "spacelift_account_id": TEST_ACCOUNT_ID,
    }

    # Act: Sync all Spacelift resources in the correct order
    sync_account(neo4j_session, TEST_API_ENDPOINT, common_job_parameters)
    sync_spaces(
        neo4j_session,
        spacelift_session,
        TEST_API_ENDPOINT,
        TEST_ACCOUNT_ID,
        common_job_parameters,
    )
    sync_stacks(
        neo4j_session,
        spacelift_session,
        TEST_API_ENDPOINT,
        TEST_ACCOUNT_ID,
        common_job_parameters,
    )
    sync_worker_pools(
        neo4j_session,
        spacelift_session,
        TEST_API_ENDPOINT,
        TEST_ACCOUNT_ID,
        common_job_parameters,
    )
    sync_workers(
        neo4j_session,
        spacelift_session,
        TEST_API_ENDPOINT,
        TEST_ACCOUNT_ID,
        common_job_parameters,
    )
    sync_runs(
        neo4j_session,
        spacelift_session,
        TEST_API_ENDPOINT,
        TEST_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert
    # Check that SpaceliftAccount nodes were created
    expected_account_nodes = {
        (TEST_ACCOUNT_ID, TEST_ACCOUNT_ID),  # name is set to account_id in sync_account
    }
    actual_account_nodes = check_nodes(
        neo4j_session,
        "SpaceliftAccount",
        ["id", "name"],
    )
    assert actual_account_nodes is not None
    assert expected_account_nodes == actual_account_nodes

    # Check that SpaceliftSpace nodes were created
    expected_space_nodes = {
        ("root-space", "Root Space"),
        ("child-space-1", "Child Space 1"),
    }
    actual_space_nodes = check_nodes(
        neo4j_session,
        "SpaceliftSpace",
        ["id", "name"],
    )
    assert actual_space_nodes is not None
    assert expected_space_nodes == actual_space_nodes

    # Check that SpaceliftStack nodes were created
    expected_stack_nodes = {
        ("stack-1", "Production Stack", "ACTIVE"),
        ("stack-2", "Staging Stack", "ACTIVE"),
    }
    actual_stack_nodes = check_nodes(
        neo4j_session,
        "SpaceliftStack",
        ["id", "name", "state"],
    )
    assert actual_stack_nodes is not None
    assert expected_stack_nodes == actual_stack_nodes

    # Check that SpaceliftWorkerPool nodes were created
    expected_pool_nodes = {
        ("pool-1", "Default Pool"),
        ("pool-2", "Private Pool"),
    }
    actual_pool_nodes = check_nodes(
        neo4j_session,
        "SpaceliftWorkerPool",
        ["id", "name"],
    )
    assert actual_pool_nodes is not None
    assert expected_pool_nodes == actual_pool_nodes

    # Check that SpaceliftWorker nodes were created
    expected_worker_nodes = {
        ("worker-1", "ACTIVE"),
        ("worker-2", "ACTIVE"),
    }
    actual_worker_nodes = check_nodes(
        neo4j_session,
        "SpaceliftWorker",
        ["id", "status"],
    )
    assert actual_worker_nodes is not None
    assert expected_worker_nodes == actual_worker_nodes

    # Check that SpaceliftRun nodes were created
    expected_run_nodes = {
        ("run-1", "PROPOSED", "FINISHED"),
        ("run-2", "TRACKED", "FINISHED"),
    }
    actual_run_nodes = check_nodes(
        neo4j_session,
        "SpaceliftRun",
        ["id", "run_type", "state"],
    )
    assert actual_run_nodes is not None
    assert expected_run_nodes == actual_run_nodes

    # Check that Run-[:AFFECTED]->EC2Instance relationships were created (from Spacelift entities API)
    expected_run_ec2_relationships = {
        ("run-1", "i-01"),
        ("run-1", "i-02"),
        ("run-2", "i-03"),
    }
    actual_run_ec2_relationships = check_rels(
        neo4j_session,
        "SpaceliftRun",
        "id",
        "EC2Instance",
        "instanceid",
        "AFFECTED",
    )
    assert actual_run_ec2_relationships is not None
    assert expected_run_ec2_relationships == actual_run_ec2_relationships

    # Check that Stack-[:GENERATED]->Run relationships were created
    expected_stack_run_relationships = {
        ("stack-1", "run-1"),
        ("stack-2", "run-2"),
    }
    actual_stack_run_relationships = check_rels(
        neo4j_session,
        "SpaceliftStack",
        "id",
        "SpaceliftRun",
        "id",
        "GENERATED",
    )
    assert actual_stack_run_relationships is not None
    assert expected_stack_run_relationships == actual_stack_run_relationships

    # Check that Space-[:CONTAINS]->Stack relationships were created
    expected_space_stack_relationships = {
        ("root-space", "stack-1"),
        ("child-space-1", "stack-2"),
    }
    actual_space_stack_relationships = check_rels(
        neo4j_session,
        "SpaceliftSpace",
        "id",
        "SpaceliftStack",
        "id",
        "CONTAINS",
    )
    assert actual_space_stack_relationships is not None
    assert expected_space_stack_relationships == actual_space_stack_relationships

    # Check that WorkerPool-[:CONTAINS]->Worker relationships were created
    expected_pool_worker_relationships = {
        ("pool-1", "worker-1"),
        ("pool-2", "worker-2"),
    }
    actual_pool_worker_relationships = check_rels(
        neo4j_session,
        "SpaceliftWorkerPool",
        "id",
        "SpaceliftWorker",
        "id",
        "CONTAINS",
    )
    assert actual_pool_worker_relationships is not None
    assert expected_pool_worker_relationships == actual_pool_worker_relationships
