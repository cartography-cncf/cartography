import cartography.intel.okta.awssaml
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "test-okta-org-id"
DEFAULT_REGEX = r"^aws\#\S+\#(?P<role>[\w\-]+)\#(?P<accountid>\d+)$"


def test_sync_okta_aws_saml(neo4j_session):
    """
    Test that Okta AWS SAML integration creates correct relationships between OktaGroups and AWSRoles.
    This follows the recommended pattern: setup test data, call sync(), verify outcomes.
    """
    # Arrange - Create Okta organization, groups, and application
    _setup_okta_test_data(neo4j_session)

    # Arrange - Create AWS accounts and roles
    _setup_aws_test_data(neo4j_session)

    # Act - Run the main sync function
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Assert - Verify that ALLOWED_BY relationships were created between AWSRoles and OktaGroups
    expected_rels = {
        ("arn:aws:iam::1234:role/myrole1", "aws#test#myrole1#1234"),
        ("arn:aws:iam::1234:role/myrole2", "aws#test#myrole2#1234"),
        ("arn:aws:iam::1234:role/myrole3", "aws#test#myrole3#1234"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "OktaGroup",
        "name",
        "ALLOWED_BY",
        rel_direction_right=False,  # AWSRole <- OktaGroup
    )
    assert actual_rels == expected_rels


def test_sync_okta_aws_sso(neo4j_session):
    """
    Test that Okta AWS SSO integration creates correct relationships between OktaGroups and AWS SSO AWSRoles.
    AWS SSO roles have a different naming pattern with 'AWSReservedSSO' prefix and hash suffix.
    """
    # Arrange - Create Okta organization, groups for AWS SSO, and SSO application
    _setup_okta_sso_test_data(neo4j_session)

    # Arrange - Create AWS accounts and SSO roles
    _setup_aws_sso_test_data(neo4j_session)

    # Act - Run the main sync function
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Assert - Verify that ALLOWED_BY relationships were created for SSO roles
    # Query specifically for the SSO roles we created (in account 5678)
    result = neo4j_session.run(
        """
        MATCH (role:AWSRole)<-[:ALLOWED_BY]-(group:OktaGroup)
        WHERE role.arn STARTS WITH 'arn:aws:iam::5678:role/AWSReservedSSO'
        RETURN role.arn as role_arn, group.name as group_name
        """,
    )
    actual_rels = {(r["role_arn"], r["group_name"]) for r in result}
    expected_rels = {
        (
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole1_abcdef",
            "aws#sso#ssorole1#5678",
        ),
        (
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole2_bcdefa",
            "aws#sso#ssorole2#5678",
        ),
        (
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole3_cdefab",
            "aws#sso#ssorole3#5678",
        ),
    }
    assert actual_rels == expected_rels


def test_sync_okta_aws_saml_multiple_accounts(neo4j_session):
    """
    Test that the sync correctly handles roles across multiple AWS accounts.
    """
    # Arrange - Create Okta data with groups for multiple accounts
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        MERGE (app:OktaApplication{name: "amazon_aws"})
        MERGE (o)-[:RESOURCE]->(app)

        // Group for account 1234
        MERGE (g1:OktaGroup{id: "group1", name: "aws#test#admin#1234"})
        MERGE (o)-[:RESOURCE]->(g1)
        MERGE (g1)-[:APPLICATION]->(app)

        // Group for account 5678
        MERGE (g2:OktaGroup{id: "group2", name: "aws#test#admin#5678"})
        MERGE (o)-[:RESOURCE]->(g2)
        MERGE (g2)-[:APPLICATION]->(app)
        """,
        ORG_ID=TEST_ORG_ID,
    )

    # Arrange - Create AWS roles in different accounts
    neo4j_session.run(
        """
        MERGE (acc1:AWSAccount{id: "1234"})
        MERGE (acc1)-[:RESOURCE]->(role1:AWSRole{
            id: "arn:aws:iam::1234:role/admin",
            arn: "arn:aws:iam::1234:role/admin",
            name: "admin"
        })

        MERGE (acc2:AWSAccount{id: "5678"})
        MERGE (acc2)-[:RESOURCE]->(role2:AWSRole{
            id: "arn:aws:iam::5678:role/admin",
            arn: "arn:aws:iam::5678:role/admin",
            name: "admin"
        })
        """,
    )

    # Act
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Assert - Each group should be linked to its corresponding role in the correct account
    # Query specifically for the admin roles we created in this test
    result = neo4j_session.run(
        """
        MATCH (role:AWSRole)<-[:ALLOWED_BY]-(group:OktaGroup)
        WHERE role.name = 'admin' AND group.name STARTS WITH 'aws#test#admin#'
        RETURN role.arn as role_arn, group.name as group_name
        """,
    )
    actual_rels = {(r["role_arn"], r["group_name"]) for r in result}
    expected_rels = {
        ("arn:aws:iam::1234:role/admin", "aws#test#admin#1234"),
        ("arn:aws:iam::5678:role/admin", "aws#test#admin#5678"),
    }
    assert actual_rels == expected_rels


def test_sync_okta_aws_saml_no_matching_roles(neo4j_session):
    """
    Test that the sync handles gracefully when Okta groups don't have matching AWS roles.
    """
    # Arrange - Create Okta groups with names that don't match any existing roles
    test_groups = [
        ("aws#nomatch#nonexistentrole1#9999", "nomatch-group1"),
        ("aws#nomatch#nonexistentrole2#9999", "nomatch-group2"),
        ("aws#nomatch#nonexistentrole3#9999", "nomatch-group3"),
    ]
    for group_name, group_id in test_groups:
        neo4j_session.run(
            """
            MERGE (o:OktaOrganization{id: $ORG_ID})
            MERGE (o)-[:RESOURCE]->(g:OktaGroup{name: $GROUP_NAME, id: $GROUP_ID, lastupdated: $UPDATE_TAG})
            MERGE (o)-[:RESOURCE]->(a:OktaApplication{name: "amazon_aws"})
            MERGE (g)-[:APPLICATION]->(a)
            """,
            ORG_ID=TEST_ORG_ID,
            GROUP_NAME=group_name,
            GROUP_ID=group_id,
            UPDATE_TAG=TEST_UPDATE_TAG,
        )

    # Act - Should not crash even though no matching AWS roles exist
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Assert - No ALLOWED_BY relationships should be created for our test groups
    # Query for relationships involving our test groups (aws#nomatch#*)
    result = neo4j_session.run(
        """
        MATCH (role:AWSRole)<-[:ALLOWED_BY]-(group:OktaGroup)
        WHERE group.name STARTS WITH 'aws#nomatch#'
        RETURN role.arn as role_arn, group.name as group_name
        """,
    )
    actual_rels = {(r["role_arn"], r["group_name"]) for r in result}
    assert actual_rels == set()


def _setup_okta_test_data(neo4j_session):
    """
    Helper to create Okta test data for regular AWS SAML (non-SSO).
    Creates an Okta organization, amazon_aws application, and groups with AWS naming pattern.
    """
    test_groups = [
        ("aws#test#myrole1#1234", "group1"),
        ("aws#test#myrole2#1234", "group2"),
        ("aws#test#myrole3#1234", "group3"),
    ]
    for group_name, group_id in test_groups:
        neo4j_session.run(
            """
            MERGE (o:OktaOrganization{id: $ORG_ID})
            MERGE (o)-[:RESOURCE]->(g:OktaGroup{name: $GROUP_NAME, id: $GROUP_ID, lastupdated: $UPDATE_TAG})
            MERGE (o)-[:RESOURCE]->(a:OktaApplication{name: "amazon_aws"})
            MERGE (g)-[:APPLICATION]->(a)
            """,
            ORG_ID=TEST_ORG_ID,
            GROUP_NAME=group_name,
            GROUP_ID=group_id,
            UPDATE_TAG=TEST_UPDATE_TAG,
        )


def _setup_aws_test_data(neo4j_session):
    """
    Helper to create AWS test data for regular (non-SSO) roles.
    """
    test_roles = [
        ("myrole1", "arn:aws:iam::1234:role/myrole1", "1234"),
        ("myrole2", "arn:aws:iam::1234:role/myrole2", "1234"),
        ("myrole3", "arn:aws:iam::1234:role/myrole3", "1234"),
    ]
    for role_name, arn, account_id in test_roles:
        neo4j_session.run(
            """
            MERGE (acc:AWSAccount{id: $account_id})
            MERGE (acc)-[:RESOURCE]->(role:AWSRole{
                name: $role_name,
                id: $arn,
                arn: $arn,
                lastupdated: $update_tag
            })
            """,
            role_name=role_name,
            arn=arn,
            account_id=account_id,
            update_tag=TEST_UPDATE_TAG,
        )


def _setup_okta_sso_test_data(neo4j_session):
    """
    Helper to create Okta test data for AWS SSO integration.
    Creates groups associated with amazon_aws_sso application.
    """
    test_groups = [
        ("aws#sso#ssorole1#5678", "ssogroup1"),
        ("aws#sso#ssorole2#5678", "ssogroup2"),
        ("aws#sso#ssorole3#5678", "ssogroup3"),
    ]
    for group_name, group_id in test_groups:
        neo4j_session.run(
            """
            MERGE (o:OktaOrganization{id: $ORG_ID})
            MERGE (o)-[:RESOURCE]->(g:OktaGroup{name: $GROUP_NAME, id: $GROUP_ID, lastupdated: $UPDATE_TAG})
            MERGE (o)-[:RESOURCE]->(a:OktaApplication{name: "amazon_aws_sso"})
            MERGE (g)-[:APPLICATION]->(a)
            """,
            ORG_ID=TEST_ORG_ID,
            GROUP_NAME=group_name,
            GROUP_ID=group_id,
            UPDATE_TAG=TEST_UPDATE_TAG,
        )


def _setup_aws_sso_test_data(neo4j_session):
    """
    Helper to create AWS SSO role test data.
    AWS SSO roles have a specific naming pattern with 'AWSReservedSSO' prefix and hash suffix.
    """
    test_sso_roles = [
        (
            "AWSReservedSSO_ssorole1_abcdef",
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole1_abcdef",
            "5678",
        ),
        (
            "AWSReservedSSO_ssorole2_bcdefa",
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole2_bcdefa",
            "5678",
        ),
        (
            "AWSReservedSSO_ssorole3_cdefab",
            "arn:aws:iam::5678:role/AWSReservedSSO_ssorole3_cdefab",
            "5678",
        ),
    ]
    for role_name, arn, account_id in test_sso_roles:
        neo4j_session.run(
            """
            MERGE (acc:AWSAccount{id: $account_id})
            MERGE (acc)-[:RESOURCE]->(role:AWSRole{
                name: $role_name,
                id: $arn,
                arn: $arn,
                path: "/aws-reserved/sso.amazonaws.com/",
                lastupdated: $update_tag
            })
            """,
            role_name=role_name,
            arn=arn,
            account_id=account_id,
            update_tag=TEST_UPDATE_TAG,
        )
