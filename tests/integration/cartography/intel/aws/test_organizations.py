import botocore.exceptions
import pytest

import cartography.intel.aws.organizations
from tests.data.aws.organizations import TEST_ACCOUNTS
from tests.data.aws.organizations import TEST_ORGANIZATION
from tests.data.aws.organizations import TEST_ORGANIZATION_ACCOUNTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SECOND_UPDATE_TAG = 987654321


@pytest.fixture(autouse=True)
def cleanup_aws_organization_test_data(neo4j_session):
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:AWSAccount OR n:AWSRootPrincipal OR n:AWSOrganization
        DETACH DELETE n
        """,
    )
    yield
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:AWSAccount OR n:AWSRootPrincipal OR n:AWSOrganization
        DETACH DELETE n
        """,
    )


class FakeOrganizationsPaginator:
    def __init__(self, accounts):
        self.accounts = accounts

    def paginate(self):
        return [{"Accounts": self.accounts}]


class FakeOrganizationsClient:
    def __init__(self, organization, accounts=None, list_accounts_error=None):
        self.organization = organization
        self.accounts = accounts or []
        self.list_accounts_error = list_accounts_error

    def describe_organization(self):
        return {"Organization": self.organization}

    def get_paginator(self, name):
        if name != "list_accounts":
            raise ValueError(f"unexpected paginator: {name}")
        if self.list_accounts_error:
            raise self.list_accounts_error
        return FakeOrganizationsPaginator(self.accounts)


def test_sync_aws_accounts(neo4j_session):
    """
    Ensure that sync() creates AWSAccount and AWSRootPrincipal nodes.
    """
    # Arrange
    accounts = TEST_ACCOUNTS

    # Act
    cartography.intel.aws.organizations.sync(
        neo4j_session,
        accounts,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAccount", ["id", "name"]) == {
        ("111111111111", "test-account-1"),
        ("222222222222", "test-account-2"),
    }
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws:iam::111111111111:root",),
        ("arn:aws:iam::222222222222:root",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSRootPrincipal",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "arn:aws:iam::111111111111:root"),
        ("222222222222", "arn:aws:iam::222222222222:root"),
    }


def test_sync_aws_organization(neo4j_session):
    """
    Ensure that sync_aws_organization() creates AWSOrganization nodes and ties
    active AWSAccount nodes to the organization.
    """
    # Arrange
    organizations_client = FakeOrganizationsClient(
        TEST_ORGANIZATION,
        TEST_ORGANIZATION_ACCOUNTS,
    )

    # Act
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        organizations_client,
        "111111111111",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSOrganization",
        ["id", "arn", "feature_set", "management_account_id"],
    ) == {
        (
            "o-exampleorgid",
            "arn:aws:organizations::111111111111:organization/o-exampleorgid",
            "ALL",
            "111111111111",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "name", "email", "state", "org_id"],
    ) == {
        (
            "111111111111",
            "management-account",
            "management@example.com",
            "ACTIVE",
            "o-exampleorgid",
        ),
        (
            "222222222222",
            "security-account",
            "security@example.com",
            "ACTIVE",
            "o-exampleorgid",
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "o-exampleorgid"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganization",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid", "111111111111"),
        ("o-exampleorgid", "222222222222"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSRootPrincipal",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "arn:aws:iam::111111111111:root"),
        ("222222222222", "arn:aws:iam::222222222222:root"),
    }


def test_sync_aws_organization_falls_back_to_current_account_membership(neo4j_session):
    """
    describe_organization() is available to member accounts; list_accounts()
    requires management or delegated-admin access. If list_accounts() is denied,
    keep existing account metadata and still attach the current account to its org.
    """
    # Arrange
    cartography.intel.aws.organizations.sync(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    error = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "ListAccounts",
    )
    organizations_client = FakeOrganizationsClient(
        TEST_ORGANIZATION,
        list_accounts_error=error,
    )

    # Act
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        organizations_client,
        "111111111111",
        TEST_SECOND_UPDATE_TAG,
        {"UPDATE_TAG": TEST_SECOND_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAccount", ["id", "name", "org_id"]) == {
        ("111111111111", "test-account-1", "o-exampleorgid"),
        ("222222222222", "test-account-2", None),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "o-exampleorgid"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganization",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid", "111111111111"),
    }


def test_sync_aws_organization_cleans_stale_memberships_only(neo4j_session):
    # Arrange
    first_organizations_client = FakeOrganizationsClient(
        TEST_ORGANIZATION,
        TEST_ORGANIZATION_ACCOUNTS[:2],
    )
    second_organizations_client = FakeOrganizationsClient(
        TEST_ORGANIZATION,
        TEST_ORGANIZATION_ACCOUNTS[:1],
    )

    # Act
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        first_organizations_client,
        "111111111111",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Act
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        second_organizations_client,
        "111111111111",
        TEST_SECOND_UPDATE_TAG,
        {"UPDATE_TAG": TEST_SECOND_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAccount", ["id"]) == {
        ("111111111111",),
        ("222222222222",),
    }
    assert check_nodes(neo4j_session, "AWSOrganization", ["id"]) == {
        ("o-exampleorgid",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "o-exampleorgid"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganization",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid", "111111111111"),
    }
