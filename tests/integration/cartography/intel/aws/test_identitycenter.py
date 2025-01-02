import tests.data.aws.identitycenter
from cartography.intel.aws.identitycenter import load_identity_center_instances
from cartography.intel.aws.identitycenter import load_permission_sets
from cartography.intel.aws.identitycenter import load_sso_users
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = '1234567890'


def test_load_sso_users(neo4j_session):
    """Test loading SSO users into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    users = tests.data.aws.identitycenter.LIST_USERS

    # Load SSO users into the Neo4j session
    load_sso_users(
        neo4j_session,
        users,
        'd-1234567890',
        'us-west-2',
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Use check_nodes to verify that the SSO users are correctly loaded
    check_nodes(neo4j_session, 'AWSSSOUser', ['id', 'external_id'])


def test_load_identity_center_instances(neo4j_session):
    """Test loading Identity Center instances into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    instances = tests.data.aws.identitycenter.LIST_INSTANCES

    # Load Identity Center instances into the Neo4j session
    load_identity_center_instances(
        neo4j_session,
        instances,
        'us-west-2',
        '123456789012',
        TEST_ACCOUNT_ID,
    )

    # Verify that the instances are correctly loaded
    check_nodes(neo4j_session, 'AWSIdentityCenterInstance', ['id', 'identity_store_id'])


def test_load_permission_sets(neo4j_session):
    """Test loading Identity Center permission sets into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    permission_sets = tests.data.aws.identitycenter.LIST_PERMISSION_SETS

    # Load permission sets into the Neo4j session
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Verify that the permission sets are correctly loaded
    check_nodes(neo4j_session, 'AWSPermissionSet', ['id', 'name'])
