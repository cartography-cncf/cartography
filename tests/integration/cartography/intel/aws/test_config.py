from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.config
from tests.data.aws.config import LIST_CONFIG_RULES
from tests.data.aws.config import LIST_CONFIGURATION_RECORDERS
from tests.data.aws.config import LIST_DELIVERY_CHANNELS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.config, "get_config_rules", return_value=LIST_CONFIG_RULES
)
@patch.object(
    cartography.intel.aws.config,
    "get_delivery_channels",
    return_value=LIST_DELIVERY_CHANNELS,
)
@patch.object(
    cartography.intel.aws.config,
    "get_configuration_recorders",
    return_value=LIST_CONFIGURATION_RECORDERS,
)
def test_sync_config(mock_recorders, mock_channels, mock_rules, neo4j_session):
    """
    Ensure that sync() creates AWSConfigurationRecorder, AWSConfigDeliveryChannel, and AWSConfigRule nodes.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.config.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify AWSConfigurationRecorder nodes
    assert check_nodes(
        neo4j_session,
        "AWSConfigurationRecorder",
        [
            "id",
            "name",
            "recording_group_all_supported",
            "recording_group_include_global_resource_types",
            "region",
        ],
    ) == {
        (
            "default:000000000000:us-east-1",
            "default",
            True,
            True,
            "us-east-1",
        ),
    }

    # Verify AWSConfigDeliveryChannel nodes
    assert check_nodes(
        neo4j_session,
        "AWSConfigDeliveryChannel",
        ["id", "name", "s3_bucket_name", "region"],
    ) == {
        (
            "default:000000000000:us-east-1",
            "default",
            "test-bucket",
            "us-east-1",
        ),
    }

    # Verify AWSConfigRule nodes
    assert check_nodes(
        neo4j_session,
        "AWSConfigRule",
        [
            "id",
            "name",
            "description",
            "source_owner",
            "source_identifier",
            "created_by",
            "region",
        ],
    ) == {
        (
            "arn:aws:config:us-east-1:000000000000:config-rule/aws-service-rule/securityhub.amazonaws.com/config-rule-magmce",  # noqa: E501
            "securityhub-alb-http-drop-invalid-header-enabled-9d3e1985",
            "Test description",
            "AWS",
            "ALB_HTTP_DROP_INVALID_HEADER_ENABLED",
            "securityhub.amazonaws.com",
            "us-east-1",
        ),
    }

    # Verify source_details separately — it's a list property which is unhashable inside check_nodes()
    result = neo4j_session.run("MATCH (n:AWSConfigRule) RETURN n.source_details")
    records = list(result)
    assert len(records) == 1
    assert records[0]["n.source_details"] == [
        "{'EventSource': 'aws.config', 'MessageType': 'ConfigurationItemChangeNotification'}",
    ]
