from unittest.mock import patch

import cartography.intel.snowflake.tasks
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.tasks import SNOWFLAKE_TASKS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_DATABASE_NAME = "SPRINGFIELD"
TEST_SCHEMA_NAME = "NUCLEAR_PLANT"
TEST_SCHEMA_ID = sf_id(
    SNOWFLAKE_ACCOUNT_ID,
    "schema",
    sf_fqn(TEST_DATABASE_NAME, TEST_SCHEMA_NAME),
)

# What `schemas.sync()` hands to every schema-level workload sync.
TEST_SCHEMAS = [
    {
        "id": TEST_SCHEMA_ID,
        "name": TEST_SCHEMA_NAME,
        "database_name": TEST_DATABASE_NAME,
    },
]


def seed_schema_level_dependencies(neo4j_session) -> None:
    """Seed the nodes owned by other Snowflake syncs that workload edges point at.

    Shared by every schema-level workload test module so each one can exercise its
    own sync against real endpoints instead of restating this.
    """
    neo4j_session.run(
        """
        MERGE (s:SnowflakeSchema {id: $schema_id})
          SET s.name = $schema_name, s.lastupdated = $update_tag
        MERGE (w:SnowflakeWarehouse {id: $warehouse_id})
          SET w.name = 'SECTOR_7G_WH', w.lastupdated = $update_tag
        MERGE (r:SnowflakeRole {id: $role_id})
          SET r.name = 'PLANT_ENGINEER', r.lastupdated = $update_tag
        MERGE (e:SnowflakeNotificationIntegration {id: $error_integration_id})
          SET e.name = 'MELTDOWN_ALERTS', e.lastupdated = $update_tag
        MERGE (n:SnowflakeNotificationIntegration {id: $notify_integration_id})
          SET n.name = 'DONUT_NOTIFY', n.lastupdated = $update_tag
        MERGE (a:SnowflakeApiIntegration {id: $api_integration_id})
          SET a.name = 'DUFF_API', a.lastupdated = $update_tag
        MERGE (x:SnowflakeExternalAccessIntegration {id: $eai_id})
          SET x.name = 'DUFF_EAI', x.lastupdated = $update_tag
        MERGE (k:SnowflakeSecret {id: $secret_id})
          SET k.name = 'DUFF_TOKEN', k.lastupdated = $update_tag
        MERGE (p:SnowflakeComputePool {id: $compute_pool_id})
          SET p.name = 'DONUT_POOL', p.lastupdated = $update_tag
        MERGE (t:SnowflakeTable {id: $table_id})
          SET t.name = 'REACTOR_READINGS', t.lastupdated = $update_tag
        """,
        schema_id=TEST_SCHEMA_ID,
        schema_name=TEST_SCHEMA_NAME,
        warehouse_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "warehouse", "SECTOR_7G_WH"),
        role_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "role", "PLANT_ENGINEER"),
        error_integration_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID, "notification_integration", "MELTDOWN_ALERTS"
        ),
        notify_integration_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID, "notification_integration", "DONUT_NOTIFY"
        ),
        api_integration_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "api_integration", "DUFF_API"),
        eai_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "external_access_integration", "DUFF_EAI"),
        secret_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID,
            "secret",
            sf_fqn(TEST_DATABASE_NAME, TEST_SCHEMA_NAME, "DUFF_TOKEN"),
        ),
        compute_pool_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "compute_pool", "DONUT_POOL"),
        table_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID,
            "table",
            sf_fqn(TEST_DATABASE_NAME, TEST_SCHEMA_NAME, "REACTOR_READINGS"),
        ),
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(cartography.intel.snowflake.tasks, "get", return_value=SNOWFLAKE_TASKS)
def test_sync_snowflake_tasks(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.tasks.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert: every schema was readable, so the caller may run cleanup.
    assert complete is True

    assert check_nodes(
        neo4j_session, "SnowflakeTask", ["qualified_name", "state", "execute_as"]
    ) == {
        ("SPRINGFIELD.NUCLEAR_PLANT.SCRAM_CHECK", "started", "OWNER"),
        ("SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TOPUP", "suspended", "CALLER"),
    }

    # A task is grantable, so it must carry the shared securable label.
    assert (
        sf_id(
            SNOWFLAKE_ACCOUNT_ID,
            "task",
            sf_fqn(TEST_DATABASE_NAME, TEST_SCHEMA_NAME, "SCRAM_CHECK"),
        ),
    ) in check_nodes(neo4j_session, "SnowflakeSecurable", ["id"])

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeTask",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "SCRAM_CHECK"),
        (SNOWFLAKE_ACCOUNT_ID, "COOLANT_TOPUP"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeTask",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "SCRAM_CHECK"),
        (TEST_SCHEMA_NAME, "COOLANT_TOPUP"),
    }

    # Only the scheduled task names a warehouse; the child task is serverless.
    assert check_rels(
        neo4j_session,
        "SnowflakeTask",
        "name",
        "SnowflakeWarehouse",
        "name",
        "USES_WAREHOUSE",
    ) == {("SCRAM_CHECK", "SECTOR_7G_WH")}

    # The DAG edge: the child task points at what triggers it. This only resolves
    # because the node batch is loaded before the edge batch.
    assert check_rels(
        neo4j_session,
        "SnowflakeTask",
        "name",
        "SnowflakeTask",
        "name",
        "PRECEDED_BY",
    ) == {("COOLANT_TOPUP", "SCRAM_CHECK")}

    # Only the owner-rights task borrows its owner's privileges.
    assert check_rels(
        neo4j_session,
        "SnowflakeTask",
        "name",
        "SnowflakeRole",
        "name",
        "ASSUMES",
    ) == {("SCRAM_CHECK", "PLANT_ENGINEER")}

    assert check_rels(
        neo4j_session,
        "SnowflakeTask",
        "name",
        "SnowflakeNotificationIntegration",
        "name",
        "NOTIFIES",
    ) == {
        # Both notification channels are modelled: the error integration and the
        # success integration reference the same kind of resource.
        ("SCRAM_CHECK", "MELTDOWN_ALERTS"),
        ("COOLANT_TOPUP", "DONUT_NOTIFY"),
    }


@patch.object(cartography.intel.snowflake.tasks, "get", return_value=None)
def test_sync_snowflake_tasks_reports_an_unreadable_schema(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.tasks.sync(
        neo4j_session,
        client,
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the sync reports an incomplete walk so the caller skips cleanup and
    # keeps the previously synced tasks.
    assert complete is False
