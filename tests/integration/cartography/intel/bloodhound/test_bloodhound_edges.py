import pytest

from cartography.intel.bloodhound import sync
from cartography.intel.bloodhound.parser import CollectionMethod
from cartography.intel.common.object_store import LocalReportReader
from tests.data.bloodhound import collection as fixture
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
NEXT_UPDATE_TAG = 123456790


def _sync(neo4j_session, path, update_tag=TEST_UPDATE_TAG):
    sync(neo4j_session, LocalReportReader(str(path)), update_tag)


def _rels(neo4j_session, rel_label, target_label="ADObject"):
    return check_rels(
        neo4j_session,
        "ADObject",
        "id",
        target_label,
        "id",
        rel_label,
    )


def _partner_collection(**user_props):
    """A collection of the trusted domain holding the user the fixture references."""
    sid = fixture.PARTNER_SID
    return {
        "domains": [
            {
                "ObjectIdentifier": sid,
                "Properties": {
                    "name": fixture.PARTNER_NAME,
                    "domain": fixture.PARTNER_NAME,
                    "domainsid": sid,
                },
                "Aces": [],
                "IsDeleted": False,
                "Trusts": [],
            },
        ],
        "users": [
            {
                "ObjectIdentifier": fixture.PARTNER_USER_SID,
                "Properties": {
                    "name": f"MIGRATED@{fixture.PARTNER_NAME}",
                    "domain": fixture.PARTNER_NAME,
                    "domainsid": sid,
                    "samaccountname": "migrated",
                    **user_props,
                },
                "Aces": [],
                "IsDeleted": False,
            },
        ],
        "groups": [],
        "computers": [],
    }


@pytest.fixture(autouse=True)
def _reset_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_sync_imports_acl_edges(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    assert _rels(neo4j_session, "GENERIC_ALL") == {
        (fixture.PARTNER_ADMINS_SID, fixture.DOMAIN_SID),
    }
    assert _rels(neo4j_session, "FORCE_CHANGE_PASSWORD") == {
        (fixture.HELPDESK_SID, fixture.ALICE_SID),
    }
    assert _rels(neo4j_session, "GENERIC_WRITE") == {
        (fixture.HELPDESK_SID, fixture.ALICE_SID),
    }
    assert _rels(neo4j_session, "ADD_KEY_CREDENTIAL_LINK") == {
        (fixture.ALICE_SID, fixture.SVC_SID),
    }
    assert _rels(neo4j_session, "ADD_SELF") == {
        (fixture.ALICE_SID, fixture.HELPDESK_SID),
    }
    assert _rels(neo4j_session, "ADD_MEMBER") == {
        (fixture.SVC_SID, fixture.HELPDESK_SID),
    }
    assert _rels(neo4j_session, "READ_LAPS_PASSWORD") == {
        (fixture.HELPDESK_SID, fixture.WS01_SID),
    }
    # Alice's ACE over herself grants nothing.
    assert _rels(neo4j_session, "WRITE_SPN") == set()
    # Only the principal holding both replication rights can DCSync.
    assert _rels(neo4j_session, "DC_SYNC", "ADDomain") == {
        (fixture.PARTNER_ADMINS_SID, fixture.DOMAIN_SID),
    }
    inherited = {
        (r["kind"], r["inherited"])
        for r in neo4j_session.run(
            "MATCH (:ADGroup {id: $id})-[r]->(:ADUser) "
            "RETURN type(r) AS kind, r.is_inherited AS inherited",
            id=fixture.HELPDESK_SID,
        )
    }
    assert inherited == {
        ("FORCE_CHANGE_PASSWORD", False),
        ("GENERIC_WRITE", True),
    }
    rel = neo4j_session.run(
        "MATCH (:ADGroup)-[r:READ_LAPS_PASSWORD]->(:ADComputer) RETURN r",
    ).single()["r"]
    assert rel["collected_at"] == fixture.COLLECTED_AT
    assert rel["source_uri"] == f"{archive}!20261012143015_computers.json"
    # OWNER RIGHTS is not a principal and gets no node.
    owner_rights = neo4j_session.run(
        "MATCH (n:ADObject) WHERE n.id ENDS WITH 'S-1-3-4' RETURN count(n) AS c",
    ).single()["c"]
    assert owner_rights == 0


def test_sync_imports_host_and_delegation_edges(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    # Helpdesk is a local administrator on WS01, and a GPO adds svc_app. The
    # local account in the group has no AD object and is skipped.
    assert _rels(neo4j_session, "ADMIN_TO", "ADComputer") == {
        (fixture.HELPDESK_SID, fixture.WS01_SID),
        (fixture.SVC_SID, fixture.WS01_SID),
    }
    # Domain Users is in Remote Desktop Users, but only Alice holds the logon right.
    assert _rels(neo4j_session, "CAN_RDP", "ADComputer") == {
        (fixture.ALICE_SID, fixture.WS01_SID),
    }
    assert _rels(neo4j_session, "CAN_PS_REMOTE", "ADComputer") == {
        (fixture.SVC_SID, fixture.WS01_SID),
    }
    assert check_rels(
        neo4j_session,
        "ADComputer",
        "id",
        "ADUser",
        "id",
        "HAS_SESSION",
    ) == {
        (fixture.WS01_SID, fixture.ALICE_SID),
        (fixture.WS01_SID, fixture.SVC_SID),
    }
    assert _rels(neo4j_session, "ALLOWED_TO_DELEGATE") == {
        (fixture.SVC_SID, fixture.WS01_SID),
    }
    assert _rels(neo4j_session, "ALLOWED_TO_ACT", "ADComputer") == {
        (fixture.SVC_SID, fixture.WS01_SID),
    }
    assert _rels(neo4j_session, "HAS_SID_HISTORY") == {
        (fixture.SVC_SID, fixture.PARTNER_USER_SID),
    }
    local_accounts = neo4j_session.run(
        "MATCH (n:ADObject {id: $id}) RETURN count(n) AS c",
        id=fixture.WS01_LOCAL_ADMIN_SID,
    ).single()["c"]
    assert local_accounts == 0


def test_placeholders_for_principals_outside_the_import(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    placeholders = {
        (r["id"], frozenset(r["labels"]), r["domainsid"], r["resources"])
        for r in neo4j_session.run(
            "MATCH (n:ADObject {collected: false}) WHERE NOT n:ADDomain "
            "RETURN n.id AS id, labels(n) AS labels, n.domainsid AS domainsid, "
            "COUNT { (n)<-[:RESOURCE]-() } AS resources",
        )
    }
    assert placeholders == {
        (
            fixture.PARTNER_ADMINS_SID,
            frozenset({"ADGroup", "ADObject"}),
            fixture.PARTNER_SID,
            0,
        ),
        (
            fixture.PARTNER_USER_SID,
            frozenset({"ADUser", "ADObject"}),
            fixture.PARTNER_SID,
            0,
        ),
    }


def test_later_import_fills_in_placeholder(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261012143015_x.zip",
            _partner_collection(),
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ADUser",
        ["id", "samaccountname", "collected"],
    ) >= {(fixture.PARTNER_USER_SID, "migrated", True)}
    assert len(check_nodes(neo4j_session, "ADUser", ["id"])) == 3
    assert _rels(neo4j_session, "HAS_SID_HISTORY") == {
        (fixture.SVC_SID, fixture.PARTNER_USER_SID),
    }


def test_placeholder_never_overwrites_imported_principal(neo4j_session, tmp_path):
    # Arrange
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261012143015_x.zip",
            _partner_collection(),
        ),
    )

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ADUser",
        ["id", "samaccountname", "collected", "lastupdated"],
    ) >= {(fixture.PARTNER_USER_SID, "migrated", True, TEST_UPDATE_TAG)}
    assert _rels(neo4j_session, "HAS_SID_HISTORY") == {
        (fixture.SVC_SID, fixture.PARTNER_USER_SID),
    }


def test_unreferenced_placeholder_is_removed(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))
    data = fixture.collection()
    for user in data["users"]:
        user["HasSIDHistory"] = []

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261013090000_x.zip",
            data,
            timestamp="20261013090000",
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    placeholders = {
        r["id"]
        for r in neo4j_session.run(
            "MATCH (n:ADObject {collected: false}) WHERE NOT n:ADDomain "
            "RETURN n.id AS id",
        )
    }
    assert placeholders == {fixture.PARTNER_ADMINS_SID}


def test_unreachable_computer_keeps_host_edges(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))
    data = fixture.collection()
    (computer,) = data["computers"]
    computer["LocalGroups"] = []
    computer["UserRights"] = []
    for name in ("Sessions", "PrivilegedSessions", "RegistrySessions"):
        computer[name] = {"Collected": False, "FailureReason": None, "Results": []}
    data["ous"][0]["GPOChanges"]["LocalAdmins"] = []

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261013090000_x.zip",
            data,
            timestamp="20261013090000",
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert _rels(neo4j_session, "ADMIN_TO", "ADComputer") == {
        (fixture.HELPDESK_SID, fixture.WS01_SID),
        (fixture.SVC_SID, fixture.WS01_SID),
    }
    assert _rels(neo4j_session, "CAN_RDP", "ADComputer") == {
        (fixture.ALICE_SID, fixture.WS01_SID),
    }
    assert check_rels(
        neo4j_session,
        "ADComputer",
        "id",
        "ADUser",
        "id",
        "HAS_SESSION",
    ) == {
        (fixture.WS01_SID, fixture.ALICE_SID),
        (fixture.WS01_SID, fixture.SVC_SID),
    }


def test_reachable_computer_removes_stale_host_edges(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))
    data = fixture.collection()
    (computer,) = data["computers"]
    computer["LocalGroups"][0]["Results"] = []
    for name in ("Sessions", "PrivilegedSessions", "RegistrySessions"):
        computer[name]["Results"] = []
    data["ous"][0]["GPOChanges"]["LocalAdmins"] = []

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261013090000_x.zip",
            data,
            timestamp="20261013090000",
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert _rels(neo4j_session, "ADMIN_TO", "ADComputer") == set()
    assert (
        check_rels(
            neo4j_session,
            "ADComputer",
            "id",
            "ADUser",
            "id",
            "HAS_SESSION",
        )
        == set()
    )
    assert _rels(neo4j_session, "CAN_RDP", "ADComputer") == {
        (fixture.ALICE_SID, fixture.WS01_SID),
    }


def test_collection_without_acl_method_keeps_acl_edges(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))
    data = fixture.collection()
    for objects in data.values():
        for obj in objects:
            obj["Aces"] = []

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261013090000_x.zip",
            data,
            timestamp="20261013090000",
            methods=fixture.ALL_METHODS & ~int(CollectionMethod.ACL),
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert _rels(neo4j_session, "DC_SYNC", "ADDomain") == {
        (fixture.PARTNER_ADMINS_SID, fixture.DOMAIN_SID),
    }
    assert _rels(neo4j_session, "ADD_MEMBER") == {
        (fixture.SVC_SID, fixture.HELPDESK_SID),
    }


def test_acl_edges_removed_when_acls_were_collected(neo4j_session, tmp_path):
    # Arrange
    _sync(neo4j_session, fixture.write_zip(tmp_path / "a" / "20261012143015_x.zip"))
    data = fixture.collection()
    for objects in data.values():
        for obj in objects:
            obj["Aces"] = []

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "b" / "20261013090000_x.zip",
            data,
            timestamp="20261013090000",
        ),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert _rels(neo4j_session, "DC_SYNC", "ADDomain") == set()
    assert _rels(neo4j_session, "ADD_MEMBER") == set()
    # Nothing references the trusted domain's admins any more.
    assert check_nodes(neo4j_session, "ADGroup", ["id"]) == {
        (fixture.DOMAIN_USERS_SID,),
        (fixture.DOMAIN_COMPUTERS_SID,),
        (fixture.HELPDESK_SID,),
    }
