from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

from cartography.intel.aws.ec2.images import get_images


@patch('cartography.intel.aws.ec2.images.get_botocore_config')
@patch('cartography.intel.aws.ec2.images.get_ec2_regions')
@patch('boto3.session.Session')
def test_get_images_all_sources(mock_boto3_session, mock_get_ec2_regions, mock_get_botocore_config):
    region = 'us-east-1'
    image_ids = ['ami-55555555', 'ami-12345678', 'ami-87654321']

    mock_client = MagicMock()
    mock_boto3_session.client.return_value = mock_client
    mock_client.describe_images.side_effect = [
        {'Images': [{'ImageId': 'ami-55555555'}]},
        {'Images': [{'ImageId': 'ami-12345678'}]},
        {'Images': [{'ImageId': 'ami-87654321'}]},
    ]

    mock_get_ec2_regions.return_value = ['us-east-1', 'us-west-2']
    mock_get_botocore_config.return_value = {}

    result = get_images(mock_boto3_session, region, image_ids)

    assert len(result) == 3
    assert result[0]['ImageId'] == 'ami-55555555'
    assert result[1]['ImageId'] == 'ami-12345678'
    assert result[2]['ImageId'] == 'ami-87654321'


@patch('cartography.intel.aws.ec2.images.get_botocore_config')
@patch('boto3.session.Session')
def test_get_images_not_found(mock_boto3_session, mock_get_botocore_config):
    region = 'us-west-2'
    image_ids = ['ami-12345678', 'ami-87654321']

    mock_client = MagicMock()
    mock_boto3_session.return_value = mock_client
    mock_client.describe_images.side_effect = ClientError(
        error_response={'Error': {'Code': 'InvalidAMIID.NotFound', 'Message': 'The image id does not exist'}},
        operation_name='DescribeImages',
    )

    mock_get_botocore_config.return_value = {}

    result = get_images(mock_boto3_session, region, image_ids)

    assert result == []


@patch('cartography.intel.aws.ec2.images.get_botocore_config')
@patch('boto3.session.Session')
def test_get_images_no_image_ids(mock_boto3_session, mock_get_botocore_config):
    region = 'us-west-2'
    image_ids = []

    mock_client = MagicMock()
    mock_boto3_session.client.return_value = mock_client
    mock_client.describe_images.side_effect = [
        {'Images': [{'ImageId': 'ami-12345678'}]},
    ]

    mock_get_botocore_config.return_value = {}

    result = get_images(mock_boto3_session, region, image_ids)

    assert len(result) == 1
    assert result[0]['ImageId'] == 'ami-12345678'
