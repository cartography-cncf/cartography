import boto3.session
from moto import mock_aws

import cartography.intel.aws.ec2.images
import tests.data.aws.ec2.images

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_images(neo4j_session):
    data = tests.data.aws.ec2.images.DESCRIBE_IMAGES
    cartography.intel.aws.ec2.images.load_images(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "img-01|us-west-1", "img-02|us-west-1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EC2Image) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_images_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test Images
    data = tests.data.aws.ec2.images.DESCRIBE_IMAGES
    cartography.intel.aws.ec2.images.load_images(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (TEST_ACCOUNT_ID, 'img-01|us-west-1'),
        (TEST_ACCOUNT_ID, 'img-02|us-west-1'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EC2Image) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


@mock_aws
def test_get_images():
    boto3_session = boto3.session.Session()
    ec2 = boto3_session.client('ec2', region_name=TEST_REGION)
    image_id = ec2.register_image(Name='test-image')['ImageId']
    image_ids = [image_id, "ami-invalid"]
    images = cartography.intel.aws.ec2.images.get_images(boto3_session, TEST_REGION, image_ids)
    assert isinstance(images, list)
    assert len(images) == 1
    assert images[0]['ImageId'] == image_id
