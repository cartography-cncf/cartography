from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.waf
from cartography.intel.aws.waf import sync
from tests.data.aws import waf as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _web_acls_for_scope(_session, _region, scope, scan_status):
    scan_status["complete"] = True
    return (
        test_data.CLOUDFRONT_WEB_ACLS
        if scope == "CLOUDFRONT"
        else test_data.REGIONAL_WEB_ACLS
    )


def _logging_for_scope(_session, _region, scope, scan_status):
    scan_status["complete"] = True
    return test_data.LOGGING_CONFIGURATIONS if scope == "REGIONAL" else []


def _protected_resources(_session, _region, _web_acl_arn, scan_status):
    scan_status["complete"] = True
    return test_data.PROTECTED_RESOURCES


@patch.object(
    cartography.intel.aws.waf,
    "get_protected_resources",
    side_effect=_protected_resources,
)
@patch.object(
    cartography.intel.aws.waf,
    "get_logging_configurations",
    side_effect=_logging_for_scope,
)
@patch.object(
    cartography.intel.aws.waf,
    "get_web_acls",
    side_effect=_web_acls_for_scope,
)
def test_sync_waf(
    _mock_get_web_acls,
    _mock_get_logging_configurations,
    _mock_get_protected_resources,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n:AWSWAFWebACL|AWSWAFRule) DETACH DELETE n")
    create_test_account(
        neo4j_session,
        test_data.TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (:AWSLoadBalancerV2 {arn: $arn})",
        arn=test_data.LOAD_BALANCER_ARN,
    )
    neo4j_session.run(
        "MERGE (:AWSCognitoUserPool {id: $id})",
        id="us-west-2_Example",
    )
    neo4j_session.run(
        """
        MATCH (account:AWSAccount {id: $account_id})
        MERGE (stale:AWSWAFWebACL {id: 'stale-acl'})
        SET stale.lastupdated = 1
        MERGE (account)-[:RESOURCE]->(stale)
        MERGE (stale_rule:AWSWAFRule {id: 'stale-rule'})
        SET stale_rule.lastupdated = 1
        MERGE (account)-[:RESOURCE]->(stale_rule)
        MERGE (stale)-[:HAS_RULE]->(stale_rule)
        """,
        account_id=test_data.TEST_ACCOUNT_ID,
    )

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        ["us-west-2"],
        test_data.TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": test_data.TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSWAFWebACL",
        ["arn", "scope", "default_action", "logging_enabled", "_ont_name"],
    ) == {
        (
            test_data.REGIONAL_WEB_ACL_ARN,
            "REGIONAL",
            "ALLOW",
            True,
            "regional-acl",
        ),
        (
            test_data.CLOUDFRONT_WEB_ACL_ARN,
            "CLOUDFRONT",
            "BLOCK",
            False,
            "cloudfront-acl",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "AWSWAFRule",
        ["name", "action", "override_action", "phase"],
    ) == {
        ("rate-limit-login", "BLOCK", None, "regular"),
        ("aws-common-rules", None, "NONE", "regular"),
    }
    assert check_rels(
        neo4j_session,
        "AWSWAFWebACL",
        "arn",
        "AWSWAFRule",
        "name",
        "HAS_RULE",
        rel_direction_right=True,
    ) == {
        (test_data.REGIONAL_WEB_ACL_ARN, "rate-limit-login"),
        (test_data.CLOUDFRONT_WEB_ACL_ARN, "aws-common-rules"),
    }
    assert check_rels(
        neo4j_session,
        "AWSWAFWebACL",
        "arn",
        "AWSLoadBalancerV2",
        "arn",
        "PROTECTS",
        rel_direction_right=True,
    ) == {(test_data.REGIONAL_WEB_ACL_ARN, test_data.LOAD_BALANCER_ARN)}
    assert check_rels(
        neo4j_session,
        "AWSWAFWebACL",
        "arn",
        "AWSCognitoUserPool",
        "id",
        "PROTECTS",
        rel_direction_right=True,
    ) == {(test_data.REGIONAL_WEB_ACL_ARN, "us-west-2_Example")}
    assert (
        neo4j_session.run(
            "MATCH (n) WHERE n.id IN ['stale-acl', 'stale-rule'] RETURN count(n) AS count",
        ).single()["count"]
        == 0
    )

    # Act - keep the ACL but remove its regional associations.
    def no_protected_resources(_session, _region, _web_acl_arn, scan_status):
        scan_status["complete"] = True
        return []

    _mock_get_protected_resources.side_effect = no_protected_resources
    sync(
        neo4j_session,
        MagicMock(),
        ["us-west-2"],
        test_data.TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": test_data.TEST_ACCOUNT_ID},
    )

    # Assert - stale PROTECTS relationships are removed while the ACL remains.
    assert (
        check_rels(
            neo4j_session,
            "AWSWAFWebACL",
            "arn",
            "AWSLoadBalancerV2",
            "arn",
            "PROTECTS",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.aws.waf,
    "get_protected_resources",
    side_effect=_protected_resources,
)
@patch.object(
    cartography.intel.aws.waf,
    "get_logging_configurations",
    side_effect=_logging_for_scope,
)
@patch.object(cartography.intel.aws.waf, "get_web_acls")
def test_sync_waf_preserves_previous_data_after_incomplete_scan(
    mock_get_web_acls,
    _mock_get_logging_configurations,
    _mock_get_protected_resources,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n:AWSWAFWebACL|AWSWAFRule) DETACH DELETE n")
    create_test_account(
        neo4j_session,
        test_data.TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MATCH (account:AWSAccount {id: $account_id})
        MERGE (account)-[:RESOURCE]->(acl:AWSWAFWebACL {id: 'previous-acl'})
        SET acl.lastupdated = $previous_update_tag
        """,
        account_id=test_data.TEST_ACCOUNT_ID,
        previous_update_tag=TEST_UPDATE_TAG - 1,
    )

    def one_region_fails(_session, region, scope, scan_status):
        if region == "us-east-2":
            return []
        scan_status["complete"] = True
        if scope == "REGIONAL":
            return test_data.REGIONAL_WEB_ACLS
        return []

    mock_get_web_acls.side_effect = one_region_fails

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        ["us-west-2", "us-east-2"],
        test_data.TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": test_data.TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSWAFWebACL", ["id"]) >= {
        ("previous-acl",),
        (test_data.REGIONAL_WEB_ACLS[0]["ARN"],),
    }
