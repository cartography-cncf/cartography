import boto3.session
from moto import mock_aws

import cartography.intel.aws.ec2.images

TEST_REGION = "us-west-1"


@mock_aws
def test_get_images():
    boto3_session = boto3.session.Session()
    ec2 = boto3_session.client("ec2", region_name=TEST_REGION)
    image_id = ec2.register_image(Name="test-image")["ImageId"]
    # Not self-owned, so it can only come back through the per-id lookup.
    public_image_id = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    image_ids = [image_id, public_image_id, "ami-invalid"]
    images = cartography.intel.aws.ec2.images.get_images(
        boto3_session, TEST_REGION, image_ids
    )
    assert isinstance(images, list)
    assert sorted(image["ImageId"] for image in images) == sorted(
        [image_id, public_image_id]
    )
