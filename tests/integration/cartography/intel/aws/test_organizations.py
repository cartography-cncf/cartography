from copy import deepcopy

import botocore.exceptions
import pytest

import cartography.intel.aws.organizations
from cartography.client.core.tx import run_write_query
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


def _make_second_organization_client_with_colliding_root_and_ou_ids():
    organization = {
        **TEST_ORGANIZATION,
        "Id": "o-otherorgid",
        "Arn": "arn:aws:organizations::555555555555:organization/o-otherorgid",
        "MasterAccountArn": "arn:aws:organizations::555555555555:account/o-otherorgid/555555555555",
        "MasterAccountId": "555555555555",
        "MasterAccountEmail": "other-management@example.com",
    }
    roots = [
        {
            **TEST_ORGANIZATION_ROOTS[0],
            "Arn": "arn:aws:organizations::555555555555:root/o-otherorgid/r-exam",
        },
    ]
    account_id_map = {
        "111111111111": "555555555555",
        "222222222222": "666666666666",
        "333333333333": "777777777777",
        "444444444444": "888888888888",
    }
    accounts = []
    for account in TEST_ORGANIZATION_ACCOUNTS:
        new_account = deepcopy(account)
        new_account["Id"] = account_id_map[account["Id"]]
        new_account["Arn"] = (
            "arn:aws:organizations::555555555555:account/o-otherorgid/"
            f"{new_account['Id']}"
        )
        new_account["Email"] = f"{new_account['Name']}@other.example.com"
        accounts.append(new_account)
    accounts_for_parent = {
        "r-exam": [accounts[0], accounts[2]],
        "ou-exam-a1b2c3d4": [accounts[1]],
        "ou-exam-b2c3d4e5": [accounts[3]],
    }
    organizational_units = deepcopy(TEST_ORGANIZATIONAL_UNITS)
    for units in organizational_units.values():
        for unit in units:
            unit["Arn"] = unit["Arn"].replace("o-exampleorgid", "o-otherorgid")
    return FakeOrganizationsClient(
        organization,
        roots,
        organizational_units,
        accounts_for_parent,
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


def test_sync_aws_accounts_removes_stale_foreign_flag(neo4j_session):
    """
    Ensure configured AWS accounts are removed from foreign account classification.
    """
    # Arrange
    account_name = "test-account-1"
    account_id = TEST_ACCOUNTS[account_name]
    run_write_query(
        neo4j_session,
        """
        MERGE (account:AWSAccount {id: $ACCOUNT_ID})
        SET account.foreign = true
        """,
        ACCOUNT_ID=account_id,
    )

    # Act
    cartography.intel.aws.organizations.sync(
        neo4j_session,
        {account_name: account_id},
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "name", "inscope", "foreign"],
    ) == {
        (account_id, account_name, True, None),
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
    assert check_nodes(
        neo4j_session,
        "AWSOrganizationRoot",
        ["id", "root_id", "name"],
    ) == {
        ("o-exampleorgid/r-exam", "r-exam", "Root"),
    }
    assert check_nodes(
        neo4j_session,
        "AWSOrganizationalUnit",
        ["id", "ou_id", "name", "parent_root_id", "parent_ou_id"],
    ) == {
        (
            "o-exampleorgid/ou-exam-a1b2c3d4",
            "ou-exam-a1b2c3d4",
            "Security",
            "o-exampleorgid/r-exam",
            None,
        ),
        (
            "o-exampleorgid/ou-exam-b2c3d4e5",
            "ou-exam-b2c3d4e5",
            "Logging",
            None,
            "o-exampleorgid/ou-exam-a1b2c3d4",
        ),
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
            None,
        ),
        (
            "222222222222",
            "security-account",
            "security@example.com",
            "ACTIVE",
            "o-exampleorgid",
            None,
        ),
        (
            "333333333333",
            "suspended-account",
            "suspended@example.com",
            "SUSPENDED",
            "o-exampleorgid",
            None,
        ),
        (
            "444444444444",
            "logging-account",
            "logging@example.com",
            "ACTIVE",
            "o-exampleorgid",
            None,
        ),
    }
    # Ontology: raw AWS account State is normalized onto _ont_status.
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "_ont_status"],
    ) == {
        ("111111111111", "active"),
        ("222222222222", "active"),
        ("333333333333", "suspended"),
        ("444444444444", "active"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganization",
        "id",
        "AWSOrganizationRoot",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("o-exampleorgid", "o-exampleorgid/r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("o-exampleorgid/r-exam", "o-exampleorgid")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid/r-exam", "o-exampleorgid/ou-exam-a1b2c3d4"),
        ("o-exampleorgid/r-exam", "o-exampleorgid/ou-exam-b2c3d4e5"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("o-exampleorgid/ou-exam-a1b2c3d4", "o-exampleorgid/ou-exam-b2c3d4e5")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("o-exampleorgid/r-exam", "111111111111")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid/ou-exam-a1b2c3d4", "222222222222"),
        ("o-exampleorgid/ou-exam-b2c3d4e5", "444444444444"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationRoot",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("o-exampleorgid/ou-exam-a1b2c3d4", "o-exampleorgid/r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("o-exampleorgid/ou-exam-b2c3d4e5", "o-exampleorgid/ou-exam-a1b2c3d4")}
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationRoot",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("111111111111", "o-exampleorgid/r-exam")}
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {
        ("222222222222", "o-exampleorgid/ou-exam-a1b2c3d4"),
        ("444444444444", "o-exampleorgid/ou-exam-b2c3d4e5"),
    }
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws:iam::111111111111:root",),
        ("arn:aws:iam::222222222222:root",),
        ("arn:aws:iam::444444444444:root",),
    }
    recursive_parent_rels = {
        (record["account_id"], record["organization_id"])
        for record in neo4j_session.run(
            """
            MATCH (account:AWSAccount)-[:PARENT*]->(organization:AWSOrganization)
            RETURN account.id AS account_id, organization.id AS organization_id
            """,
        )
    }
    assert recursive_parent_rels == {
        ("111111111111", "o-exampleorgid"),
        ("222222222222", "o-exampleorgid"),
        ("444444444444", "o-exampleorgid"),
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
        ("o-exampleorgid/r-exam",),
    }
    assert check_nodes(neo4j_session, "AWSOrganizationalUnit", ["id"]) == {
        ("o-exampleorgid/ou-exam-a1b2c3d4",),
        ("o-exampleorgid/ou-exam-b2c3d4e5",),
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
        ("222222222222", "o-exampleorgid/ou-exam-a1b2c3d4"),
        ("444444444444", "o-exampleorgid/ou-exam-b2c3d4e5"),
    }


def test_sync_aws_organization_scopes_root_and_ou_ids_by_organization(
    neo4j_session,
):
    """
    AWS documents root and OU IDs as unique only within an organization, so
    separate organizations with the same raw IDs must not merge graph nodes.
    """
    # Arrange
    _sync_organization(neo4j_session, _make_organizations_client())
    second_organization_client = (
        _make_second_organization_client_with_colliding_root_and_ou_ids()
    )

    # Act
    cartography.intel.aws.organizations.sync_aws_organization(
        neo4j_session,
        second_organization_client,
        "555555555555",
        TEST_SECOND_UPDATE_TAG,
        {"UPDATE_TAG": TEST_SECOND_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSOrganizationRoot",
        ["id", "root_id", "org_id"],
    ) == {
        ("o-exampleorgid/r-exam", "r-exam", "o-exampleorgid"),
        ("o-otherorgid/r-exam", "r-exam", "o-otherorgid"),
    }
    assert check_nodes(
        neo4j_session,
        "AWSOrganizationalUnit",
        ["id", "ou_id", "org_id"],
    ) == {
        (
            "o-exampleorgid/ou-exam-a1b2c3d4",
            "ou-exam-a1b2c3d4",
            "o-exampleorgid",
        ),
        (
            "o-exampleorgid/ou-exam-b2c3d4e5",
            "ou-exam-b2c3d4e5",
            "o-exampleorgid",
        ),
        (
            "o-otherorgid/ou-exam-a1b2c3d4",
            "ou-exam-a1b2c3d4",
            "o-otherorgid",
        ),
        (
            "o-otherorgid/ou-exam-b2c3d4e5",
            "ou-exam-b2c3d4e5",
            "o-otherorgid",
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
    ) == {
        ("o-exampleorgid", "o-exampleorgid/r-exam"),
        ("o-otherorgid", "o-otherorgid/r-exam"),
    }
    assert check_rels(
        neo4j_session,
        "AWSOrganizationRoot",
        "id",
        "AWSOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {
        ("o-exampleorgid/r-exam", "o-exampleorgid"),
        ("o-otherorgid/r-exam", "o-otherorgid"),
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
        ("111111111111", "o-exampleorgid/r-exam"),
        ("222222222222", "o-exampleorgid/r-exam"),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("444444444444", "o-exampleorgid/ou-exam-b2c3d4e5")}
    assert check_rels(
        neo4j_session,
        "AWSOrganizationalUnit",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("o-exampleorgid/ou-exam-b2c3d4e5", "444444444444")}


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
        ("o-exampleorgid/ou-exam-a1b2c3d4",),
    }
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "org_id", "state", "inscope", "lastupdated"],
    ) == {
        ("111111111111", "o-exampleorgid", "ACTIVE", None, TEST_SECOND_UPDATE_TAG),
        ("222222222222", "o-exampleorgid", "ACTIVE", None, TEST_SECOND_UPDATE_TAG),
        ("333333333333", "o-exampleorgid", "SUSPENDED", None, TEST_SECOND_UPDATE_TAG),
        ("444444444444", None, None, None, TEST_SECOND_UPDATE_TAG),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSOrganizationalUnit",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("222222222222", "o-exampleorgid/ou-exam-a1b2c3d4")}


def test_sync_aws_organization_cleanup_preserves_configured_account_scope(
    neo4j_session,
):
    # Arrange
    cartography.intel.aws.organizations.sync(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    _sync_organization(neo4j_session, _make_organizations_client())
    organizational_units_without_nested_ou = {
        "r-exam": TEST_ORGANIZATIONAL_UNITS["r-exam"],
        "ou-exam-a1b2c3d4": [],
    }
    accounts_without_logging_account = {
        "r-exam": TEST_ACCOUNTS_FOR_PARENT["r-exam"],
        "ou-exam-a1b2c3d4": TEST_ACCOUNTS_FOR_PARENT["ou-exam-a1b2c3d4"],
    }

    # Act
    _sync_organization(
        neo4j_session,
        _make_organizations_client(
            organizational_units=organizational_units_without_nested_ou,
            accounts_for_parent=accounts_without_logging_account,
        ),
        TEST_SECOND_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        ["id", "org_id", "state", "inscope"],
    ) == {
        ("111111111111", "o-exampleorgid", "ACTIVE", True),
        ("222222222222", "o-exampleorgid", "ACTIVE", True),
        ("333333333333", "o-exampleorgid", "SUSPENDED", None),
        ("444444444444", None, None, True),
    }


def test_sync_aws_organization_cleans_ous_before_stale_roots(neo4j_session):
    # Arrange
    _sync_organization(neo4j_session, _make_organizations_client())
    replacement_roots = [
        {
            **TEST_ORGANIZATION_ROOTS[0],
            "Id": "r-repl",
            "Arn": "arn:aws:organizations::111111111111:root/o-exampleorgid/r-repl",
        },
    ]
    replacement_accounts_for_parent = {
        "r-repl": [TEST_ORGANIZATION_ACCOUNTS[0]],
    }

    # Act
    _sync_organization(
        neo4j_session,
        FakeOrganizationsClient(
            TEST_ORGANIZATION,
            replacement_roots,
            organizational_units={},
            accounts_for_parent=replacement_accounts_for_parent,
        ),
        TEST_SECOND_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSOrganizationRoot", ["id"]) == {
        ("o-exampleorgid/r-repl",),
    }
    assert check_nodes(neo4j_session, "AWSOrganizationalUnit", ["id"]) == set()
    assert check_nodes(neo4j_session, "AWSAccount", ["id"]) == {
        ("111111111111",),
        ("222222222222",),
        ("333333333333",),
        ("444444444444",),
    }
    assert (
        neo4j_session.run(
            """
            MATCH ()-[r:RESOURCE|PARENT]-()
            WHERE coalesce(endNode(r).id, '') STARTS WITH 'o-exampleorgid/ou-'
                OR coalesce(startNode(r).id, '') STARTS WITH 'o-exampleorgid/ou-'
                OR endNode(r).id = 'o-exampleorgid/r-exam'
                OR startNode(r).id = 'o-exampleorgid/r-exam'
            RETURN count(r) AS rel_count
            """,
        ).single()["rel_count"]
        == 0
    )
