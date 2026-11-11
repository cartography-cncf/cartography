from unittest.mock import Mock
from unittest.mock import patch

import pytest
from tencentcloud.common.credential import Credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)

from cartography.intel.tencentcloud import util


def _client(*responses: dict) -> Mock:
    client = Mock()
    client.call_json.side_effect = [{"Response": response} for response in responses]
    return client


def test_paginate_offset_reads_every_page_until_total_count():
    # Arrange
    client = _client(
        {
            "InstanceSet": [{"InstanceId": "ins-1"}, {"InstanceId": "ins-2"}],
            "TotalCount": 3,
        },
        {"InstanceSet": [{"InstanceId": "ins-3"}], "TotalCount": 3},
    )

    # Act
    items = util.paginate_offset(client, "DescribeInstances", "InstanceSet", limit=2)

    # Assert
    assert items == [
        {"InstanceId": "ins-1"},
        {"InstanceId": "ins-2"},
        {"InstanceId": "ins-3"},
    ]


def test_paginate_offset_sends_string_offsets_for_vpc_style_actions():
    # Arrange
    client = _client({"VpcSet": [], "TotalCount": 0})

    # Act
    util.paginate_offset(client, "DescribeVpcs", "VpcSet", string_paging=True)

    # Assert
    client.call_json.assert_called_once_with(
        "DescribeVpcs",
        {"Offset": "0", "Limit": "100"},
    )


def test_paginate_offset_treats_a_null_result_set_as_empty():
    # Arrange
    client = _client({"DiskSet": None, "TotalCount": 0})

    # Act
    items = util.paginate_offset(client, "DescribeDisks", "DiskSet")

    # Assert
    assert items == []


def test_paginate_page_reads_every_page_until_total_num():
    # Arrange
    client = _client(
        {"List": [{"RoleId": "1"}], "TotalNum": 2},
        {"List": [{"RoleId": "2"}], "TotalNum": 2},
    )

    # Act
    items = util.paginate_page(client, "DescribeRoleList", "List", rp=1)

    # Assert
    assert items == [{"RoleId": "1"}, {"RoleId": "2"}]


def test_get_regions_returns_only_available_regions():
    # Arrange
    client = _client(
        {
            "TotalCount": 3,
            "RegionSet": [
                {"Region": "ap-singapore", "RegionState": "AVAILABLE"},
                {"Region": "ap-mumbai", "RegionState": "UNAVAILABLE"},
                {"Region": "ap-guangzhou", "RegionState": "AVAILABLE"},
            ],
        },
    )

    # Act
    with patch.object(util, "build_client", return_value=client):
        regions = util.get_regions(Credential("AKIDtest", "secret"))

    # Assert
    assert regions == ["ap-guangzhou", "ap-singapore"]


def test_get_in_region_skips_a_region_where_the_product_is_unavailable():
    # Arrange
    def fetch(client):
        raise TencentCloudSDKException("UnsupportedRegion", "not supported", "req-1")

    # Act
    items = util.get_in_region(
        Credential("AKIDtest", "secret"),
        "clb",
        "ap-singapore",
        fetch,
    )

    # Assert
    assert items == []


def test_get_in_region_propagates_permission_errors():
    # Arrange
    def fetch(client):
        raise TencentCloudSDKException(
            "AuthFailure.UnauthorizedOperation",
            "not authorized",
            "req-1",
        )

    # Act and assert
    with pytest.raises(TencentCloudSDKException):
        util.get_in_region(
            Credential("AKIDtest", "secret"),
            "cvm",
            "ap-guangzhou",
            fetch,
        )


def test_format_tags_flattens_key_value_pairs():
    # Act
    tags = util.format_tags(
        [{"TagKey": "env", "TagValue": "prod"}],
        key_field="TagKey",
        value_field="TagValue",
    )

    # Assert
    assert tags == ["env:prod"]
