from copy import deepcopy

import cartography.intel.gcp.cloud_sql_instance
from tests.data.gcp.cloud_sql import MOCK_INSTANCES

TEST_PROJECT_ID = "test-project"


def test_transform_sql_instances_extracts_audit_logging_flags():
    instances = cartography.intel.gcp.cloud_sql_instance.transform_sql_instances(
        MOCK_INSTANCES["items"],
        TEST_PROJECT_ID,
    )

    instance = instances[0]
    assert instance["flag_cloudsql_enable_pgaudit"] == "on"
    assert instance["flag_log_checkpoints"] == "on"
    assert instance["flag_log_connections"] == "on"
    assert instance["flag_log_disconnections"] == "on"
    assert instance["flag_log_lock_waits"] == "on"


def test_transform_sql_instances_handles_missing_database_flags():
    raw_instances = deepcopy(MOCK_INSTANCES["items"])
    raw_instances[0]["settings"].pop("databaseFlags")

    instances = cartography.intel.gcp.cloud_sql_instance.transform_sql_instances(
        raw_instances,
        TEST_PROJECT_ID,
    )

    instance = instances[0]
    assert instance["database_flags"] is None
    assert instance["flag_cloudsql_enable_pgaudit"] is None
    assert instance["flag_log_checkpoints"] is None
    assert instance["flag_log_connections"] is None
    assert instance["flag_log_disconnections"] is None
    assert instance["flag_log_lock_waits"] is None


def test_transform_sql_instances_handles_empty_database_flags():
    raw_instances = deepcopy(MOCK_INSTANCES["items"])
    raw_instances[0]["settings"]["databaseFlags"] = []

    instances = cartography.intel.gcp.cloud_sql_instance.transform_sql_instances(
        raw_instances,
        TEST_PROJECT_ID,
    )

    instance = instances[0]
    assert instance["database_flags"] is None
    assert instance["flag_cloudsql_enable_pgaudit"] is None
    assert instance["flag_log_checkpoints"] is None
    assert instance["flag_log_connections"] is None
    assert instance["flag_log_disconnections"] is None
    assert instance["flag_log_lock_waits"] is None
