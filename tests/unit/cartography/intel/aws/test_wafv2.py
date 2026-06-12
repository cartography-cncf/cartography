from unittest.mock import MagicMock

import botocore.exceptions

import tests.data.aws.wafv2 as test_data
from cartography.intel.aws.wafv2 import get_web_acls
from cartography.intel.aws.wafv2 import transform_web_acls


def test_get_web_acls_paginates_with_next_marker() -> None:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.list_web_acls.side_effect = [
        test_data.LIST_WEB_ACLS_PAGES[0],
        test_data.LIST_WEB_ACLS_PAGES[1],
    ]
    mock_client.list_resources_for_web_acl.return_value = (
        test_data.LIST_RESOURCES_FOR_WEB_ACL
    )

    result = get_web_acls(mock_session, "us-east-1", "REGIONAL")

    assert len(result) == 2
    assert result[0]["Name"] == "regional-acl"
    assert result[1]["Name"] == "regional-acl-2"
    # Second list call must pass the NextMarker from the first page
    second_call_kwargs = mock_client.list_web_acls.call_args_list[1][1]
    assert second_call_kwargs["NextMarker"] == "regional-acl"
    # ALB associations are fetched for each regional web ACL
    assert result[0]["AlbArns"] == [test_data.PROTECTED_ALB_ARN]
    resource_calls = mock_client.list_resources_for_web_acl.call_args_list
    assert [c[1] for c in resource_calls] == [
        {
            "WebACLArn": result[0]["ARN"],
            "ResourceType": "APPLICATION_LOAD_BALANCER",
        },
        {
            "WebACLArn": result[1]["ARN"],
            "ResourceType": "APPLICATION_LOAD_BALANCER",
        },
    ]


def test_get_web_acls_stops_on_final_page_with_stale_next_marker() -> None:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    # WAFv2 can return a NextMarker on the final page; an empty page or a
    # marker that makes no progress must terminate pagination.
    mock_client.list_web_acls.side_effect = [
        test_data.LIST_WEB_ACLS_PAGES[0],
        {"WebACLs": [], "NextMarker": "regional-acl"},
    ]
    mock_client.list_resources_for_web_acl.return_value = (
        test_data.LIST_RESOURCES_FOR_WEB_ACL
    )

    result = get_web_acls(mock_session, "us-east-1", "REGIONAL")

    assert len(result) == 1
    assert mock_client.list_web_acls.call_count == 2


def test_get_web_acls_skips_web_acl_deleted_mid_sync() -> None:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.list_web_acls.return_value = {
        "WebACLs": test_data.LIST_WEB_ACLS_PAGES[0]["WebACLs"],
    }
    mock_client.list_resources_for_web_acl.side_effect = (
        botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "WAFNonexistentItemException"}},
            operation_name="ListResourcesForWebACL",
        )
    )

    result = get_web_acls(mock_session, "us-east-1", "REGIONAL")

    assert len(result) == 1
    assert result[0]["AlbArns"] == []


def test_get_web_acls_cloudfront_scope_skips_resource_lookup() -> None:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.list_web_acls.return_value = {
        "WebACLs": test_data.GET_WEB_ACLS_CLOUDFRONT,
    }

    result = get_web_acls(mock_session, "us-east-1", "CLOUDFRONT")

    assert len(result) == 1
    # list_resources_for_web_acl does not support CLOUDFRONT-scoped ACLs;
    # distributions are matched on their web_acl_id property instead.
    mock_client.list_resources_for_web_acl.assert_not_called()


def test_transform_web_acls() -> None:
    transformed = transform_web_acls(test_data.GET_WEB_ACLS_REGIONAL, "REGIONAL")

    assert transformed == [
        {
            "ARN": test_data.REGIONAL_WEB_ACL_ARN,
            "Id": "11111111-1111-1111-1111-111111111111",
            "Name": "regional-acl",
            "Description": "Protects the regional API",
            "Scope": "REGIONAL",
            "AlbArns": [test_data.PROTECTED_ALB_ARN],
        },
    ]


def test_transform_web_acls_defaults_missing_albs_to_empty_list() -> None:
    transformed = transform_web_acls(test_data.GET_WEB_ACLS_CLOUDFRONT, "CLOUDFRONT")

    assert transformed[0]["Scope"] == "CLOUDFRONT"
    assert transformed[0]["AlbArns"] == []
