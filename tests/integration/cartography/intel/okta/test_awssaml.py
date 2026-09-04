import cartography.intel.okta
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

    assert (
        check_rels(
            neo4j_session,
            "AWSRole",
            "arn",
            "OktaGroup",
            "name",
            "HAS_ROLE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    relationship_metadata = neo4j_session.run(
        """
        MATCH (group:OktaGroup)-[r]->(:AWSRole)
        WHERE group.id IN $GROUP_IDS AND r.lastupdated = $UPDATE_TAG
              AND type(r) IN ["ALLOWED_BY", "HAS_ROLE"]
        RETURN DISTINCT r._sub_resource_label AS label,
                        r._sub_resource_id AS id
        """,
        GROUP_IDS=["group1", "group2", "group3"],
        UPDATE_TAG=TEST_UPDATE_TAG,
    ).data()
    assert relationship_metadata == [
        {
            "label": "OktaOrganization",
            "id": TEST_ORG_ID,
        },
    ]


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


def test_sync_okta_aws_saml_scopes_groups_to_the_current_organization(
    neo4j_session,
):
    # Arrange
    other_org_id = "other-okta-org-id"
    current_group_id = "scope-current-group"
    current_sso_group_id = "scope-current-sso-group"
    other_group_id = "other-org-group"
    other_sso_group_id = "other-org-sso-group"
    current_role_arn = "arn:aws:iam::2468:role/current-role"
    current_sso_role_arn = (
        "arn:aws:iam::2468:role/AWSReservedSSO_current-sso-role_abcdef"
    )
    other_role_arn = "arn:aws:iam::4321:role/other-org-role"
    other_sso_role_arn = "arn:aws:iam::4321:role/AWSReservedSSO_other-sso-role_abcdef"
    neo4j_session.run(
        """
        UNWIND $MAPPINGS AS mapping
        MERGE (org:OktaOrganization {id: mapping.org_id})
        MERGE (app:OktaApplication {id: mapping.app_id})
        SET app.name = mapping.app_name
        MERGE (group:OktaGroup {id: mapping.group_id})
        SET group.name = mapping.group_name
        MERGE (org)-[:RESOURCE]->(app)
        MERGE (org)-[:RESOURCE]->(group)
        MERGE (group)-[:APPLICATION]->(app)
        MERGE (account:AWSAccount {id: mapping.account_id})
        MERGE (role:AWSRole {id: mapping.role_arn})
        SET role.arn = mapping.role_arn,
            role.name = mapping.role_name,
            role.path = mapping.role_path
        MERGE (account)-[:RESOURCE]->(role)
        """,
        MAPPINGS=[
            {
                "org_id": TEST_ORG_ID,
                "app_id": "scope-current-aws-app",
                "app_name": "amazon_aws",
                "group_id": current_group_id,
                "group_name": "aws#test#current-role#2468",
                "account_id": "2468",
                "role_arn": current_role_arn,
                "role_name": "current-role",
                "role_path": "/",
            },
            {
                "org_id": TEST_ORG_ID,
                "app_id": "scope-current-aws-sso-app",
                "app_name": "amazon_aws_sso",
                "group_id": current_sso_group_id,
                "group_name": "aws#sso#current-sso-role#2468",
                "account_id": "2468",
                "role_arn": current_sso_role_arn,
                "role_name": "AWSReservedSSO_current-sso-role_abcdef",
                "role_path": "/aws-reserved/sso.amazonaws.com/",
            },
            {
                "org_id": other_org_id,
                "app_id": "scope-other-aws-app",
                "app_name": "amazon_aws",
                "group_id": other_group_id,
                "group_name": "aws#test#other-org-role#4321",
                "account_id": "4321",
                "role_arn": other_role_arn,
                "role_name": "other-org-role",
                "role_path": "/",
            },
            {
                "org_id": other_org_id,
                "app_id": "scope-other-aws-sso-app",
                "app_name": "amazon_aws_sso",
                "group_id": other_sso_group_id,
                "group_name": "aws#sso#other-sso-role#4321",
                "account_id": "4321",
                "role_arn": other_sso_role_arn,
                "role_name": "AWSReservedSSO_other-sso-role_abcdef",
                "role_path": "/aws-reserved/sso.amazonaws.com/",
            },
        ],
    )

    # Act
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Assert
    relationships = neo4j_session.run(
        """
        MATCH (group:OktaGroup)-[r]->(role:AWSRole)
        WHERE group.id IN $GROUP_IDS
              AND type(r) IN ["ALLOWED_BY", "HAS_ROLE"]
        RETURN group.id AS group_id, type(r) AS rel_type, role.arn AS role_arn
        """,
        GROUP_IDS=[
            current_group_id,
            current_sso_group_id,
            other_group_id,
            other_sso_group_id,
        ],
    ).data()
    assert {
        (row["group_id"], row["rel_type"], row["role_arn"]) for row in relationships
    } == {
        (current_group_id, "ALLOWED_BY", current_role_arn),
        (current_group_id, "HAS_ROLE", current_role_arn),
        (current_sso_group_id, "ALLOWED_BY", current_sso_role_arn),
        (current_sso_group_id, "HAS_ROLE", current_sso_role_arn),
    }


def test_sync_okta_aws_saml_removes_stale_relationships(neo4j_session):
    # Arrange
    org_id = "stale-test-okta-org-id"
    group_id = "stale-test-group"
    role_arn = "arn:aws:iam::8765:role/stale-test-role"
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $ORG_ID})
        MERGE (app:OktaApplication {id: $APP_ID, name: "amazon_aws"})
        MERGE (org)-[:RESOURCE]->(app)
        MERGE (group:OktaGroup {
            id: $GROUP_ID,
            name: "aws#test#stale-test-role#8765"
        })
        MERGE (org)-[:RESOURCE]->(group)
        MERGE (group)-[:APPLICATION]->(app)
        MERGE (role:AWSRole {id: $ROLE_ARN, arn: $ROLE_ARN})
        """,
        ORG_ID=org_id,
        APP_ID="stale-test-app",
        GROUP_ID=group_id,
        ROLE_ARN=role_arn,
    )
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        org_id,
    )

    # Act
    neo4j_session.run(
        """
        MATCH (:OktaGroup {id: $GROUP_ID})-[r:APPLICATION]->(:OktaApplication)
        DELETE r
        """,
        GROUP_ID=group_id,
    )
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG + 1,
        org_id,
    )

    # Assert
    relationship_count = neo4j_session.run(
        """
        MATCH (:OktaGroup {id: $GROUP_ID})-[r]->(:AWSRole)
        WHERE type(r) IN ["ALLOWED_BY", "HAS_ROLE"]
        RETURN count(r) AS count
        """,
        GROUP_ID=group_id,
    ).single(strict=True)["count"]
    assert relationship_count == 0


def test_okta_cleanup_removes_unscoped_legacy_role_relationships(neo4j_session):
    # Arrange
    org_id = "legacy-role-test-okta-org-id"
    group_id = "legacy-role-test-group"
    role_arn = "arn:aws:iam::9876:role/legacy-role-test"
    other_org_id = "other-legacy-role-test-okta-org-id"
    other_group_id = "other-legacy-role-test-group"
    other_role_arn = "arn:aws:iam::9876:role/other-legacy-role-test"
    neo4j_session.run(
        """
        UNWIND $MAPPINGS AS mapping
        MERGE (org:OktaOrganization {id: mapping.org_id})
        MERGE (group:OktaGroup {id: mapping.group_id})
        SET group.lastupdated = $UPDATE_TAG
        MERGE (org)-[:RESOURCE]->(group)
        MERGE (role:AWSRole {id: mapping.role_arn})
        SET role.arn = mapping.role_arn
        MERGE (group)-[:ALLOWED_BY {lastupdated: $OLD_UPDATE_TAG}]->(role)
        """,
        MAPPINGS=[
            {
                "org_id": org_id,
                "group_id": group_id,
                "role_arn": role_arn,
            },
            {
                "org_id": other_org_id,
                "group_id": other_group_id,
                "role_arn": other_role_arn,
            },
        ],
        UPDATE_TAG=TEST_UPDATE_TAG,
        OLD_UPDATE_TAG=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.okta._cleanup_okta_organizations(
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "OKTA_ORG_ID": org_id,
        },
    )

    # Assert
    relationship_counts = neo4j_session.run(
        """
        UNWIND $GROUP_IDS AS group_id
        OPTIONAL MATCH (:OktaGroup {id: group_id})-[r:ALLOWED_BY]->(:AWSRole)
        RETURN group_id, count(r) AS count
        """,
        GROUP_IDS=[group_id, other_group_id],
    ).data()
    assert {row["group_id"]: row["count"] for row in relationship_counts} == {
        group_id: 0,
        other_group_id: 1,
    }


def test_okta_cleanup_preserves_adopted_legacy_role_relationships(neo4j_session):
    # Arrange
    org_id = TEST_ORG_ID
    group_id = "legacy-adoption-group"
    role_arn = "arn:aws:iam::1234:role/myrole1"
    _setup_okta_test_data(neo4j_session)
    _setup_aws_test_data(neo4j_session)
    neo4j_session.run(
        """
        MATCH (org:OktaOrganization {id: $ORG_ID})
        MATCH (app:OktaApplication {name: "amazon_aws"})
        MATCH (role:AWSRole {arn: $ROLE_ARN})
        MERGE (group:OktaGroup {id: $GROUP_ID})
        SET group.name = "aws#test#myrole1#1234"
        MERGE (org)-[:RESOURCE]->(group)
        MERGE (group)-[:APPLICATION]->(app)
        MERGE (group)-[:ALLOWED_BY {lastupdated: $OLD_UPDATE_TAG}]->(role)
        """,
        ORG_ID=org_id,
        GROUP_ID=group_id,
        ROLE_ARN=role_arn,
        OLD_UPDATE_TAG=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.okta.awssaml.sync_okta_aws_saml(
        neo4j_session,
        DEFAULT_REGEX,
        TEST_UPDATE_TAG,
        org_id,
    )
    cartography.intel.okta._cleanup_okta_organizations(
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "OKTA_ORG_ID": org_id,
        },
    )

    # Assert
    relationships = neo4j_session.run(
        """
        MATCH (:OktaGroup {id: $GROUP_ID})-[r]->(:AWSRole {arn: $ROLE_ARN})
        WHERE type(r) IN ["ALLOWED_BY", "HAS_ROLE"]
        RETURN type(r) AS rel_type,
               r.lastupdated AS lastupdated,
               r._sub_resource_label AS sub_resource_label,
               r._sub_resource_id AS sub_resource_id
        """,
        GROUP_ID=group_id,
        ROLE_ARN=role_arn,
    ).data()
    assert {
        (
            row["rel_type"],
            row["lastupdated"],
            row["sub_resource_label"],
            row["sub_resource_id"],
        )
        for row in relationships
    } == {
        ("ALLOWED_BY", TEST_UPDATE_TAG, "OktaOrganization", org_id),
        ("HAS_ROLE", TEST_UPDATE_TAG, "OktaOrganization", org_id),
    }


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
