import cartography.intel.aws.config
import tests.data.aws.config

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_configuration_recorders(neo4j_session, *args):
    """
    Ensure that expected configuration recorders get loaded with their key fields.
    """
    data = tests.data.aws.config.LIST_CONFIGURATION_RECORDERS
    cartography.intel.aws.config.load_configuration_recorders(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "default:000000000000:us-east-1",
            "default",
            True,
            True,
            "us-east-1",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSConfigurationRecorder)
        RETURN n.id, n.name, n.recording_group_all_supported,
        n.recording_group_include_global_resource_types, n.region
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.recording_group_all_supported"],
            n["n.recording_group_include_global_resource_types"],
            n["n.region"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_delivery_channels(neo4j_session, *args):
    """
    Ensure that expected delivery channels get loaded with their key fields.
    """
    data = tests.data.aws.config.LIST_DELIVERY_CHANNELS
    cartography.intel.aws.config.load_delivery_channels(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "default:000000000000:us-east-1",
            "default",
            "test-bucket",
            "us-east-1",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSConfigDeliveryChannel)
        RETURN n.id, n.name, n.s3_bucket_name, n.region
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.name"],
            n["n.s3_bucket_name"],
            n["n.region"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_config_rules(neo4j_session, *args):
    """
    Ensure that expected delivery channels get loaded with their key fields.
    """
    data = tests.data.aws.config.LIST_CONFIG_RULES
    cartography.intel.aws.config.load_config_rules(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:config:us-east-1:000000000000:config-rule/aws-service-rule/securityhub.amazonaws.com/config-rule-magmce",  # noqa:E501
            "arn:aws:config:us-east-1:000000000000:config-rule/aws-service-rule/securityhub.amazonaws.com/config-rule-magmce",  # noqa:E501
            "securityhub-alb-http-drop-invalid-header-enabled-9d3e1985",
            "Test description",
            "AWS",
            "ALB_HTTP_DROP_INVALID_HEADER_ENABLED",
            tuple(
                [
                    "{'EventSource': 'aws.config', 'MessageType': 'ConfigurationItemChangeNotification'}",
                ],
            ),
            "securityhub.amazonaws.com",
            "us-east-1",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSConfigRule)
        RETURN n.id, n.arn, n.name, n.description, n.source_owner, n.source_identifier,
        n.source_details, n.created_by, n.region
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.arn"],
            n["n.name"],
            n["n.description"],
            n["n.source_owner"],
            n["n.source_identifier"],
            tuple(n["n.source_details"]),
            n["n.created_by"],
            n["n.region"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
