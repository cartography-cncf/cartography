from unittest.mock import patch

import cartography.intel.snowflake.notification_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.notification_integrations import (
    SNOWFLAKE_NOTIFICATION_INTEGRATIONS,
)
from tests.data.snowflake.notification_integrations import (
    SNOWFLAKE_NOTIFICATION_ROLE_ARN,
)
from tests.data.snowflake.notification_integrations import (
    SNOWFLAKE_NOTIFICATION_TOPIC_ARN,
)
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

REACTOR_ALERT_SNS_ID = "SPRINGFIELD.NUCLEAR/notification_integration/REACTOR_ALERT_SNS"
DONUT_PUBSUB_ID = "SPRINGFIELD.NUCLEAR/notification_integration/DONUT_PUBSUB"
MOE_EMAIL_ID = "SPRINGFIELD.NUCLEAR/notification_integration/MOE_EMAIL"


@patch.object(
    cartography.intel.snowflake.notification_integrations,
    "get",
    return_value=SNOWFLAKE_NOTIFICATION_INTEGRATIONS,
)
def test_sync_snowflake_notification_integrations(mock_get, neo4j_session):
    # Arrange: the SNS topic and the IAM role that publishes to it belong to the aws
    # module, so seed both the way a real graph would already have them.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (t:AWSSNSTopic{arn: $topic}) SET t.lastupdated = $tag "
        "MERGE (p:AWSPrincipal{arn: $role}) SET p.lastupdated = $tag",
        topic=SNOWFLAKE_NOTIFICATION_TOPIC_ARN,
        role=SNOWFLAKE_NOTIFICATION_ROLE_ARN,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.notification_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the notification_hook sub-object is flattened, so the transport and its
    # per-cloud coordinates sit on the node.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeNotificationIntegration",
        [
            "id",
            "name",
            "enabled",
            "notification_hook_type",
            "aws_sns_topic_arn",
            "gcp_pubsub_topic_name",
        ],
    ) == {
        (
            REACTOR_ALERT_SNS_ID,
            "REACTOR_ALERT_SNS",
            True,
            "QUEUE_AWS_SNS_OUTBOUND",
            SNOWFLAKE_NOTIFICATION_TOPIC_ARN,
            None,
        ),
        (
            DONUT_PUBSUB_ID,
            "DONUT_PUBSUB",
            True,
            "QUEUE_GCP_PUBSUB",
            None,
            "projects/springfield/topics/donut-events",
        ),
        (MOE_EMAIL_ID, "MOE_EMAIL", False, "EMAIL", None, None),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeNotificationIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (REACTOR_ALERT_SNS_ID, SNOWFLAKE_ACCOUNT_ID),
        (DONUT_PUBSUB_ID, SNOWFLAKE_ACCOUNT_ID),
        (MOE_EMAIL_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The cross-cloud payoff: the integration is joined both to the topic it publishes
    # to and to the IAM role it assumes to do so.
    assert check_rels(
        neo4j_session,
        "SnowflakeNotificationIntegration",
        "id",
        "AWSSNSTopic",
        "arn",
        "NOTIFIES",
        rel_direction_right=True,
    ) == {(REACTOR_ALERT_SNS_ID, SNOWFLAKE_NOTIFICATION_TOPIC_ARN)}
    assert check_rels(
        neo4j_session,
        "SnowflakeNotificationIntegration",
        "id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {(REACTOR_ALERT_SNS_ID, SNOWFLAKE_NOTIFICATION_ROLE_ARN)}
