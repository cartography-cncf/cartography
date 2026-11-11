import json

import pytest

import cartography.intel.onepassword
from cartography.config import Config
from tests.data.onepassword import snapshots as data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
NEXT_UPDATE_TAG = 123456790


def _write(directory, name, snapshot):
    (directory / name).write_text(json.dumps(snapshot))


def _sync(neo4j_session, source, update_tag):
    cartography.intel.onepassword.start_onepassword_ingestion(
        neo4j_session,
        Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=update_tag,
            onepassword_source=str(source),
        ),
    )


def _grants(neo4j_session):
    return {
        (
            record["principal"],
            record["vault"],
            tuple(record["permissions"]),
            record["mask"],
        )
        for record in neo4j_session.run(
            """
            MATCH (p)-[r:CAN_ACCESS]->(v:OnePasswordVault)
            RETURN p.id AS principal, v.id AS vault,
                   r.permissions AS permissions, r.permissions_bitmask AS mask
            """,
        )
    }


@pytest.fixture(autouse=True)
def _reset_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_sync_onepassword_snapshot(neo4j_session, tmp_path):
    # Arrange
    _write(tmp_path, "snapshot.json", data.SNAPSHOT)

    # Act
    _sync(neo4j_session, tmp_path, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "OnePasswordAccount",
        ["id", "snapshot_id", "snapshot_collected_at", "collector_version"],
    ) == {
        (
            data.ACCOUNT_ID,
            data.SNAPSHOT["snapshot_id"],
            "2026-11-10T08:00:00Z",
            "0.1.0",
        ),
    }
    assert check_nodes(
        neo4j_session, "OnePasswordUser", ["id", "email", "state", "type"]
    ) == {
        (data.HOMER_ID, "homer@example.com", "ACTIVE", "MEMBER"),
        (data.MARGE_ID, "marge@example.com", "ACTIVE", "MEMBER"),
        (data.BART_ID, "bart@example.com", "SUSPENDED", "GUEST"),
    }
    assert check_nodes(neo4j_session, "OnePasswordServiceAccount", ["id", "name"]) == {
        (data.DEPLOY_BOT_ID, "Deploy bot"),
        (data.COLLECTOR_ID, None),
    }
    assert check_rels(
        neo4j_session,
        "UserAccount",
        "id",
        "OnePasswordGroup",
        "name",
        "MEMBER_OF",
    ) == {(data.HOMER_ID, "Engineering"), (data.MARGE_ID, "Owners")}
    assert check_rels(
        neo4j_session,
        "ServiceAccount",
        "id",
        "UserGroup",
        "name",
        "MEMBER_OF",
    ) == {(data.DEPLOY_BOT_ID, "Engineering")}
    assert _grants(neo4j_session) == {
        (data.BART_ID, data.INFRA_VAULT_ID, ("read_items",), data.READ_ITEMS),
        (data.COLLECTOR_ID, data.INFRA_VAULT_ID, ("read_items",), data.READ_ITEMS),
        (
            data.ENGINEERING_ID,
            data.INFRA_VAULT_ID,
            ("read_items", "reveal_item_password"),
            data.READ_ITEMS | data.REVEAL_ITEM_PASSWORD,
        ),
        (
            data.OWNERS_ID,
            data.SHARED_VAULT_ID,
            ("manage_vault",),
            data.MANAGE_VAULT | data.UNKNOWN_BIT,
        ),
    }
    assert check_rels(
        neo4j_session,
        "OnePasswordVault",
        "id",
        "Secret",
        "id",
        "CONTAINS",
    ) == {
        (data.INFRA_VAULT_ID, data.DEPLOY_KEY_ID),
        (data.INFRA_VAULT_ID, data.ROOT_LOGIN_ID),
        (data.SHARED_VAULT_ID, data.OLD_NOTE_ID),
    }
    assert check_nodes(
        neo4j_session, "OnePasswordItem", ["id", "category", "state"]
    ) == {
        (data.DEPLOY_KEY_ID, "SSH_KEY", None),
        (data.ROOT_LOGIN_ID, "LOGIN", None),
        (data.OLD_NOTE_ID, "SECURE_NOTE", "ARCHIVED"),
    }
    resource_count = neo4j_session.run(
        """
        MATCH (:OnePasswordAccount {id: $account_id})-[:RESOURCE]->(n)
        RETURN count(n) AS count
        """,
        account_id=data.ACCOUNT_ID,
    ).single()["count"]
    # 3 users, 2 service accounts, 2 groups, 2 vaults, 3 items
    assert resource_count == 12


def test_onepassword_users_map_to_ontology(neo4j_session, tmp_path):
    # Arrange
    _write(tmp_path, "snapshot.json", data.SNAPSHOT)

    # Act
    _sync(neo4j_session, tmp_path, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "OnePasswordUser",
        ["id", "_ont_email", "_ont_inactive", "_ont_source"],
    ) == {
        (data.HOMER_ID, "homer@example.com", False, "onepassword"),
        (data.MARGE_ID, "marge@example.com", False, "onepassword"),
        (data.BART_ID, "bart@example.com", True, "onepassword"),
    }


def test_newer_snapshot_replaces_removed_access(neo4j_session, tmp_path):
    # Arrange
    _write(tmp_path, "snapshot.json", data.SNAPSHOT)
    _sync(neo4j_session, tmp_path, TEST_UPDATE_TAG)
    _write(tmp_path, "snapshot.json", data.newer_snapshot())

    # Act
    _sync(neo4j_session, tmp_path, NEXT_UPDATE_TAG)

    # Assert
    assert data.BART_ID not in {
        user_id for (user_id,) in check_nodes(neo4j_session, "OnePasswordUser", ["id"])
    }
    assert _grants(neo4j_session) == {
        (data.COLLECTOR_ID, data.INFRA_VAULT_ID, ("read_items",), data.READ_ITEMS),
        (data.ENGINEERING_ID, data.INFRA_VAULT_ID, ("read_items",), data.READ_ITEMS),
    }


def test_sync_ingests_newest_snapshot_per_account(neo4j_session, tmp_path):
    # Arrange: an older snapshot of the same account must not restore Bart.
    _write(tmp_path, "a-newer.json", data.newer_snapshot())
    _write(tmp_path, "b-older.json", data.SNAPSHOT)
    _write(tmp_path, "c-other-account.json", data.other_account_snapshot())

    # Act
    _sync(neo4j_session, tmp_path, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "OnePasswordAccount", ["id", "snapshot_id"]) == {
        (data.ACCOUNT_ID, data.newer_snapshot()["snapshot_id"]),
        (data.OTHER_ACCOUNT_ID, data.other_account_snapshot()["snapshot_id"]),
    }
    assert data.BART_ID not in {
        user_id for (user_id,) in check_nodes(neo4j_session, "OnePasswordUser", ["id"])
    }
    assert check_rels(
        neo4j_session,
        "OnePasswordAccount",
        "id",
        "OnePasswordVault",
        "id",
        "RESOURCE",
    ) == {
        (data.ACCOUNT_ID, data.INFRA_VAULT_ID),
        (data.ACCOUNT_ID, data.SHARED_VAULT_ID),
        (data.OTHER_ACCOUNT_ID, data.other_account_snapshot()["vaults"][0]["id"]),
    }


def test_sync_of_one_account_keeps_other_accounts(neo4j_session, tmp_path):
    # Arrange
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _write(first, "snapshot.json", data.SNAPSHOT)
    _write(second, "snapshot.json", data.other_account_snapshot())
    _sync(neo4j_session, first, TEST_UPDATE_TAG)

    # Act
    _sync(neo4j_session, second, NEXT_UPDATE_TAG)

    # Assert
    assert len(check_nodes(neo4j_session, "OnePasswordUser", ["id"])) == 3
    assert len(_grants(neo4j_session)) == 4
