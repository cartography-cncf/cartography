import copy
from typing import Any
from unittest.mock import MagicMock

import cartography.intel.aws.apigateway
import cartography.intel.aws.cloudfront
import cartography.intel.aws.ec2.load_balancer_v2s
import tests.data.aws.apigateway
import tests.data.aws.cloudfront
import tests.data.aws.ec2.load_balancer_v2s
import tests.data.aws.wafv2 as test_data
from cartography.intel.aws.wafv2 import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789

DISTRIBUTION_ARN = "arn:aws:cloudfront::000000000000:distribution/E7F8G9H0I1J2K3"
STAGE_INFRA_ID = "arn:aws:apigateway:::test-001/Cartography-testing-infra"
STAGE_UNIT_ID = "arn:aws:apigateway:::test-002/Cartography-testing-unit"

# What each region's wafv2 endpoint returns from list_web_acls, by scope.
LIST_WEB_ACLS = {
    ("us-east-1", "REGIONAL"): test_data.LIST_WEB_ACLS_REGIONAL_US_EAST_1,
    ("us-west-2", "REGIONAL"): test_data.LIST_WEB_ACLS_REGIONAL_US_WEST_2,
    ("us-east-1", "CLOUDFRONT"): test_data.LIST_WEB_ACLS_CLOUDFRONT,
    ("us-gov-west-1", "REGIONAL"): test_data.LIST_WEB_ACLS_REGIONAL_US_GOV_WEST_1,
}
LIST_RESOURCES_FOR_WEB_ACL = {
    test_data.ALB_WEB_ACL_ARN: test_data.LIST_RESOURCES_FOR_ALB_WEB_ACL,
}


def _fake_boto3_session(list_web_acls: dict[tuple[str, str], Any]) -> MagicMock:
    """A boto3 session whose wafv2 clients answer from canned API responses."""

    def client(service_name: str, region_name: str, **kwargs: Any) -> MagicMock:
        wafv2 = MagicMock()
        wafv2.list_web_acls.side_effect = lambda Scope: copy.deepcopy(
            list_web_acls.get((region_name, Scope), {"WebACLs": []}),
        )
        wafv2.list_resources_for_web_acl.side_effect = (
            lambda WebACLArn, ResourceType: LIST_RESOURCES_FOR_WEB_ACL.get(
                WebACLArn,
                test_data.LIST_RESOURCES_NONE,
            )
        )
        return wafv2

    session = MagicMock()
    session.client.side_effect = client
    session.region_name = "us-east-1"
    return session


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)


def _load_protected_resources(neo4j_session, distributions: list[dict]) -> None:
    """Load the resources web ACLs protect with their own modules' loaders."""
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        tests.data.aws.ec2.load_balancer_v2s.GET_LOAD_BALANCER_V2_DATA,
        "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.apigateway.load_rest_api_details(
        neo4j_session,
        tests.data.aws.apigateway.GET_REST_API_DETAILS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudfront.load_cloudfront_distributions(
        neo4j_session,
        cartography.intel.aws.cloudfront.transform_cloudfront_distributions(
            distributions,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _sync(neo4j_session, regions: list[str], update_tag: int) -> None:
    sync(
        neo4j_session,
        _fake_boto3_session(LIST_WEB_ACLS),
        regions,
        TEST_ACCOUNT_ID,
        update_tag,
        {"UPDATE_TAG": update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )


def test_sync_loads_web_acls_for_each_scope(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)

    # Act
    _sync(neo4j_session, ["us-east-1", "us-west-2"], TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSWebACL",
        ["arn", "acl_id", "name", "scope", "region"],
    ) == {
        (
            test_data.ALB_WEB_ACL_ARN,
            "11111111-1111-1111-1111-111111111111",
            "alb-acl",
            "REGIONAL",
            "us-east-1",
        ),
        (
            test_data.API_GATEWAY_WEB_ACL_ARN,
            "a1b2c3d4-5678-90ab-cdef-EXAMPLE111",
            "test-cli",
            "REGIONAL",
            "us-west-2",
        ),
        (
            test_data.CLOUDFRONT_WEB_ACL_ARN,
            "abc123",
            "test-acl",
            "CLOUDFRONT",
            "us-east-1",
        ),
    }


def test_sync_lists_cloudfront_web_acls_from_us_east_1_when_not_requested(
    neo4j_session,
):
    # Arrange
    _reset_graph(neo4j_session)

    # Act
    _sync(neo4j_session, ["us-west-2"], TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "AWSWebACL", ["arn", "scope", "region"]) == {
        (test_data.API_GATEWAY_WEB_ACL_ARN, "REGIONAL", "us-west-2"),
        (test_data.CLOUDFRONT_WEB_ACL_ARN, "CLOUDFRONT", "us-east-1"),
    }


def test_sync_skips_cloudfront_web_acls_in_govcloud(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)

    # Act
    _sync(neo4j_session, ["us-gov-west-1"], TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "AWSWebACL", ["arn", "scope"]) == {
        (test_data.GOVCLOUD_WEB_ACL_ARN, "REGIONAL"),
    }


def test_sync_attaches_web_acls_to_their_account(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)

    # Act
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSWebACL",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, test_data.ALB_WEB_ACL_ARN),
        (TEST_ACCOUNT_ID, test_data.CLOUDFRONT_WEB_ACL_ARN),
    }


def test_sync_labels_web_acls_as_network_access_controls(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)

    # Act
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "NetworkAccessControl", ["arn"]) == {
        (test_data.ALB_WEB_ACL_ARN,),
        (test_data.CLOUDFRONT_WEB_ACL_ARN,),
    }


def test_sync_links_web_acl_to_the_load_balancer_it_protects(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)
    _load_protected_resources(
        neo4j_session,
        tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
    )

    # Act
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "AWSLoadBalancerV2",
        "arn",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.ALB_WEB_ACL_ARN, test_data.PROTECTED_ALB_ARN),
    }


def test_sync_links_web_acl_to_api_gateway_stages_that_name_it(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)
    _load_protected_resources(
        neo4j_session,
        tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
    )

    # Act
    _sync(neo4j_session, ["us-west-2"], TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "AWSAPIGatewayStage",
        "id",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.API_GATEWAY_WEB_ACL_ARN, STAGE_INFRA_ID),
        (test_data.API_GATEWAY_WEB_ACL_ARN, STAGE_UNIT_ID),
    }


def test_sync_links_web_acl_to_cloudfront_distributions_that_name_it(
    neo4j_session,
):
    # Arrange
    _reset_graph(neo4j_session)
    _load_protected_resources(
        neo4j_session,
        tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
    )

    # Act
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSWebACL",
        "arn",
        "AWSCloudFrontDistribution",
        "arn",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (test_data.CLOUDFRONT_WEB_ACL_ARN, DISTRIBUTION_ARN),
    }


def test_sync_removes_web_acls_deleted_from_aws(neo4j_session):
    # Arrange
    _reset_graph(neo4j_session)
    _sync(neo4j_session, ["us-east-1", "us-west-2"], TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        _fake_boto3_session(
            {("us-east-1", "CLOUDFRONT"): test_data.LIST_WEB_ACLS_CLOUDFRONT},
        ),
        ["us-east-1", "us-west-2"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSWebACL", ["arn"]) == {
        (test_data.CLOUDFRONT_WEB_ACL_ARN,),
    }


def test_sync_removes_protects_edge_when_distribution_drops_its_web_acl(
    neo4j_session,
):
    # Arrange
    _reset_graph(neo4j_session)
    _load_protected_resources(
        neo4j_session,
        tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA,
    )
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG)
    # The next CloudFront sync sees the distribution without a web ACL; the
    # API returns an empty WebACLId in that case.
    cartography.intel.aws.cloudfront.load_cloudfront_distributions(
        neo4j_session,
        cartography.intel.aws.cloudfront.transform_cloudfront_distributions(
            [
                {
                    **tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA[0],
                    "WebACLId": "",
                },
            ],
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
    )

    # Act
    _sync(neo4j_session, ["us-east-1"], TEST_UPDATE_TAG + 1)

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "AWSWebACL",
            "arn",
            "AWSCloudFrontDistribution",
            "arn",
            "PROTECTS",
            rel_direction_right=True,
        )
        == set()
    )
