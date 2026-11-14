import copy
from unittest.mock import call
from unittest.mock import MagicMock

import botocore.exceptions

import tests.data.aws.wafv2 as test_data
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS
from cartography.intel.aws.wafv2 import get_web_acls
from cartography.intel.aws.wafv2 import transform_web_acls


def _session_returning(client: MagicMock) -> MagicMock:
    session = MagicMock()
    session.client.return_value = client
    return session


def _list_resources_by_resource_type(client: MagicMock) -> None:
    """Answer ListResourcesForWebACL from canned data, per ResourceType."""

    def _list_resources(WebACLArn: str, ResourceType: str) -> dict:
        resources = {
            "APPLICATION_LOAD_BALANCER": test_data.LIST_RESOURCES_FOR_ALB_WEB_ACL,
            "API_GATEWAY": test_data.LIST_RESOURCES_FOR_API_GATEWAY_WEB_ACL,
        }
        return resources[ResourceType]

    client.list_resources_for_web_acl.side_effect = _list_resources


def test_wafv2_syncs_after_the_modules_it_links_to() -> None:
    # Arrange
    order = list(RESOURCE_FUNCTIONS)

    # Act
    wafv2_position = order.index("wafv2")

    # Assert
    # PROTECTS edges match nodes these modules load, so they must run first.
    assert order.index("ec2:load_balancer_v2") < wafv2_position
    assert order.index("apigateway") < wafv2_position
    assert order.index("apigatewayv2") < wafv2_position
    assert order.index("cloudfront") < wafv2_position


def test_get_web_acls_follows_next_marker_until_a_page_is_empty() -> None:
    # Arrange
    pages_by_marker = {
        None: test_data.LIST_WEB_ACLS_FIRST_PAGE,
        "alb-acl": test_data.LIST_WEB_ACLS_LAST_PAGE,
        "test-cli": test_data.LIST_WEB_ACLS_EMPTY_PAGE_WITH_MARKER,
    }

    def _list_web_acls(Scope: str, NextMarker: str | None = None) -> dict:
        return pages_by_marker[NextMarker]

    client = MagicMock()
    client.list_web_acls.side_effect = _list_web_acls

    # Act
    result = get_web_acls(_session_returning(client), "us-east-1", "CLOUDFRONT")

    # Assert
    assert result == [
        test_data.ALB_WEB_ACL_SUMMARY,
        test_data.API_GATEWAY_WEB_ACL_SUMMARY,
    ]


def test_get_web_acls_stops_when_next_marker_makes_no_progress() -> None:
    # Arrange
    client = MagicMock()
    # A third call would raise StopIteration and fail the test.
    client.list_web_acls.side_effect = [
        {"WebACLs": [test_data.ALB_WEB_ACL_SUMMARY], "NextMarker": "same"},
        {"WebACLs": [test_data.API_GATEWAY_WEB_ACL_SUMMARY], "NextMarker": "same"},
    ]

    # Act
    result = get_web_acls(_session_returning(client), "us-east-1", "CLOUDFRONT")

    # Assert
    assert result == [
        test_data.ALB_WEB_ACL_SUMMARY,
        test_data.API_GATEWAY_WEB_ACL_SUMMARY,
    ]


def test_get_web_acls_adds_the_load_balancers_a_regional_web_acl_protects() -> None:
    # Arrange
    client = MagicMock()
    # get_web_acls adds AlbArns and ApiGatewayStageArns to the response it
    # receives, so copy it.
    client.list_web_acls.return_value = copy.deepcopy(
        test_data.LIST_WEB_ACLS_REGIONAL_US_EAST_1
    )
    _list_resources_by_resource_type(client)

    # Act
    result = get_web_acls(_session_returning(client), "us-east-1", "REGIONAL")

    # Assert
    assert result == [
        {
            "Name": "alb-acl",
            "Id": "11111111-1111-1111-1111-111111111111",
            "Description": "Protects the public load balancer",
            "LockToken": "lock-token-1",
            "ARN": test_data.ALB_WEB_ACL_ARN,
            "AlbArns": [test_data.PROTECTED_ALB_ARN],
            "ApiGatewayStageArns": [test_data.PROTECTED_V2_STAGE_ARN],
        },
    ]


def test_get_web_acls_lists_both_resource_types_for_regional_web_acls() -> None:
    # Arrange
    client = MagicMock()
    client.list_web_acls.return_value = copy.deepcopy(
        test_data.LIST_WEB_ACLS_REGIONAL_US_EAST_1
    )
    _list_resources_by_resource_type(client)

    # Act
    get_web_acls(_session_returning(client), "us-east-1", "REGIONAL")

    # Assert
    assert client.list_resources_for_web_acl.call_args_list == [
        call(
            WebACLArn=test_data.ALB_WEB_ACL_ARN,
            ResourceType="APPLICATION_LOAD_BALANCER",
        ),
        call(
            WebACLArn=test_data.ALB_WEB_ACL_ARN,
            ResourceType="API_GATEWAY",
        ),
    ]


def test_get_web_acls_keeps_a_web_acl_deleted_while_listing_its_resources() -> None:
    # Arrange
    client = MagicMock()
    # get_web_acls adds AlbArns to the response it receives, so copy it.
    client.list_web_acls.return_value = copy.deepcopy(
        test_data.LIST_WEB_ACLS_REGIONAL_US_EAST_1
    )
    client.list_resources_for_web_acl.side_effect = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "WAFNonexistentItemException"}},
        operation_name="ListResourcesForWebACL",
    )

    # Act
    result = get_web_acls(_session_returning(client), "us-east-1", "REGIONAL")

    # Assert
    assert result == [
        {
            "Name": "alb-acl",
            "Id": "11111111-1111-1111-1111-111111111111",
            "Description": "Protects the public load balancer",
            "LockToken": "lock-token-1",
            "ARN": test_data.ALB_WEB_ACL_ARN,
            "AlbArns": [],
            "ApiGatewayStageArns": [],
        },
    ]


def test_get_web_acls_does_not_list_resources_for_cloudfront_scope() -> None:
    # Arrange
    client = MagicMock()
    client.list_web_acls.return_value = test_data.LIST_WEB_ACLS_CLOUDFRONT

    # Act
    get_web_acls(_session_returning(client), "us-east-1", "CLOUDFRONT")

    # Assert
    # AWS rejects ListResourcesForWebACL for CloudFront, for both application
    # load balancer and API Gateway stage resource types; distributions are
    # linked through their own web_acl_id instead.
    client.list_resources_for_web_acl.assert_not_called()


def test_transform_web_acls_records_scope_and_protected_resources() -> None:
    # Arrange
    web_acls = [
        {
            **test_data.ALB_WEB_ACL_SUMMARY,
            "AlbArns": [test_data.PROTECTED_ALB_ARN],
            "ApiGatewayStageArns": [test_data.PROTECTED_V2_STAGE_ARN],
        },
    ]

    # Act
    result = transform_web_acls(web_acls, "REGIONAL")

    # Assert
    assert result == [
        {
            "ARN": test_data.ALB_WEB_ACL_ARN,
            "Id": "11111111-1111-1111-1111-111111111111",
            "Name": "alb-acl",
            "Description": "Protects the public load balancer",
            "Scope": "REGIONAL",
            "AlbArns": [test_data.PROTECTED_ALB_ARN],
            "ApiGatewayStageArns": [test_data.PROTECTED_V2_STAGE_ARN],
        },
    ]


def test_transform_web_acls_defaults_protected_resources_to_empty_lists() -> None:
    # Arrange
    web_acls = [test_data.CLOUDFRONT_WEB_ACL_SUMMARY]

    # Act
    result = transform_web_acls(web_acls, "CLOUDFRONT")

    # Assert
    assert result == [
        {
            "ARN": test_data.CLOUDFRONT_WEB_ACL_ARN,
            "Id": "abc123",
            "Name": "test-acl",
            "Description": "Protects the CDN",
            "Scope": "CLOUDFRONT",
            "AlbArns": [],
            "ApiGatewayStageArns": [],
        },
    ]
