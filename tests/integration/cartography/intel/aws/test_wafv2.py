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
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

APIGW_STAGE_ARN = "arn:aws:apigateway:::test-api/prod"
CLOUDFRONT_DISTRIBUTION_ARN = (
    f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/EDFDVBD632BHDS5"
)


def _cleanup(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSWebACL OR n:AWSLoadBalancerV2 OR n:APIGatewayStage "
        "OR n:CloudFrontDistribution DETACH DELETE n",
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

    # Pre-create the nodes that web ACLs attach to
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

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AWSWebACL",
        ["arn", "name", "scope", "region"],
    ) == {
        (
            test_data.REGIONAL_WEB_ACL_ARN,
            "regional-acl",
            "REGIONAL",
            TEST_REGION,
        ),
        (
            test_data.CLOUDFRONT_WEB_ACL_ARN,
            "cloudfront-acl",
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
