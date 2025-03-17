from cartography.intel.aws.ec2.launch_templates import load_launch_template_versions
from cartography.intel.aws.ec2.launch_templates import load_launch_templates
from cartography.intel.aws.ec2.launch_templates import transform_launch_template_versions
from cartography.intel.aws.ec2.launch_templates import transform_launch_templates
from tests.data.aws.ec2.launch_templates import GET_LAUNCH_TEMPLATE_VERSIONS
from tests.data.aws.ec2.launch_templates import GET_LAUNCH_TEMPLATES
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_launch_templates(neo4j_session, *args):
    # Arrange: an AWSAccount must exist
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    # Act: transform and load the launch templates
    templates = transform_launch_templates(GET_LAUNCH_TEMPLATES)
    load_launch_templates(
        neo4j_session,
        templates,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_templates = {
        (
            "lt-00000000000000000",
            "eks-00000000-0000-0000-0000-000000000000",
            "1634020072",
            1,
        ),
    }
    # Assert that the launch templates exist
    templates = neo4j_session.run(
        """
        MATCH (n:LaunchTemplate)<-[:RESOURCE]-(:AWSAccount)
        return n.id, n.name, n.create_time, n.latest_version_number
        """,
    )
    actual_templates = {
        (
            n['n.id'],
            n['n.name'],
            n['n.create_time'],
            n['n.latest_version_number'],
        )
        for n in templates
    }
    assert actual_templates == expected_templates

    # Act: transform and load the launch template versions
    versions = transform_launch_template_versions(GET_LAUNCH_TEMPLATE_VERSIONS)
    load_launch_template_versions(
        neo4j_session,
        versions,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Assert that the launch templates are loaded as expected
    expected_versions = {
        (
            "lt-00000000000000000-1",
            "eks-00000000-0000-0000-0000-000000000000",
            1,
            "1634020072",
            "ami-00000000000000000",
        ),
    }
    versions = neo4j_session.run(
        """
        MATCH (:LaunchTemplate)-[:VERSION]->(n:LaunchTemplateVersion)
        return n.id, n.name, n.version_number, n.create_time, n.image_id
        """,
    )
    actual_versions = {
        (
            n['n.id'],
            n['n.name'],
            n['n.version_number'],
            n['n.create_time'],
            n['n.image_id'],
        )
        for n in versions
    }
    assert actual_versions == expected_versions

    # Assert that the Launch Template version is attached to the AWS account
    assert check_rels(
        neo4j_session,
        'LaunchTemplateVersion',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('lt-00000000000000000-1', TEST_ACCOUNT_ID),
    }
