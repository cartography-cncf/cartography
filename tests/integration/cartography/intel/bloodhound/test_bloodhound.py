import json

import pytest

from cartography.intel.bloodhound import BloodHoundImportError
from cartography.intel.bloodhound import sync
from cartography.intel.bloodhound.parser import CollectionMethod
from cartography.intel.common.object_store import ListedReportReader
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ReportRef
from tests.data.bloodhound import collection as fixture
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
NEXT_UPDATE_TAG = 123456790


def _sync(neo4j_session, path, update_tag=TEST_UPDATE_TAG):
    sync(neo4j_session, LocalReportReader(str(path)), update_tag)


@pytest.fixture(autouse=True)
def _reset_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_sync_imports_nodes(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    assert check_nodes(neo4j_session, "ADDomain", ["id", "name", "collected"]) == {
        (fixture.DOMAIN_SID, fixture.DOMAIN_NAME, True),
        (fixture.PARTNER_SID, fixture.PARTNER_NAME, False),
    }
    # objectid mirrors id on every node, placeholders included, as in BloodHound CE.
    mismatched = neo4j_session.run(
        "MATCH (n:ADObject) WHERE n.objectid IS NULL OR n.objectid <> n.id "
        "RETURN count(n) AS c",
    ).single()["c"]
    assert mismatched == 0
    # Principals from the trusted domain are placeholders.
    assert check_nodes(
        neo4j_session,
        "ADUser",
        ["id", "samaccountname", "collected"],
    ) == {
        (fixture.ALICE_SID, "alice", True),
        (fixture.SVC_SID, "svc_app", True),
        (fixture.PARTNER_USER_SID, None, False),
    }
    assert check_nodes(neo4j_session, "ADGroup", ["id", "collected"]) == {
        (fixture.DOMAIN_USERS_SID, True),
        (fixture.DOMAIN_COMPUTERS_SID, True),
        (fixture.HELPDESK_SID, True),
        (fixture.PARTNER_ADMINS_SID, False),
    }
    assert check_nodes(neo4j_session, "ADComputer", ["id", "hostname"]) == {
        (fixture.WS01_SID, "WS01"),
    }
    assert check_nodes(neo4j_session, "ADOU", ["id"]) == {(fixture.WORKSTATIONS_OU,)}
    assert check_nodes(neo4j_session, "ADGPO", ["id"]) == {(fixture.DEFAULT_GPO,)}
    assert check_nodes(neo4j_session, "ADContainer", ["id"]) == {
        (fixture.USERS_CONTAINER,),
    }
    assert check_rels(
        neo4j_session,
        "ADDomain",
        "id",
        "ADUser",
        "id",
        "RESOURCE",
    ) == {
        (fixture.DOMAIN_SID, fixture.ALICE_SID),
        (fixture.DOMAIN_SID, fixture.SVC_SID),
    }


def test_sync_records_provenance_and_ontology(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    alice = neo4j_session.run(
        "MATCH (u:ADUser:ADObject:UserAccount {id: $id}) RETURN u",
        id=fixture.ALICE_SID,
    ).single()["u"]
    assert alice["source_uri"] == f"{archive}!20261012143015_users.json"
    assert alice["collected_at"] == fixture.COLLECTED_AT
    assert alice["collector_version"] == fixture.COLLECTOR_VERSION
    assert alice["_ont_email"] == "alice@example.test"
    assert alice["_ont_source"] == "bloodhound"
    assert "userpassword" not in alice
    assert check_nodes(neo4j_session, "Tenant", ["id"]) >= {(fixture.DOMAIN_SID,)}
    assert check_nodes(neo4j_session, "UserGroup", ["id"]) >= {
        (fixture.HELPDESK_SID,),
    }
    rel = neo4j_session.run(
        "MATCH (:ADUser {id: $user})-[r:MEMBER_OF]->(:ADGroup {id: $group}) RETURN r",
        user=fixture.ALICE_SID,
        group=fixture.HELPDESK_SID,
    ).single()["r"]
    assert rel["collected_at"] == fixture.COLLECTED_AT
    assert rel["source_uri"] == f"{archive}!20261012143015_groups.json"


def test_sync_imports_structural_edges(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    _sync(neo4j_session, archive)

    # Assert
    assert check_rels(
        neo4j_session,
        "ADObject",
        "id",
        "ADGroup",
        "id",
        "MEMBER_OF",
    ) == {
        (fixture.ALICE_SID, fixture.HELPDESK_SID),
        (fixture.ALICE_SID, fixture.DOMAIN_USERS_SID),
        (fixture.SVC_SID, fixture.DOMAIN_USERS_SID),
        (fixture.WS01_SID, fixture.DOMAIN_COMPUTERS_SID),
    }
    assert check_rels(
        neo4j_session,
        "ADObject",
        "id",
        "ADObject",
        "id",
        "CONTAINS",
    ) == {
        (fixture.DOMAIN_SID, fixture.WORKSTATIONS_OU),
        (fixture.DOMAIN_SID, fixture.USERS_CONTAINER),
        (fixture.WORKSTATIONS_OU, fixture.WS01_SID),
        (fixture.USERS_CONTAINER, fixture.ALICE_SID),
        (fixture.USERS_CONTAINER, fixture.SVC_SID),
        (fixture.USERS_CONTAINER, fixture.DOMAIN_USERS_SID),
        (fixture.USERS_CONTAINER, fixture.DOMAIN_COMPUTERS_SID),
        (fixture.USERS_CONTAINER, fixture.HELPDESK_SID),
    }
    assert check_rels(
        neo4j_session,
        "ADGPO",
        "id",
        "ADObject",
        "id",
        "GP_LINK",
        rel_direction_right=True,
    ) == {
        (fixture.DEFAULT_GPO, fixture.DOMAIN_SID),
        (fixture.DEFAULT_GPO, fixture.WORKSTATIONS_OU),
    }
    enforced = neo4j_session.run(
        "MATCH (:ADGPO)-[r:GP_LINK]->(:ADOU) RETURN r.enforced AS enforced",
    ).single()["enforced"]
    assert enforced is True
    # EXAMPLE.TEST has an outbound external trust: it trusts PARTNER.TEST.
    assert check_rels(
        neo4j_session,
        "ADDomain",
        "id",
        "ADDomain",
        "id",
        "CROSS_FOREST_TRUST",
    ) == {(fixture.DOMAIN_SID, fixture.PARTNER_SID)}
    trust = neo4j_session.run(
        "MATCH (:ADDomain)-[r:CROSS_FOREST_TRUST]->(:ADDomain) RETURN r",
    ).single()["r"]
    assert trust["trust_type"] == "External"
    assert trust["sid_filtering_enabled"] is True


def test_reimport_keeps_identity_and_removes_stale_objects(neo4j_session, tmp_path):
    # Arrange
    first = fixture.write_zip(tmp_path / "first" / "20261012143015_BloodHound.zip")
    _sync(neo4j_session, first)
    data = fixture.collection()
    data["users"] = [
        u for u in data["users"] if u["ObjectIdentifier"] != fixture.SVC_SID
    ]
    data["containers"][0]["ChildObjects"] = [
        c
        for c in data["containers"][0]["ChildObjects"]
        if c["ObjectIdentifier"] != fixture.SVC_SID
    ]
    data["groups"][2]["Members"] = []
    second = fixture.write_zip(
        tmp_path / "second" / "20261013090000_BloodHound.zip",
        data,
        timestamp="20261013090000",
    )

    # Act
    _sync(neo4j_session, second, NEXT_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ADUser",
        ["id", "lastupdated", "collected_at"],
    ) == {(fixture.ALICE_SID, NEXT_UPDATE_TAG, "2026-10-13T09:00:00")}
    assert (
        fixture.ALICE_SID,
        fixture.HELPDESK_SID,
    ) not in check_rels(
        neo4j_session,
        "ADObject",
        "id",
        "ADGroup",
        "id",
        "MEMBER_OF",
    )


def test_failed_import_keeps_previous_graph(neo4j_session, tmp_path):
    # Arrange
    first = fixture.write_zip(tmp_path / "first" / "20261012143015_BloodHound.zip")
    _sync(neo4j_session, first)
    data = fixture.collection()
    data.pop("users")
    users = json.dumps(fixture.document("users", fixture.collection()["users"]))
    broken = fixture.write_zip(
        tmp_path / "second" / "20261013090000_BloodHound.zip",
        data,
        timestamp="20261013090000",
        raw_members={"20261013090000_users.json": users[:-40].encode()},
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="users.json"):
        _sync(neo4j_session, broken, NEXT_UPDATE_TAG)
    assert check_nodes(neo4j_session, "ADUser", ["id", "lastupdated"]) == {
        (fixture.ALICE_SID, TEST_UPDATE_TAG),
        (fixture.SVC_SID, TEST_UPDATE_TAG),
        (fixture.PARTNER_USER_SID, TEST_UPDATE_TAG),
    }
    assert check_nodes(neo4j_session, "ADGroup", ["lastupdated"]) == {
        (TEST_UPDATE_TAG,),
    }
    member_of = neo4j_session.run(
        "MATCH ()-[r:MEMBER_OF]->() RETURN count(r) AS c",
    ).single()["c"]
    assert member_of == 4


def test_partial_collection_keeps_uncollected_edges(neo4j_session, tmp_path):
    # Arrange
    first = fixture.write_zip(tmp_path / "first" / "20261012143015_BloodHound.zip")
    _sync(neo4j_session, first)
    data = fixture.collection()
    data["domains"][0]["Trusts"] = []
    without_trusts = fixture.write_zip(
        tmp_path / "second" / "20261013090000_BloodHound.zip",
        data,
        timestamp="20261013090000",
        methods=int(CollectionMethod.GROUP | CollectionMethod.CONTAINER),
    )

    # Act
    _sync(neo4j_session, without_trusts, NEXT_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        "ADDomain",
        "id",
        "ADDomain",
        "id",
        "CROSS_FOREST_TRUST",
    ) == {(fixture.DOMAIN_SID, fixture.PARTNER_SID)}


def test_placeholder_does_not_overwrite_imported_domain(neo4j_session, tmp_path):
    # Arrange: import the partner domain first, as a real collection.
    partner = fixture.collection()
    partner_domain = partner["domains"][0]
    partner_domain["ObjectIdentifier"] = fixture.PARTNER_SID
    partner_domain["Properties"]["name"] = fixture.PARTNER_NAME
    partner_domain["Properties"]["functionallevel"] = "2012"
    partner_domain["Trusts"] = []
    for data_type in ("users", "groups", "computers", "ous", "gpos", "containers"):
        partner[data_type] = []
    partner["users"] = [
        {
            **fixture.collection()["users"][0],
            "ObjectIdentifier": f"{fixture.PARTNER_SID}-1105",
            "Properties": {
                "name": f"BOB@{fixture.PARTNER_NAME}",
                "domainsid": fixture.PARTNER_SID,
            },
            "PrimaryGroupSID": None,
        },
    ]
    partner["groups"] = [
        {
            **fixture.collection()["groups"][0],
            "ObjectIdentifier": f"{fixture.PARTNER_SID}-513",
            "Properties": {"name": "G", "domainsid": fixture.PARTNER_SID},
            "Members": [],
        },
    ]
    partner["computers"] = [
        {
            **fixture.collection()["computers"][0],
            "ObjectIdentifier": f"{fixture.PARTNER_SID}-1201",
            "Properties": {
                "name": "SRV.PARTNER.TEST",
                "domainsid": fixture.PARTNER_SID,
            },
            "PrimaryGroupSID": None,
        },
    ]
    _sync(
        neo4j_session,
        fixture.write_zip(
            tmp_path / "p" / "20261001000000_BloodHound.zip",
            partner,
            timestamp="20261001000000",
        ),
    )

    # Act
    _sync(
        neo4j_session,
        fixture.write_zip(tmp_path / "e" / "20261012143015_BloodHound.zip"),
        NEXT_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ADDomain",
        ["id", "collected", "functionallevel"],
    ) == {
        (fixture.DOMAIN_SID, True, "2016"),
        (fixture.PARTNER_SID, True, "2012"),
    }
    assert check_nodes(neo4j_session, "ADUser", ["id"]) >= {
        (f"{fixture.PARTNER_SID}-1105",),
    }


def test_sync_reads_archives_from_object_store(neo4j_session, tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")
    ref = ReportRef(
        "s3://example-bucket/bloodhound/20261012143015_BloodHound.zip",
        "bloodhound/20261012143015_BloodHound.zip",
    )
    reader = ListedReportReader(
        "s3://example-bucket/bloodhound/",
        [ref],
        lambda _ref: archive.read_bytes(),
    )

    # Act
    sync(neo4j_session, reader, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "ADUser", ["id", "source_uri"]) == {
        (fixture.ALICE_SID, f"{ref.uri}!20261012143015_users.json"),
        (fixture.SVC_SID, f"{ref.uri}!20261012143015_users.json"),
        (fixture.PARTNER_USER_SID, None),
    }


def test_omitted_files_keep_their_edges(neo4j_session, tmp_path):
    # Arrange
    first = fixture.write_zip(tmp_path / "first" / "20261012143015_BloodHound.zip")
    _sync(neo4j_session, first)
    data = fixture.collection()
    del data["ous"]
    del data["containers"]
    second = fixture.write_zip(
        tmp_path / "second" / "20261013090000_BloodHound.zip",
        data,
        timestamp="20261013090000",
    )

    # Act
    _sync(neo4j_session, second, NEXT_UPDATE_TAG)

    # Assert
    contains = check_rels(
        neo4j_session,
        "ADObject",
        "id",
        "ADObject",
        "id",
        "CONTAINS",
    )
    assert (fixture.WORKSTATIONS_OU, fixture.WS01_SID) in contains
    assert (fixture.USERS_CONTAINER, fixture.ALICE_SID) in contains
    assert (fixture.DEFAULT_GPO, fixture.WORKSTATIONS_OU) in check_rels(
        neo4j_session,
        "ADGPO",
        "id",
        "ADObject",
        "id",
        "GP_LINK",
    )
    assert check_nodes(neo4j_session, "ADOU", ["id", "lastupdated"]) == {
        (fixture.WORKSTATIONS_OU, TEST_UPDATE_TAG),
    }


def test_empty_file_removes_stale_objects_of_its_type(neo4j_session, tmp_path):
    # Arrange
    first = fixture.write_zip(tmp_path / "first" / "20261012143015_BloodHound.zip")
    _sync(neo4j_session, first)
    data = fixture.collection()
    data["gpos"] = []
    data["domains"][0]["Links"] = []
    data["ous"][0]["Links"] = []
    second = fixture.write_zip(
        tmp_path / "second" / "20261013090000_BloodHound.zip",
        data,
        timestamp="20261013090000",
    )

    # Act
    _sync(neo4j_session, second, NEXT_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "ADGPO", ["id"]) == set()


def test_duplicate_domain_records_are_merged(neo4j_session, tmp_path):
    # Arrange: a partial record without a name after the full one.
    data = fixture.collection()
    data["domains"].append(
        {
            **data["domains"][0],
            "Properties": {"domainsid": fixture.DOMAIN_SID},
            "Trusts": [],
        },
    )
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip", data)

    # Act
    _sync(neo4j_session, archive)

    # Assert
    assert (
        fixture.DOMAIN_SID,
        fixture.DOMAIN_NAME,
        "2016",
    ) in check_nodes(neo4j_session, "ADDomain", ["id", "name", "functionallevel"])
