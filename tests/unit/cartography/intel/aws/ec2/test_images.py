import boto3.session
from moto import mock_aws

import cartography.intel.aws.ec2.images

TEST_REGION = "us-west-1"


@mock_aws
def test_get_images():
    boto3_session = boto3.session.Session()
    ec2 = boto3_session.client("ec2", region_name=TEST_REGION)
    image_id = ec2.register_image(Name="test-image")["ImageId"]
    image_ids = [image_id, "ami-invalid"]
    images = cartography.intel.aws.ec2.images.get_images(
        boto3_session, TEST_REGION, image_ids
    )
    assert isinstance(images, list)
    assert len(images) == 1
    assert images[0]["ImageId"] == image_id
