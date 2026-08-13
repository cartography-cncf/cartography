from unittest.mock import patch

import cartography.intel.snowflake.pipes
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.pipes import SNOWFLAKE_PIPES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_tasks import (
    seed_schema_level_dependencies,
)
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMA_NAME
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:000000000000:donut-deliveries"


def _seed_sns_topic(neo4j_session) -> None:
    """Seed the SNS topic the aws module owns, so the cross-cloud edge can match."""
    neo4j_session.run(
        """
        MERGE (t:AWSSNSTopic {id: $arn})
        SET t.arn = $arn, t.lastupdated = $update_tag
        """,
        arn=TEST_SNS_TOPIC_ARN,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(cartography.intel.snowflake.pipes, "get", return_value=SNOWFLAKE_PIPES)
def test_sync_snowflake_pipes(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    _seed_sns_topic(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.pipes.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True

    assert check_nodes(
        neo4j_session, "SnowflakePipe", ["name", "auto_ingest", "invalid_reason"]
    ) == {
        ("DONUT_DELIVERY_PIPE", True, None),
        ("SQUISHEE_PIPE", False, "Target table SQUISHEE_SALES was dropped"),
    }

    # A pipe that reports no `definition` still has its COPY statement, under the
    # `copy_statement` name.
    assert check_nodes(neo4j_session, "SnowflakePipe", ["name", "definition"]) == {
        ("DONUT_DELIVERY_PIPE", "COPY INTO DONUT_DELIVERIES FROM @DONUT_STAGE"),
        ("SQUISHEE_PIPE", "COPY INTO SQUISHEE_SALES FROM @KWIK_E_STAGE"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakePipe",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "DONUT_DELIVERY_PIPE"),
        (SNOWFLAKE_ACCOUNT_ID, "SQUISHEE_PIPE"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakePipe",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "DONUT_DELIVERY_PIPE"),
        (TEST_SCHEMA_NAME, "SQUISHEE_PIPE"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakePipe",
        "name",
        "SnowflakeNotificationIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("DONUT_DELIVERY_PIPE", "DONUT_NOTIFY")}

    # The cross-cloud edge: the pipe is driven by a topic the aws module ingested,
    # matched on the topic ARN Snowflake reports.
    #
    # The edge runs topic -> pipe, not pipe -> topic. NOTIFIES means the source sends
    # notifications to the target everywhere in the codebase, and an auto-ingest pipe
    # is the recipient: the topic is what tells it a file has arrived.
    assert check_rels(
        neo4j_session,
        "SnowflakePipe",
        "name",
        "AWSSNSTopic",
        "arn",
        "NOTIFIES",
        rel_direction_right=False,
    ) == {("DONUT_DELIVERY_PIPE", TEST_SNS_TOPIC_ARN)}
