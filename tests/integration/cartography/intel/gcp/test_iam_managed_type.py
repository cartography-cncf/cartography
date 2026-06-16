import cartography.intel.gcp.iam
import tests.data.gcp.iam
from tests.integration.util import check_nodes

TEST_PROJECT_NUMBER = '000000000000'
TEST_ORG_ID = 'organizations/123'
TEST_UPDATE_TAG = 123456789


def test_roles_managed_type(neo4j_session):
    # Predefined roles are named "roles/*"; project/org custom roles are namespaced.
    roles = [
        {'id': 'organizations/123/roles/viewer', 'name': 'roles/viewer', 'title': 'Viewer'},
        {'id': 'projects/project123/roles/myrole', 'name': 'projects/project123/roles/myrole', 'title': 'My Role'},
    ]
    cartography.intel.gcp.iam.load_project_roles(neo4j_session, roles, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    assert check_nodes(neo4j_session, 'GCPRole', ['name', 'managed_type']) >= {
        ('roles/viewer', 'predefined'),
        ('projects/project123/roles/myrole', 'custom'),
    }


def test_service_accounts_managed_type(neo4j_session):
    accounts = [
        {
            'name': 'projects/p/serviceAccounts/p@appspot.gserviceaccount.com',
            'email': 'p@appspot.gserviceaccount.com',
            'uniqueId': 'sa-predefined',
            'displayName': 'appspot',
        },
        {
            'name': 'projects/p/serviceAccounts/my-sa@p.iam.gserviceaccount.com',
            'email': 'my-sa@p.iam.gserviceaccount.com',
            'uniqueId': 'sa-custom',
            'displayName': 'my-sa',
        },
    ]
    accounts = cartography.intel.gcp.iam.transform_service_accounts(accounts, 'p')
    cartography.intel.gcp.iam.load_service_accounts(neo4j_session, accounts, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    assert check_nodes(neo4j_session, 'GCPServiceAccount', ['serviceaccountid', 'managed_type']) >= {
        ('sa-predefined', 'predefined'),
        ('sa-custom', 'custom'),
    }


def test_service_account_keys_managed_type(neo4j_session):
    # SYSTEM_MANAGED keys are Google-managed; USER_MANAGED keys are customer-created.
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNT_KEYS
    cartography.intel.gcp.iam.load_service_account_keys(neo4j_session, data, None, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    assert check_nodes(neo4j_session, 'GCPServiceAccountKey', ['id', 'managed_type']) == {
        ('abc@gmail.com/key123', 'custom'),       # USER_MANAGED
        ('defg@gmail.com/key456', 'predefined'),  # SYSTEM_MANAGED
    }


def test_api_keys_managed_type(neo4j_session):
    data = tests.data.gcp.iam.API_KEY
    cartography.intel.gcp.iam.load_api_keys(neo4j_session, data, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    managed_types = {mt for (_, mt) in check_nodes(neo4j_session, 'GCPAPIKey', ['id', 'managed_type'])}
    assert managed_types == {'custom'}
