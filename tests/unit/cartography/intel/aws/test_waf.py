from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.waf
from cartography.intel.aws.waf import _list_with_marker
from cartography.intel.aws.waf import sync
from cartography.intel.aws.waf import transform
from tests.data.aws import waf as test_data


def test_list_with_marker_collects_every_page():
    # Arrange
    client = MagicMock()
    client.list_web_acls.side_effect = [
        {"WebACLs": [{"ARN": "first"}], "NextMarker": "page-2"},
        {"WebACLs": [{"ARN": "second"}]},
    ]

    # Act
    result = _list_with_marker(
        client,
        "list_web_acls",
        "WebACLs",
        Scope="REGIONAL",
    )

    # Assert
    assert result == [{"ARN": "first"}, {"ARN": "second"}]


def test_transform_extracts_nested_rule_and_logging_metadata():
    # Arrange
    protected_resources = {
        test_data.REGIONAL_WEB_ACL_ARN: test_data.PROTECTED_RESOURCES,
    }

    # Act
    web_acls, rules = transform(
        test_data.REGIONAL_WEB_ACLS,
        test_data.LOGGING_CONFIGURATIONS,
        protected_resources,
        "us-west-2",
        "REGIONAL",
    )

    # Assert
    assert web_acls[0]["DefaultAction"] == "ALLOW"
    assert web_acls[0]["LoggingEnabled"] is True
    assert web_acls[0]["RedactedFieldTypes"] == ["SingleHeader"]
    assert web_acls[0]["ProtectedLoadBalancerArns"] == [
        test_data.LOAD_BALANCER_ARN,
    ]
    assert web_acls[0]["ProtectedCognitoUserPoolIds"] == ["us-west-2_Example"]
    assert rules[0]["Action"] == "BLOCK"
    assert rules[0]["StatementTypes"] == [
        "RateBasedStatement",
        "ScopeDownStatement",
        "IPSetReferenceStatement",
    ]
    assert rules[0]["ReferencedIPSetArns"] == [
        f"arn:aws:wafv2:us-west-2:{test_data.TEST_ACCOUNT_ID}:regional/ipset/office/ipset-1",
    ]
    assert rules[0]["RateLimits"] == [100]


@patch.object(cartography.intel.aws.waf, "cleanup")
@patch.object(cartography.intel.aws.waf, "get_web_acls", return_value=[])
def test_sync_skips_cleanup_after_incomplete_scan(
    _mock_get_web_acls,
    mock_cleanup,
):
    # Arrange
    neo4j_session = MagicMock()

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        ["us-west-2"],
        test_data.TEST_ACCOUNT_ID,
        123456789,
        {"UPDATE_TAG": 123456789, "AWS_ID": test_data.TEST_ACCOUNT_ID},
    )

    # Assert
    mock_cleanup.assert_not_called()


@patch.object(cartography.intel.aws.waf, "cleanup")
@patch.object(cartography.intel.aws.waf, "get_logging_configurations")
@patch.object(cartography.intel.aws.waf, "get_web_acls")
def test_sync_skips_logging_lookup_when_scope_has_no_web_acls(
    mock_get_web_acls,
    mock_get_logging_configurations,
    mock_cleanup,
):
    # Arrange
    def complete_empty_scan(_session, _region, _scope, scan_status):
        scan_status["complete"] = True
        return []

    mock_get_web_acls.side_effect = complete_empty_scan

    # Act
    sync(
        MagicMock(),
        MagicMock(),
        ["us-west-2"],
        test_data.TEST_ACCOUNT_ID,
        123456789,
        {"UPDATE_TAG": 123456789, "AWS_ID": test_data.TEST_ACCOUNT_ID},
    )

    # Assert
    mock_get_logging_configurations.assert_not_called()
    mock_cleanup.assert_called_once()
