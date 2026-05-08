import botocore.exceptions
import pytest

import cartography.intel.aws.organizations
from tests.data.aws.organizations import TEST_ACCOUNTS
from tests.data.aws.organizations import TEST_ACCOUNTS_FOR_PARENT
from tests.data.aws.organizations import TEST_ORGANIZATION
from tests.data.aws.organizations import TEST_ORGANIZATION_ACCOUNTS
from tests.data.aws.organizations import TEST_ORGANIZATION_ROOTS
from tests.data.aws.organizations import TEST_ORGANIZATIONAL_UNITS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SECOND_UPDATE_TAG = 987654321


@pytest.fixture(autouse=True)
def cleanup_aws_organization_test_data(neo4j_session):
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:AWSAccount
            OR n:AWSRootPrincipal
            OR n:AWSOrganization
            OR n:AWSOrganizationRoot
            OR n:AWSOrganizationalUnit
        DETACH DELETE n
        """,
    )
    yield
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:AWSAccount
            OR n:AWSRootPrincipal
            OR n:AWSOrganization
            OR n:AWSOrganizationRoot
            OR n:AWSOrganizationalUnit
        DETACH DELETE n
        """,
    )


class FakeOrganizationsPaginator:
    def __init__(self, pages, error=None):
        self.pages = pages
        self.error = error

    def paginate(self, **kwargs):
        if self.error:
            raise self.error
        return self.pages


class FakeOrganizationsClient:
    def __init__(
        self,
        organization,
        roots=None,
        organizational_units=None,
        accounts_for_parent=None,
        paginator_errors=None,
    ):
        self.organization = organization
        self.roots = roots or []
        self.organizational_units = organizational_units or {}
        self.accounts_for_parent = accounts_for_parent or {}
        self.paginator_errors = paginator_errors or {}

    def describe_organization(self):
        return {"Organization": self.organization}

    def get_paginator(self, name):
        if name == "list_roots":
            return FakeOrganizationsPaginator(
                [{"Roots": self.roots[:1]}, {"Roots": self.roots[1:]}],
                self.paginator_errors.get(name),
            )
        if name == "list_organizational_units_for_parent":
            return FakeOrganizationsParentPaginator(
                self.organizational_units,
                "OrganizationalUnits",
                self.paginator_errors.get(name),
            )
        if name == "list_accounts_for_parent":
            return FakeOrganizationsParentPaginator(
                self.accounts_for_parent,
                "Accounts",
                self.paginator_errors.get(name),
            )
        raise ValueError(f"unexpected paginator: {name}")


class FakeOrganizationsParentPaginator:
    def __init__(self, items_by_parent, result_key, error=None):
        self.items_by_parent = items_by_parent
        self.result_key = result_key
        self.error = error

    def paginate(self, **kwargs):
        if self.error:
            raise self.error
        items = self.items_by_parent.get(kwargs["ParentId"], [])
        return [{self.result_key: items[:1]}, {self.result_key: items[1:]}]


def _make_organizations_client(
    organizational_units=None,
    accounts_for_parent=None,
    paginator_errors=None,
):
    return FakeOrganizationsClient(
        TEST_ORGANIZATION,
        TEST_ORGANIZATION_ROOTS,
        organizational_units or TEST_ORGANIZATIONAL_UNITS,
        accounts_for_parent or TEST_ACCOUNTS_FOR_PARENT,
        paginator_errors,
    )


def _sync_organization(neo4j_session, client, update_tag=TEST_UPDATE_TAG):
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        client,
        "111111111111",
        update_tag,
        {"UPDATE_TAG": update_tag},
    )


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
        ("444444444444", "test-account-3"),
    }
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws:iam::111111111111:root",),
        ("arn:aws:iam::222222222222:root",),
        ("arn:aws:iam::444444444444:root",),
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
        ("444444444444", "arn:aws:iam::444444444444:root"),
    }


def test_sync_aws_organization_hierarchy(neo4j_session):
    """
    Ensure that sync_aws_organization() creates the organization hierarchy and
    active account placement relationships.
    """
    # Arrange
    organizations_client = _make_organizations_client()

    # Act
    _sync_organization(neo4j_session, organizations_client)

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
    assert check_nodes(neo4j_session, "AWSOrganizationRoot", ["id", "name"]) == {
        ("r-exam", "Root"),
    }
    assert check_nodes(
        neo4j_session,
        "AWSOrganizationalUnit",
        ["id", "name", "parent_root_id", "parent_ou_id"],
    ) == {
        ("ou-exam-a1b2c3d4", "Security", "r-exam", None),
        ("ou-exam-b2c3d4e5", "Logging", None, "ou-exam-a1b2c3d4"),
    }
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "name", "email", "state", "org_id", "inscope"],
    ) == {
        (
            "111111111111",
            "management-account",
            "management@example.com",
            "ACTIVE",
            "o-exampleorgid",
            True,
        ),
        (
            "222222222222",
            "security-account",
            "security@example.com",
            "ACTIVE",
            "o-exampleorgid",
            True,
        ),
        (
            "333333333333",
            "suspended-account",
            "suspended@example.com",
            "SUSPENDED",
            "o-exampleorgid",
            False,
        ),
        (
            "444444444444",
            "logging-account",
            "logging@example.com",
            "ACTIVE",
            "o-exampleorgid",
            True,
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganization",
        "id",
        "AWSOrganizationRoot",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("o-exampleorgid", "r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("r-exam", "ou-exam-a1b2c3d4"),
        ("r-exam", "ou-exam-b2c3d4e5"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("ou-exam-a1b2c3d4", "ou-exam-b2c3d4e5")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("r-exam", "111111111111")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("ou-exam-a1b2c3d4", "222222222222"),
        ("ou-exam-b2c3d4e5", "444444444444"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationRoot",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("ou-exam-a1b2c3d4", "r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("ou-exam-b2c3d4e5", "ou-exam-a1b2c3d4")}
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationRoot",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("111111111111", "r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {
        ("222222222222", "ou-exam-a1b2c3d4"),
        ("444444444444", "ou-exam-b2c3d4e5"),
    }
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws:iam::111111111111:root",),
        ("arn:aws:iam::222222222222:root",),
        ("arn:aws:iam::444444444444:root",),
    }


def test_sync_aws_organization_denied_hierarchy_preserves_prior_data(neo4j_session):
    """
    If a hierarchy API is denied, skip the org sync and cleanup so the last
    complete Organizations hierarchy remains intact.
    """
    # Arrange
    _sync_organization(neo4j_session, _make_organizations_client())
    error = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "ListAccountsForParent",
    )
    denied_client = _make_organizations_client(
        paginator_errors={"list_accounts_for_parent": error},
    )

    # Act
    _sync_organization(neo4j_session, denied_client, TEST_SECOND_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "AWSOrganizationRoot", ["id"]) == {
        ("r-exam",),
    }
    assert check_nodes(neo4j_session, "AWSOrganizationalUnit", ["id"]) == {
        ("ou-exam-a1b2c3d4",),
        ("ou-exam-b2c3d4e5",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {
        ("222222222222", "ou-exam-a1b2c3d4"),
        ("444444444444", "ou-exam-b2c3d4e5"),
    }


def test_sync_aws_organization_moves_account_between_parents(neo4j_session):
    # Arrange
    moved_accounts_for_parent = {
        "r-exam": [
            TEST_ORGANIZATION_ACCOUNTS[0],
            TEST_ORGANIZATION_ACCOUNTS[1],
        ],
        "ou-exam-a1b2c3d4": [],
        "ou-exam-b2c3d4e5": [
            TEST_ORGANIZATION_ACCOUNTS[3],
        ],
    }
    _sync_organization(neo4j_session, _make_organizations_client())

    # Act
    _sync_organization(
        neo4j_session,
        _make_organizations_client(accounts_for_parent=moved_accounts_for_parent),
        TEST_SECOND_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAccount", ["id"]) == {
        ("111111111111",),
        ("222222222222",),
        ("333333333333",),
        ("444444444444",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationRoot",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {
        ("111111111111", "r-exam"),
        ("222222222222", "r-exam"),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("444444444444", "ou-exam-b2c3d4e5")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("ou-exam-b2c3d4e5", "444444444444")}


def test_sync_aws_organization_cleans_deleted_ous_without_deleting_accounts(
    neo4j_session,
):
    # Arrange
    organizational_units_without_nested_ou = {
        "r-exam": TEST_ORGANIZATIONAL_UNITS["r-exam"],
        "ou-exam-a1b2c3d4": [],
    }
    accounts_without_nested_ou = {
        "r-exam": TEST_ACCOUNTS_FOR_PARENT["r-exam"],
        "ou-exam-a1b2c3d4": TEST_ACCOUNTS_FOR_PARENT["ou-exam-a1b2c3d4"],
    }
    _sync_organization(neo4j_session, _make_organizations_client())

    # Act
    _sync_organization(
        neo4j_session,
        _make_organizations_client(
            organizational_units=organizational_units_without_nested_ou,
            accounts_for_parent=accounts_without_nested_ou,
        ),
        TEST_SECOND_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSOrganizationalUnit", ["id"]) == {
        ("ou-exam-a1b2c3d4",),
    }
    assert check_nodes(neo4j_session, "AWSAccount", ["id", "org_id", "state"]) == {
        ("111111111111", "o-exampleorgid", "ACTIVE"),
        ("222222222222", "o-exampleorgid", "ACTIVE"),
        ("333333333333", "o-exampleorgid", "SUSPENDED"),
        ("444444444444", None, None),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("222222222222", "ou-exam-a1b2c3d4")}
