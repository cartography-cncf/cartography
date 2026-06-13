from cartography.intel.azure import iam
from tests.data.azure.iam import DESCRIBE_APPLICATIONS
from tests.data.azure.iam import DESCRIBE_DOMAINS
from tests.data.azure.iam import DESCRIBE_GROUPS
from tests.data.azure.iam import DESCRIBE_ROLES
from tests.data.azure.iam import DESCRIBE_SERVICE_ACCOUNTS
from tests.data.azure.iam import DESCRIBE_USERS
from tests.integration.util import check_nodes

TEST_TENANT_ID = '00-00-00-00'
TEST_UPDATE_TAG = 123456789


def test_load_users(neo4j_session):
    iam.load_tenant_users(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_USERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "gdvsd43562",
        "gdvsd43562we34",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureUser) RETURN r.object_id;
        """, )
    actual_nodes = {n['r.object_id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_user_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_users(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_USERS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            '00-00-00-00',
            'user-123',
        ),
        (
            '00-00-00-00',
            'user-321',
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureTenant)-[:RESOURCE]->(n2:AzureUser) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_groups(neo4j_session):
    iam.load_tenant_groups(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "45b7d2e7-b882-4a80-ba97-10b7a63b8fa4",
        "d7797254-3084-44d0-99c9-a3b5ab149538",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureGroup) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_group_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_groups(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_TENANT_ID,
            "45b7d2e7-b882-4a80-ba97-10b7a63b8fa4",
        ),
        (
            TEST_TENANT_ID,
            "d7797254-3084-44d0-99c9-a3b5ab149538",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureTenant)-[:RESOURCE]->(n2:AzureGroup) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_applications(neo4j_session):
    iam.load_tenant_applications(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_APPLICATIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureApplication) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_application_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_applications(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_APPLICATIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_TENANT_ID,
            "00000000-0000-0000-0000-000000000001",
        ),
        (
            TEST_TENANT_ID,
            "00000000-0000-0000-0000-000000000002",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureTenant)-[:RESOURCE]->(n2:AzureApplication) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_service_accounts(neo4j_session):
    iam.load_tenant_service_accounts(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_SERVICE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "86823hkhjhd",
        "hvhg575757g",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureServiceAccount) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_service_account_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_service_accounts(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_SERVICE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_TENANT_ID,
            "86823hkhjhd",
        ),
        (
            TEST_TENANT_ID,
            "hvhg575757g",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureTenant)-[:RESOURCE]->(n2:AzureServiceAccount) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_domains(neo4j_session):
    iam.load_tenant_domains(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_DOMAINS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "contoso1.com",
        "contoso2.com",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureDomain) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_domain_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_domains(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_DOMAINS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_TENANT_ID,
            "contoso1.com",
        ),
        (
            TEST_TENANT_ID,
            "contoso2.com",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureTenant)-[:RESOURCE]->(n2:AzureDomain) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_roles(neo4j_session):
    iam.load_roles(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_ROLES,
        TEST_UPDATE_TAG,
        SUBSCRIPTION_ID=None,
    )

    expected_nodes = {
        "97254c67-852d-61c20eb66ffc",
        "97254c67-852d-61c20eb66ffcsdds",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureRole) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_users_managed_type(neo4j_session):
    iam.load_tenant_users(neo4j_session, TEST_TENANT_ID, DESCRIBE_USERS, TEST_UPDATE_TAG)
    managed_types = {mt for (_, mt) in check_nodes(neo4j_session, 'AzureUser', ['id', 'managed_type'])}
    assert managed_types == {'custom'}


def test_load_groups_managed_type(neo4j_session):
    iam.load_tenant_groups(neo4j_session, TEST_TENANT_ID, DESCRIBE_GROUPS, TEST_UPDATE_TAG)
    managed_types = {mt for (_, mt) in check_nodes(neo4j_session, 'AzureGroup', ['id', 'managed_type'])}
    assert managed_types == {'custom'}


def test_load_applications_managed_type(neo4j_session):
    iam.load_tenant_applications(neo4j_session, TEST_TENANT_ID, DESCRIBE_APPLICATIONS, TEST_UPDATE_TAG)
    managed_types = {mt for (_, mt) in check_nodes(neo4j_session, 'AzureApplication', ['id', 'managed_type'])}
    assert managed_types == {'custom'}


def test_load_domains_managed_type(neo4j_session):
    iam.load_tenant_domains(neo4j_session, TEST_TENANT_ID, DESCRIBE_DOMAINS, TEST_UPDATE_TAG)
    managed_types = {mt for (_, mt) in check_nodes(neo4j_session, 'AzureDomain', ['id', 'managed_type'])}
    assert managed_types == {'custom'}


def test_load_service_accounts_managed_type(neo4j_session):
    # A Microsoft first-party service principal (predefined) and an ordinary customer one (custom).
    service_accounts = [
        {
            "id": "tenants/00-00-00-00/ServiceAccounts/ms-first-party",
            "object_id": "ms-first-party",
            "display_name": "Microsoft First Party",
            "app_owner_organization_id": iam.AZURE_MICROSOFT_TENANT_ID,
        },
        {
            "id": "tenants/00-00-00-00/ServiceAccounts/customer-sp",
            "object_id": "customer-sp",
            "display_name": "Customer SP",
            "app_owner_organization_id": "11111111-2222-3333-4444-555555555555",
        },
    ]
    iam.load_tenant_service_accounts(neo4j_session, TEST_TENANT_ID, service_accounts, TEST_UPDATE_TAG)
    assert check_nodes(neo4j_session, 'AzureServiceAccount', ['object_id', 'managed_type']) >= {
        ('ms-first-party', 'predefined'),
        ('customer-sp', 'custom'),
    }


def test_load_roles_managed_type(neo4j_session):
    roles = [
        {
            "id": "predefined-builtin-role",
            "type": "Microsoft.Authorization/roleDefinitions",
            "roleName": "Owner",
        },
        {
            "id": "custom-role",
            "type": "Microsoft.Authorization/roleAssignments",
            "role_type": "CustomRole",
            "roleName": "MyRole",
        },
    ]
    iam.load_roles(neo4j_session, TEST_TENANT_ID, roles, TEST_UPDATE_TAG, SUBSCRIPTION_ID=None)
    assert check_nodes(neo4j_session, 'AzureRole', ['id', 'managed_type']) >= {
        ('predefined-builtin-role', 'predefined'),
        ('custom-role', 'custom'),
    }


def test_load_role_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureTenant{id: $tenant_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    iam.load_tenant_service_accounts(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_SERVICE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    iam.load_roles(
        neo4j_session,
        TEST_TENANT_ID,
        DESCRIBE_ROLES,
        TEST_UPDATE_TAG,
        SUBSCRIPTION_ID=None,
    )

    expected = {
        (
            "86823hkhjhd",
            "97254c67-852d-61c20eb66ffc",
        ),
        (
            "hvhg575757g",
            "97254c67-852d-61c20eb66ffcsdds",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureServiceAccount)-[:ASSUME_ROLE]->(n2:AzureRole) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected
