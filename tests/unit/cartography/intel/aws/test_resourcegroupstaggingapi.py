import copy
from unittest.mock import MagicMock

import cartography.intel.aws.resourcegroupstaggingapi as rgta
import tests.data.aws.resourcegroupstaggingapi as test_data


def test_compute_resource_id():
    """
    Test that the id_func function pointer behaves as expected and returns the instanceid from an EC2Instance's ARN.
    """
    tag_mapping = {
        "ResourceARN": "arn:aws:ec2:us-east-1:1234:instance/i-abcd",
        "Tags": [
            {
                "Key": "my_key",
                "Value": "my_value",
            },
        ],
    }
    ec2_short_id = "i-abcd"
    assert ec2_short_id == rgta.compute_resource_id(tag_mapping, "ec2:instance")


def test_get_bucket_name_from_arn():
    arn = "arn:aws:s3:::bucket_name"
    assert "bucket_name" == rgta.get_bucket_name_from_arn(arn)


def test_get_short_id_from_ec2_arn():
    arn = "arn:aws:ec2:us-east-1:test_account:instance/i-1337"
    assert "i-1337" == rgta.get_short_id_from_ec2_arn(arn)


def test_get_short_id_from_elb_arn():
    arn = "arn:aws:elasticloadbalancing:::loadbalancer/foo"
    assert "foo" == rgta.get_short_id_from_elb_arn(arn)


def test_get_short_id_from_lb2_arn():
    arn = "arn:aws:elasticloadbalancing:::loadbalancer/app/foo/abdc123"
    assert "foo" == rgta.get_short_id_from_lb2_arn(arn)


def test_get_resource_type_from_arn():
    assert "ec2:instance" == rgta.get_resource_type_from_arn(
        "arn:aws:ec2:us-east-1:1234:instance/i-01"
    )
    assert "s3" == rgta.get_resource_type_from_arn("arn:aws:s3:::bucket-1")
    assert "elasticloadbalancing:loadbalancer/app" == rgta.get_resource_type_from_arn(
        "arn:aws:elasticloadbalancing:us-east-1:1234:loadbalancer/app/foo/123"
    )


def test_group_tag_data_by_resource_type():
    grouped = rgta._group_tag_data_by_resource_type(
        copy.deepcopy(test_data.GET_RESOURCES_RESPONSE),
        rgta.TAG_RESOURCE_TYPE_MAPPINGS,
    )
    assert len(grouped["ec2:instance"]) == 1
    assert len(grouped["s3"]) == 1


def test_transform_tags():
    get_resources_response = copy.deepcopy(test_data.GET_RESOURCES_RESPONSE)
    assert "resource_id" not in get_resources_response[0]
    rgta.transform_tags(get_resources_response, "ec2:instance")
    assert "resource_id" in get_resources_response[0]


def test_load_tags_empty_data():
    """
    Ensure that the load_tags function returns early if the tag_data is empty
    """
    # Arrange
    mock_neo4j_session = MagicMock()
    resource_type = "ec2:instance"
    region = "us-east-1"
    account_id = "123456789012"
    update_tag = 123456789

    # Act
    rgta.load_tags(
        neo4j_session=mock_neo4j_session,
        tag_data={},
        resource_type=resource_type,
        region=region,
        current_aws_account_id=account_id,
        aws_update_tag=update_tag,
    )

    # Assert
    mock_neo4j_session.execute_write.assert_not_called()


def test_get_tags_does_not_call_iam(mocker):
    """
    get_tags() handles only regional resource types. IAM tags are fetched
    once per sync from sync(), not per region from get_tags().
    """
    role_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.get_role_tags",
    )
    user_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.get_user_tags",
    )
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "ResourceTagMappingList": [
                {"ResourceARN": "arn:aws:s3:::bucket", "Tags": []}
            ]
        },
    ]
    mock_client.get_paginator.return_value = mock_paginator
    mock_session.client.return_value = mock_client

    result = rgta.get_tags(mock_session, ["s3"], "us-east-1")

    assert [item["ResourceARN"] for item in result] == ["arn:aws:s3:::bucket"]
    role_mock.assert_not_called()
    user_mock.assert_not_called()
    mock_paginator.paginate.assert_called_once_with(ResourceTypeFilters=["s3"])


def test_sync_fetches_iam_tags_once_across_regions(mocker):
    """
    IAM is global, so get_role_tags and get_user_tags must be called exactly
    once per sync, regardless of how many regions are synced. IAM tags must
    be loaded with the GLOBAL_REGION marker.
    """
    role_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.get_role_tags",
        return_value=[
            {
                "ResourceARN": "arn:aws:iam::123456789012:role/test-role",
                "Tags": [{"Key": "k", "Value": "v"}],
            }
        ],
    )
    user_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.get_user_tags",
        return_value=[
            {
                "ResourceARN": "arn:aws:iam::123456789012:user/test-user",
                "Tags": [{"Key": "k", "Value": "v"}],
            }
        ],
    )
    get_tags_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.get_tags",
        return_value=[],
    )
    load_tags_mock = mocker.patch(
        "cartography.intel.aws.resourcegroupstaggingapi.load_tags",
    )
    mocker.patch("cartography.intel.aws.resourcegroupstaggingapi.cleanup")

    regions = ["us-east-1", "us-west-2", "eu-west-1"]
    mapping = {
        "iam:role": rgta.TAG_RESOURCE_TYPE_MAPPINGS["iam:role"],
        "iam:user": rgta.TAG_RESOURCE_TYPE_MAPPINGS["iam:user"],
        "s3": rgta.TAG_RESOURCE_TYPE_MAPPINGS["s3"],
    }

    rgta.sync(
        neo4j_session=MagicMock(),
        boto3_session=MagicMock(),
        regions=regions,
        current_aws_account_id="123456789012",
        update_tag=42,
        common_job_parameters={"UPDATE_TAG": 42, "AWS_ID": "123456789012"},
        tag_resource_type_mappings=mapping,
    )

    role_mock.assert_called_once()
    user_mock.assert_called_once()

    # get_tags() is called once per region, never with iam:* in the type list
    assert get_tags_mock.call_count == len(regions)
    for call in get_tags_mock.call_args_list:
        regional_types = (
            call.args[1] if len(call.args) > 1 else call.kwargs["resource_types"]
        )
        assert "iam:role" not in regional_types
        assert "iam:user" not in regional_types

    # IAM resource types are loaded with region="global", not a real region
    iam_load_calls = [
        c
        for c in load_tags_mock.call_args_list
        if c.kwargs["resource_type"] in {"iam:role", "iam:user"}
    ]
    assert len(iam_load_calls) == 2
    for call in iam_load_calls:
        assert call.kwargs["region"] == rgta.GLOBAL_REGION
