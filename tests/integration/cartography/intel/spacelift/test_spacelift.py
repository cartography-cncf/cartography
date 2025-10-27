from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.spacelift.account import sync_account
from cartography.intel.spacelift.runs import sync_runs
from cartography.intel.spacelift.spaces import sync_spaces
from cartography.intel.spacelift.stacks import sync_stacks
from cartography.intel.spacelift.users import sync_users
from cartography.intel.spacelift.workerpools import sync_worker_pools
from cartography.intel.spacelift.workers import sync_workers
from tests.data.spacelift.spacelift_data import ACCOUNT_DATA
from tests.data.spacelift.spacelift_data import EC2_INSTANCES_DATA
from tests.data.spacelift.spacelift_data import ENTITIES_DATA
from tests.data.spacelift.spacelift_data import RUNS_DATA
from tests.data.spacelift.spacelift_data import SPACES_DATA
from tests.data.spacelift.spacelift_data import STACKS_DATA
from tests.data.spacelift.spacelift_data import USERS_DATA
from tests.data.spacelift.spacelift_data import WORKER_POOLS_DATA
from tests.data.spacelift.spacelift_data import WORKERS_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_ENDPOINT = "https://fake.spacelift.io/graphql"
TEST_ACCOUNT_ID = "test-account-123"


@patch('cartography.intel.spacelift.runs.call_spacelift_api')
@patch('cartography.intel.spacelift.runs.fetch_all_paginated')
@patch('cartography.intel.spacelift.workers.fetch_all_paginated')
@patch('cartography.intel.spacelift.workerpools.fetch_all_paginated')
@patch('cartography.intel.spacelift.stacks.fetch_all_paginated')
@patch('cartography.intel.spacelift.users.fetch_all_paginated')
@patch('cartography.intel.spacelift.spaces.fetch_all_paginated')
@patch('cartography.intel.spacelift.account.fetch_single_query')
def test_sync_spacelift_runs_with_ec2_relationships_end_to_end(
    mock_account_fetch_single_query,
    mock_spaces_fetch_all_paginated,
    mock_users_fetch_all_paginated,
    mock_stacks_fetch_all_paginated,
    mock_workerpools_fetch_all_paginated,
    mock_workers_fetch_all_paginated,
    mock_runs_fetch_all_paginated,
    mock_runs_call_spacelift_api,
    neo4j_session,
):
    """
    Test that Spacelift runs are correctly synced and connected to EC2 instances.
    This tests the complete end-to-end flow including the Run-[:AFFECTS]->EC2Instance relationship.
    """
    # Arrange - Mock all API calls
    # Account uses fetch_single_query - returns the extracted account object
    mock_account_fetch_single_query.return_value = ACCOUNT_DATA["data"]["account"]

    # Each module uses fetch_all_paginated - returns already-extracted lists
    mock_spaces_fetch_all_paginated.return_value = SPACES_DATA
    mock_users_fetch_all_paginated.return_value = USERS_DATA
    mock_stacks_fetch_all_paginated.return_value = STACKS_DATA
    mock_workerpools_fetch_all_paginated.return_value = WORKER_POOLS_DATA
    mock_workers_fetch_all_paginated.return_value = WORKERS_DATA
    mock_runs_fetch_all_paginated.return_value = RUNS_DATA

    
    mock_runs_call_spacelift_api.return_value = ENTITIES_DATA

    # Create mock spacelift session
    spacelift_session = MagicMock()

    # Create mock EC2 instances (simulating AWS EC2 sync running before Spacelift sync)
    for instance in EC2_INSTANCES_DATA:
        neo4j_session.run(
            """
            MERGE (i:EC2Instance{instanceid: $instance_id})
            SET i.id = $instance_id,
                i.region = $region,
                i.instancetype = $instance_type,
                i.state = $state
            """,
            instance_id=instance["InstanceId"],
            region=instance["Region"],
            instance_type=instance["InstanceType"],
            state=instance["State"],
        )

    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "SPACELIFT_ACCOUNT_ID": TEST_ACCOUNT_ID,
        "account_id": TEST_ACCOUNT_ID,
    }

    # Act - Sync all Spacelift resources in the correct order
    sync_account(neo4j_session, spacelift_session, TEST_API_ENDPOINT, common_job_parameters)
    sync_spaces(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)
    sync_users(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)
    sync_stacks(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)
    sync_worker_pools(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)
    sync_workers(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)
    sync_runs(neo4j_session, spacelift_session, TEST_API_ENDPOINT, TEST_ACCOUNT_ID, common_job_parameters)

    # Assert - Test that SpaceliftAccount was created
    expected_account_nodes = {
        (TEST_ACCOUNT_ID, "Test Organization"),
    }
    actual_account_nodes = check_nodes(
        neo4j_session,
        "SpaceliftAccount",
        ["id", "name"],
    )
    assert actual_account_nodes is not None
    assert expected_account_nodes == actual_account_nodes

    # Assert - Test that SpaceliftRun nodes were created
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

    # Assert - Test that Run-[:AFFECTS]->EC2Instance relationships were created
    expected_run_ec2_relationships = {
        ("run-1", "i-1234567890abcdef0"),
        ("run-1", "i-0987654321fedcba0"),
        ("run-2", "i-abcdef1234567890a"),
    }
    actual_run_ec2_relationships = check_rels(
        neo4j_session,
        "SpaceliftRun",
        "id",
        "EC2Instance",
        "instanceid",
        "AFFECTS",
    )
    assert actual_run_ec2_relationships is not None
    assert expected_run_ec2_relationships == actual_run_ec2_relationships

    # Assert - Test that Stack-[:GENERATES]->Run relationships were created
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
        "GENERATES",
    )
    assert actual_stack_run_relationships is not None
    assert expected_stack_run_relationships == actual_stack_run_relationships

    # Assert - Test that Worker-[:EXECUTES]->Run relationships were created
    expected_worker_run_relationships = {
        ("worker-1", "run-1"),
        ("worker-2", "run-2"),
    }
    actual_worker_run_relationships = check_rels(
        neo4j_session,
        "SpaceliftWorker",
        "id",
        "SpaceliftRun",
        "id",
        "EXECUTES",
    )
    assert actual_worker_run_relationships is not None
    assert expected_worker_run_relationships == actual_worker_run_relationships

    # Assert - Test that Space-[:CONTAINS]->Stack relationships were created
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

    # Assert - Test that WorkerPool-[:CONTAINS]->Worker relationships were created
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
