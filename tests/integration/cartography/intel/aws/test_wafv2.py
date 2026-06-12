import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.wafv2
import tests.data.aws.wafv2 as test_data
from cartography.intel.aws.wafv2 import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
# Distinct from CLOUDFRONT_SCOPE_REGION so the test catches scope/region mixups
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789

APIGW_STAGE_ARN = "arn:aws:apigateway:::test-api/prod"
CLOUDFRONT_DISTRIBUTION_ARN = (
    f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/EDFDVBD632BHDS5"
)


def _cleanup(neo4j_session):
    neo4j_session.run("MATCH (n:AWSWebACL) DETACH DELETE n")
    neo4j_session.run(
        "MATCH (n) WHERE (n:AWSLoadBalancerV2 AND n.arn = $alb_arn) "
        "OR (n:APIGatewayStage AND n.id = $stage_arn) "
        "OR (n:CloudFrontDistribution AND n.arn = $distribution_arn) "
        "DETACH DELETE n",
        alb_arn=test_data.PROTECTED_ALB_ARN,
        stage_arn=APIGW_STAGE_ARN,
        distribution_arn=CLOUDFRONT_DISTRIBUTION_ARN,
    )


def _seed_protected_resources(neo4j_session):
    neo4j_session.run(
        "MERGE (:AWSLoadBalancerV2 {arn: $arn})",
        arn=test_data.PROTECTED_ALB_ARN,
    )
    neo4j_session.run(
        "MERGE (:APIGatewayStage {id: $id, webaclarn: $webaclarn})",
        id=APIGW_STAGE_ARN,
        webaclarn=test_data.REGIONAL_WEB_ACL_ARN,
    )
    neo4j_session.run(
        "MERGE (:CloudFrontDistribution {arn: $arn, web_acl_id: $web_acl_id})",
        arn=CLOUDFRONT_DISTRIBUTION_ARN,
        web_acl_id=test_data.CLOUDFRONT_WEB_ACL_ARN,
    )


def _mock_get_web_acls(boto3_session, region, scope):
    if scope == "REGIONAL":
        return copy.deepcopy(test_data.GET_WEB_ACLS_REGIONAL)
    return copy.deepcopy(test_data.GET_WEB_ACLS_CLOUDFRONT)


@patch.object(
    cartography.intel.aws.wafv2,
    "get_web_acls",
    side_effect=_mock_get_web_acls,
)
def test_sync_wafv2_web_acls(mock_get_web_acls, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _cleanup(neo4j_session)
    _seed_protected_resources(neo4j_session)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Regional ACLs are fetched per requested region, CLOUDFRONT-scoped ACLs
    # only via us-east-1
    assert [c[0][1:] for c in mock_get_web_acls.call_args_list] == [
        (TEST_REGION, "REGIONAL"),
        ("us-east-1", "CLOUDFRONT"),
    ]

    assert check_nodes(
        neo4j_session,
        "AWSWebACL",
        ["arn", "web_acl_id", "name", "description", "scope", "region"],
    ) == {
        (
            test_data.REGIONAL_WEB_ACL_ARN,
            "11111111-1111-1111-1111-111111111111",
            "regional-acl",
            "Protects the regional API",
            "REGIONAL",
            TEST_REGION,
        ),
        (
            test_data.CLOUDFRONT_WEB_ACL_ARN,
            "22222222-2222-2222-2222-222222222222",
            "cloudfront-acl",
            "Protects the CDN",
            "CLOUDFRONT",
            "us-east-1",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSWebACL",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, test_data.REGIONAL_WEB_ACL_ARN),
        (TEST_ACCOUNT_ID, test_data.CLOUDFRONT_WEB_ACL_ARN),
    }

    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "AWSLoadBalancerV2",
        "arn",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.REGIONAL_WEB_ACL_ARN, test_data.PROTECTED_ALB_ARN),
    }

    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "APIGatewayStage",
        "id",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.REGIONAL_WEB_ACL_ARN, APIGW_STAGE_ARN),
    }

    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "CloudFrontDistribution",
        "arn",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.CLOUDFRONT_WEB_ACL_ARN, CLOUDFRONT_DISTRIBUTION_ARN),
    }


@patch.object(cartography.intel.aws.wafv2, "get_web_acls")
def test_sync_wafv2_cleanup_removes_stale_nodes_and_rels(
    mock_get_web_acls, neo4j_session
):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _cleanup(neo4j_session)
    _seed_protected_resources(neo4j_session)

    # First sync: both ACLs exist and all PROTECTS edges materialize
    mock_get_web_acls.side_effect = _mock_get_web_acls
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Second sync: the regional ACL was deleted in AWS, and the CloudFront
    # distribution no longer has a web ACL associated
    neo4j_session.run(
        "MATCH (d:CloudFrontDistribution {arn: $arn}) SET d.web_acl_id = null",
        arn=CLOUDFRONT_DISTRIBUTION_ARN,
    )
    mock_get_web_acls.side_effect = lambda boto3_session, region, scope: (
        copy.deepcopy(test_data.GET_WEB_ACLS_CLOUDFRONT)
        if scope == "CLOUDFRONT"
        else []
    )
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # The stale regional ACL node is removed, the CloudFront ACL remains
    assert check_nodes(neo4j_session, "AWSWebACL", ["arn"]) == {
        (test_data.CLOUDFRONT_WEB_ACL_ARN,),
    }

    # The stale PROTECTS edge to the distribution is removed even though both
    # nodes still exist
    assert (
        check_rels(
            neo4j_session,
            "AWSWebACL",
            "arn",
            "CloudFrontDistribution",
            "arn",
            "PROTECTS",
            rel_direction_right=True,
        )
        == set()
    )

    # The protected resource nodes are untouched by wafv2 cleanup
    assert (test_data.PROTECTED_ALB_ARN,) in check_nodes(
        neo4j_session,
        "AWSLoadBalancerV2",
        ["arn"],
    )
    assert (CLOUDFRONT_DISTRIBUTION_ARN,) in check_nodes(
        neo4j_session,
        "CloudFrontDistribution",
        ["arn"],
    )


@patch.object(
    cartography.intel.aws.wafv2,
    "get_web_acls",
    return_value=[],
)
def test_sync_wafv2_empty(mock_get_web_acls, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _cleanup(neo4j_session)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "AWSWebACL", ["arn"]) == set()
