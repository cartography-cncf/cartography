import datetime
import json
from collections import Counter
from pathlib import Path

import pytest

from cartography.intel.bloodhound.collection import BloodHoundImportError
from cartography.intel.bloodhound.collection import open_collection
from cartography.intel.bloodhound.collection import timestamp_from_filename
from cartography.intel.bloodhound.parser import CollectionMethod
from cartography.intel.bloodhound.parser import iter_edges
from cartography.intel.bloodhound.parser import placeholder_domain
from cartography.intel.bloodhound.parser import Provenance
from cartography.intel.bloodhound.parser import transform_node
from cartography.intel.bloodhound.parser import uncollected_host_edges
from cartography.intel.bloodhound.parser import validate_collection
from cartography.intel.common.object_store import LocalReportReader
from tests.data.bloodhound import collection as fixture

PROVENANCE = Provenance("test://source", fixture.COLLECTED_AT, "2.5.0.0")


def _validate(path: Path, collected_at: str | None = None):
    with open_collection(LocalReportReader(str(path))) as files:
        return validate_collection(files, collected_at)


def test_validate_collection_reads_zip_metadata(tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    collection = _validate(archive)

    # Assert
    assert {f.data_type for f in collection.files} == {
        "domains",
        "users",
        "groups",
        "computers",
        "ous",
        "gpos",
        "containers",
    }
    assert collection.domains == {fixture.DOMAIN_SID: fixture.DOMAIN_NAME}
    assert collection.trust_targets == {fixture.PARTNER_SID: fixture.PARTNER_NAME}
    users_file = collection.files_of("users")[0]
    assert users_file.provenance == Provenance(
        f"{archive}!20261012143015_users.json",
        fixture.COLLECTED_AT,
        fixture.COLLECTOR_VERSION,
    )


def test_validate_collection_accepts_loose_json_with_bom(tmp_path):
    # Arrange
    for data_type, objects in fixture.collection().items():
        content = json.dumps(fixture.document(data_type, objects)).encode()
        (tmp_path / f"20261012143015_{data_type}.json").write_bytes(
            b"\xef\xbb\xbf" + content,
        )

    # Act
    collection = _validate(tmp_path)

    # Assert
    assert len(collection.files) == 7


def test_validate_collection_rejects_truncated_file(tmp_path):
    # Arrange
    data = fixture.collection()
    users = json.dumps(fixture.document("users", data.pop("users")))
    archive = fixture.write_zip(
        tmp_path / "a.zip",
        data,
        raw_members={"20261012143015_users.json": users[: len(users) // 2].encode()},
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="users.json"):
        _validate(archive)


def test_validate_collection_rejects_count_mismatch(tmp_path):
    # Arrange
    data = fixture.collection()
    users = fixture.document("users", data.pop("users"), count=5)
    archive = fixture.write_zip(
        tmp_path / "a.zip",
        data,
        raw_members={"20261012143015_users.json": json.dumps(users).encode()},
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="contains 2 objects"):
        _validate(archive)


def test_validate_collection_rejects_legacy_version(tmp_path):
    # Arrange
    data = fixture.collection()
    users = fixture.document("users", data.pop("users"), version=5)
    archive = fixture.write_zip(
        tmp_path / "a.zip",
        data,
        raw_members={"20261012143015_users.json": json.dumps(users).encode()},
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="version 5"):
        _validate(archive)


def test_validate_collection_rejects_missing_required_type(tmp_path):
    # Arrange
    data = fixture.collection()
    del data["computers"]
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="missing computers"):
        _validate(archive)


def test_validate_collection_rejects_object_from_unknown_domain(tmp_path):
    # Arrange
    data = fixture.collection()
    data["users"][0]["Properties"]["domainsid"] = fixture.PARTNER_SID
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match=fixture.PARTNER_SID):
        _validate(archive)


def test_validate_collection_rejects_malformed_edge(tmp_path):
    # Arrange
    data = fixture.collection()
    data["groups"][2]["Members"] = [{"ObjectType": "User"}]
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="Malformed groups object #3"):
        _validate(archive)


def test_validate_collection_rejects_duplicate_domain(tmp_path):
    # Arrange
    fixture.write_zip(tmp_path / "a" / "20261012143015_BloodHound.zip")
    fixture.write_zip(tmp_path / "b" / "20261012143015_BloodHound.zip")

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="same collection time"):
        _validate(tmp_path)


def test_validate_collection_rejects_bad_zip(tmp_path):
    # Arrange
    (tmp_path / "20261012143015_BloodHound.zip").write_bytes(b"not a zip")

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="not a readable zip"):
        _validate(tmp_path)


def test_validate_collection_requires_timestamp(tmp_path):
    # Arrange
    for data_type, objects in fixture.collection().items():
        (tmp_path / f"{data_type}.json").write_text(
            json.dumps(fixture.document(data_type, objects)),
        )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="--bloodhound-collected-at"):
        _validate(tmp_path)
    collection = _validate(tmp_path, collected_at="2026-10-01T08:00:00")
    assert collection.files[0].provenance.collected_at == "2026-10-01T08:00:00"


def test_was_collected_honors_collection_methods(tmp_path):
    # Arrange
    archive = fixture.write_zip(
        tmp_path / "a.zip",
        methods=int(CollectionMethod.GROUP | CollectionMethod.OBJECT_PROPS),
    )

    # Act
    collection = _validate(archive)

    # Assert
    assert collection.was_collected(fixture.DOMAIN_SID, CollectionMethod.GROUP)
    assert not collection.was_collected(fixture.DOMAIN_SID, CollectionMethod.TRUSTS)


def test_was_collected_treats_unreported_methods_as_full(tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "a.zip", methods=0)

    # Act
    collection = _validate(archive)

    # Assert
    assert collection.was_collected(fixture.DOMAIN_SID, CollectionMethod.TRUSTS)


def test_timestamp_from_filename():
    assert timestamp_from_filename("20261012143015_users.json") == fixture.COLLECTED_AT
    assert timestamp_from_filename("dir/20261012143015_BloodHound.zip") == (
        fixture.COLLECTED_AT
    )
    assert timestamp_from_filename("users.json") is None
    assert timestamp_from_filename("20261399999999_users.json") is None


def test_transform_node_keeps_allowlisted_properties_only():
    # Arrange
    alice = fixture.collection()["users"][0]

    # Act
    node = transform_node("users", alice, PROVENANCE)

    # Assert
    assert node["id"] == fixture.ALICE_SID
    assert node["email"] == "alice@example.test"
    assert node["primarygroupsid"] == fixture.DOMAIN_USERS_SID
    assert node["collected_at"] == fixture.COLLECTED_AT
    assert "userpassword" not in node


def test_transform_node_derives_computer_hostname():
    # Act
    node = transform_node("computers", fixture.collection()["computers"][0], PROVENANCE)

    # Assert
    assert node["hostname"] == "WS01"
    assert node["isdc"] is False


def test_iter_edges_membership_and_structure():
    # Arrange
    data = fixture.collection()

    # Act
    edges = [
        (kind, row["source_id"], row["target_id"])
        for data_type, objects in data.items()
        for obj in objects
        for kind, row in iter_edges(data_type, obj, PROVENANCE)
    ]

    # Assert
    assert ("MEMBER_OF", fixture.ALICE_SID, fixture.HELPDESK_SID) in edges
    assert ("MEMBER_OF", fixture.ALICE_SID, fixture.DOMAIN_USERS_SID) in edges
    assert ("MEMBER_OF", fixture.WS01_SID, fixture.DOMAIN_COMPUTERS_SID) in edges
    assert ("CONTAINS", fixture.WORKSTATIONS_OU, fixture.WS01_SID) in edges
    assert ("CONTAINS", fixture.DOMAIN_SID, fixture.USERS_CONTAINER) in edges
    assert ("GP_LINK", fixture.DEFAULT_GPO, fixture.WORKSTATIONS_OU) in edges
    assert ("GP_LINK", fixture.DEFAULT_GPO, fixture.DOMAIN_SID) in edges


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        ("Outbound", [("DOMAIN", "PARTNER")]),
        ("Inbound", [("PARTNER", "DOMAIN")]),
        (3, [("DOMAIN", "PARTNER"), ("PARTNER", "DOMAIN")]),
        ("Disabled", []),
    ],
)
def test_iter_edges_trust_direction(direction, expected):
    # Arrange
    domain = fixture.collection()["domains"][0]
    domain["Trusts"][0]["TrustDirection"] = direction
    names = {fixture.DOMAIN_SID: "DOMAIN", fixture.PARTNER_SID: "PARTNER"}

    # Act
    trusts = [
        row
        for kind, row in iter_edges("domains", domain, PROVENANCE)
        if kind == "CROSS_FOREST_TRUST"
    ]

    # Assert
    assert sorted((names[r["source_id"]], names[r["target_id"]]) for r in trusts) == (
        expected
    )
    for row in trusts:
        assert row["trust_type"] == "External"


@pytest.mark.parametrize(
    ("trust_type", "kind"),
    [
        ("ParentChild", "SAME_FOREST_TRUST"),
        ("TreeRoot", "SAME_FOREST_TRUST"),
        ("CrossLink", "SAME_FOREST_TRUST"),
        # BloodHound CE treats every other type as cross-forest.
        ("Shortcut", "CROSS_FOREST_TRUST"),
        ("Realm", "CROSS_FOREST_TRUST"),
        ("Forest", "CROSS_FOREST_TRUST"),
        (3, "CROSS_FOREST_TRUST"),
    ],
)
def test_iter_edges_trust_kind_follows_bloodhound(trust_type, kind):
    # Arrange
    domain = fixture.collection()["domains"][0]
    domain["Trusts"][0]["TrustType"] = trust_type

    # Act
    kinds = [
        k for k, _ in iter_edges("domains", domain, PROVENANCE) if k.endswith("_TRUST")
    ]

    # Assert
    assert kinds == [kind]


def _replace_member(tmp_path, data_type: str, document: dict) -> Path:
    data = fixture.collection()
    data.pop(data_type)
    return fixture.write_zip(
        tmp_path / "a.zip",
        data,
        raw_members={
            f"20261012143015_{data_type}.json": json.dumps(document).encode(),
        },
    )


def test_validate_collection_rejects_missing_data_array(tmp_path):
    # Arrange
    archive = _replace_member(
        tmp_path,
        "ous",
        {"meta": fixture.document("ous", [])["meta"]},
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="no data array"):
        _validate(archive)


def test_validate_collection_rejects_missing_type(tmp_path):
    # Arrange
    document = fixture.document("ous", fixture.collection()["ous"])
    del document["meta"]["type"]
    archive = _replace_member(tmp_path, "ous", document)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="no data type"):
        _validate(archive)


@pytest.mark.parametrize("methods", ["all", -1, 1.5, True])
def test_validate_collection_rejects_invalid_methods(tmp_path, methods):
    # Arrange
    document = fixture.document("ous", fixture.collection()["ous"])
    document["meta"]["methods"] = methods
    archive = _replace_member(tmp_path, "ous", document)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="collection-method mask"):
        _validate(archive)


def test_deleted_objects_count_toward_collected_scope(tmp_path):
    # Arrange
    data = fixture.collection()
    data["gpos"][0]["IsDeleted"] = True
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act
    collection = _validate(archive)

    # Assert
    assert ("gpos", fixture.DOMAIN_SID) in collection.collected_types


def test_zip_without_timestamp_prefix_requires_override(tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "BloodHound.zip", timestamp="custom")

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="--bloodhound-collected-at"):
        _validate(archive)


def test_transform_node_converts_epoch_seconds():
    # Arrange
    alice = fixture.collection()["users"][0]
    alice["Properties"]["lastlogon"] = -1

    # Act
    node = transform_node("users", alice, PROVENANCE)

    # Assert
    assert node["whencreated"] == datetime.datetime(
        2023, 11, 14, 22, 13, 20, tzinfo=datetime.timezone.utc
    )
    assert node["lastlogon"] is None


def test_transform_node_falls_back_to_typed_sid_history():
    # Arrange
    alice = fixture.collection()["users"][0]
    old_sid = f"{fixture.PARTNER_SID}-2001"
    alice["HasSIDHistory"] = [{"ObjectIdentifier": old_sid, "ObjectType": "User"}]

    # Act
    node = transform_node("users", alice, PROVENANCE)

    # Assert
    assert node["sidhistory"] == [old_sid]


@pytest.mark.parametrize("value", ["yesterday", True, 10**15, 1e300])
def test_validate_collection_rejects_malformed_epoch(tmp_path, value):
    # Arrange
    data = fixture.collection()
    data["users"][0]["Properties"]["pwdlastset"] = value
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="Malformed users object #1"):
        _validate(archive)


def test_iter_edges_derives_contains_from_contained_by():
    # Arrange: current SharpHound leaves ChildObjects empty.
    data = fixture.collection()
    for data_type in ("domains", "ous", "containers"):
        for obj in data[data_type]:
            obj["ChildObjects"] = []

    # Act
    contains = {
        (row["source_id"], row["target_id"])
        for data_type, objects in data.items()
        for obj in objects
        for kind, row in iter_edges(data_type, obj, PROVENANCE)
        if kind == "CONTAINS"
    }

    # Assert
    assert (fixture.WORKSTATIONS_OU, fixture.WS01_SID) in contains
    assert (fixture.USERS_CONTAINER, fixture.ALICE_SID) in contains
    assert (fixture.DOMAIN_SID, fixture.WORKSTATIONS_OU) in contains


def test_validate_collection_merges_duplicate_domain_records(tmp_path):
    # Arrange
    data = fixture.collection()
    partial = {**data["domains"][0], "Properties": {"domainsid": fixture.DOMAIN_SID}}
    data["domains"].append(partial)
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act
    collection = _validate(archive)

    # Assert
    assert collection.domains == {fixture.DOMAIN_SID: fixture.DOMAIN_NAME}


def test_validate_collection_rejects_conflicting_domain_records(tmp_path):
    # Arrange
    data = fixture.collection()
    conflicting = {
        **data["domains"][0],
        "Properties": {**data["domains"][0]["Properties"], "functionallevel": "2012"},
    }
    data["domains"].append(conflicting)
    archive = fixture.write_zip(tmp_path / "a.zip", data)

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="conflicting functionallevel"):
        _validate(archive)


def _edges(data_type, obj, skipped_rights=None):
    return {
        (kind, row["source_id"], row["target_id"])
        for kind, row in iter_edges(data_type, obj, PROVENANCE, skipped_rights)
    }


def _domain():
    return fixture.collection()["domains"][0]


def _computer():
    return fixture.collection()["computers"][0]


def test_iter_edges_dcsync_needs_both_replication_rights():
    # Arrange
    domain = _domain()

    # Act
    edges = _edges("domains", domain)

    # Assert
    assert ("DC_SYNC", fixture.PARTNER_ADMINS_SID, fixture.DOMAIN_SID) in edges
    assert not any(e[0] == "DC_SYNC" and e[1] == fixture.SVC_SID for e in edges)


def test_iter_edges_dcsync_only_on_domains():
    # Arrange
    user = fixture.collection()["users"][0]
    user["Aces"] = [
        {"PrincipalSID": fixture.SVC_SID, "PrincipalType": "User", "RightName": r}
        for r in ("GetChanges", "GetChangesAll")
    ]
    skipped = Counter()

    # Act
    edges = _edges("users", user, skipped)

    # Assert
    assert edges.isdisjoint({("DC_SYNC", fixture.SVC_SID, fixture.ALICE_SID)})
    assert skipped == Counter({"GetChanges": 1, "GetChangesAll": 1})


def test_iter_edges_skips_owner_rights_self_and_unmapped_rights():
    # Arrange
    domain = _domain()
    domain["Aces"].append(
        {
            "PrincipalSID": f"{fixture.DOMAIN_NAME}-S-1-3-4",
            "PrincipalType": "Group",
            "RightName": "WriteDacl",
        },
    )
    domain["Aces"].append(
        {
            "PrincipalSID": fixture.DOMAIN_SID,
            "PrincipalType": "Domain",
            "RightName": "GenericAll",
        },
    )
    skipped = Counter()

    # Act
    edges = _edges("domains", domain, skipped)

    # Assert
    acl = {e for e in edges if e[0] in ("GENERIC_ALL", "WRITE_DACL")}
    assert acl == {("GENERIC_ALL", fixture.PARTNER_ADMINS_SID, fixture.DOMAIN_SID)}
    assert skipped == Counter({"WriteGPLink": 1})


def test_iter_edges_ace_inheritance_prefers_direct_grant():
    # Arrange
    alice = fixture.collection()["users"][0]

    # Act
    rows = {
        kind: row
        for kind, row in iter_edges("users", alice, PROVENANCE)
        if kind in ("FORCE_CHANGE_PASSWORD", "GENERIC_WRITE")
    }

    # Assert
    assert rows["FORCE_CHANGE_PASSWORD"]["is_inherited"] is False
    assert rows["GENERIC_WRITE"]["is_inherited"] is True
    assert rows["GENERIC_WRITE"]["source_type"] == "Group"


def test_iter_edges_rdp_without_user_rights_uses_group_membership():
    # Arrange
    computer = _computer()
    computer["UserRights"] = []

    # Act
    edges = _edges("computers", computer)

    # Assert
    assert {e for e in edges if e[0] == "CAN_RDP"} == {
        ("CAN_RDP", fixture.DOMAIN_USERS_SID, fixture.WS01_SID),
        ("CAN_RDP", fixture.ALICE_SID, fixture.WS01_SID),
    }


def test_iter_edges_rdp_when_group_holds_logon_right():
    # Arrange
    computer = _computer()
    computer["UserRights"][0]["Results"] = [
        {"ObjectIdentifier": f"{fixture.WS01_SID}-555", "ObjectType": "LocalGroup"},
    ]

    # Act
    edges = _edges("computers", computer)

    # Assert
    assert {e for e in edges if e[0] == "CAN_RDP"} == {
        ("CAN_RDP", fixture.DOMAIN_USERS_SID, fixture.WS01_SID),
        ("CAN_RDP", fixture.ALICE_SID, fixture.WS01_SID),
    }


def test_iter_edges_skips_uncollected_local_groups_and_sessions():
    # Arrange
    computer = _computer()
    for group in computer["LocalGroups"]:
        group["Collected"] = False
    computer["Sessions"]["Collected"] = False
    computer["RegistrySessions"]["Collected"] = False

    # Act
    edges = _edges("computers", computer)

    # Assert
    assert {e[0] for e in edges} & {"ADMIN_TO", "CAN_RDP", "CAN_PS_REMOTE"} == set()
    assert {e for e in edges if e[0] == "HAS_SESSION"} == {
        ("HAS_SESSION", fixture.WS01_SID, fixture.SVC_SID),
    }
    assert set(uncollected_host_edges(computer)) == {
        "ADMIN_TO",
        "CAN_RDP",
        "CAN_PS_REMOTE",
    }


def test_uncollected_host_edges_for_unreachable_computer():
    # Arrange
    computer = _computer()
    computer["LocalGroups"] = []
    for name in ("Sessions", "PrivilegedSessions", "RegistrySessions"):
        computer[name] = {"Collected": False, "Results": []}

    # Act and assert
    assert set(uncollected_host_edges(computer)) == {
        "ADMIN_TO",
        "CAN_RDP",
        "CAN_PS_REMOTE",
        "HAS_SESSION",
    }
    assert uncollected_host_edges(_computer()) == []


def test_iter_edges_gpo_local_groups_reach_affected_computers():
    # Arrange
    ou = fixture.collection()["ous"][0]
    ou["GPOChanges"]["PSRemoteUsers"] = [
        {"ObjectIdentifier": fixture.HELPDESK_SID, "ObjectType": "Group"},
        {"ObjectIdentifier": "S-1-5-21-1-2-3-500", "ObjectType": "LocalUser"},
    ]

    # Act
    edges = _edges("ous", ou)

    # Assert
    assert {e for e in edges if e[0] in ("ADMIN_TO", "CAN_PS_REMOTE")} == {
        ("ADMIN_TO", fixture.SVC_SID, fixture.WS01_SID),
        ("CAN_PS_REMOTE", fixture.HELPDESK_SID, fixture.WS01_SID),
    }


@pytest.mark.parametrize(
    ("principal_id", "expected"),
    [
        (
            "S-1-5-21-1-2-3-1105",
            {"domainsid": "S-1-5-21-1-2-3", "domain": None},
        ),
        (
            "EXAMPLE.TEST-S-1-5-32-544",
            {"domainsid": None, "domain": "EXAMPLE.TEST"},
        ),
        ("S-1-5-11", {"domainsid": None, "domain": None}),
    ],
)
def test_placeholder_domain(principal_id, expected):
    assert placeholder_domain(principal_id) == expected


def test_validate_collection_records_referenced_principals(tmp_path):
    # Arrange
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")

    # Act
    collection = _validate(archive)

    # Assert
    assert collection.referenced_principals[fixture.PARTNER_ADMINS_SID] == "ADGroup"
    assert collection.referenced_principals[fixture.PARTNER_USER_SID] == "ADUser"
    assert collection.referenced_principals[fixture.HELPDESK_SID] == "ADGroup"
    # Local accounts and OWNER RIGHTS are never placeholders.
    assert fixture.WS01_LOCAL_ADMIN_SID not in collection.referenced_principals
    assert "S-1-3-4" not in collection.referenced_principals
    assert dict(collection.uncollected_hosts) == {}


def test_validate_collection_skips_placeholder_for_filtered_gpo_rdp(tmp_path):
    # Arrange
    outsider = f"{fixture.PARTNER_SID}-1600"
    data = fixture.collection()
    data["ous"][0]["GPOChanges"]["RemoteDesktopUsers"] = [
        {"ObjectIdentifier": outsider, "ObjectType": "User"},
    ]
    archive = fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip", data)

    # Act
    collection = _validate(archive)

    # Assert
    # WS01's user rights grant the logon right to Alice only.
    assert outsider not in collection.referenced_principals
    assert not collection.allows_rdp(outsider, fixture.WS01_SID)
    assert collection.allows_rdp(fixture.ALICE_SID, fixture.WS01_SID)


def _partner_data():
    sid = fixture.PARTNER_SID
    return {
        "domains": [
            {
                "ObjectIdentifier": sid,
                "Properties": {"name": fixture.PARTNER_NAME, "domainsid": sid},
                "Aces": [],
                "IsDeleted": False,
                "Trusts": [],
            },
        ],
        "users": [
            {
                "ObjectIdentifier": fixture.PARTNER_USER_SID,
                "Properties": {"name": "MIGRATED", "domainsid": sid},
                "Aces": [],
                "IsDeleted": False,
            },
        ],
        "groups": [],
        "computers": [],
    }


def test_validate_collection_imports_newest_collection_per_domain(tmp_path):
    # Arrange
    fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")
    fixture.write_zip(
        tmp_path / "20261013090000_BloodHound.zip",
        timestamp="20261013090000",
    )

    # Act
    collection = _validate(tmp_path)

    # Assert
    assert {f.provenance.collected_at for f in collection.files} == {
        "2026-10-13T09:00:00",
    }
    assert len(collection.files) == 7


def test_validate_collection_keeps_collections_of_other_domains(tmp_path):
    # Arrange
    fixture.write_zip(tmp_path / "20261012143015_example.zip")
    fixture.write_zip(
        tmp_path / "20261013090000_partner.zip",
        _partner_data(),
        timestamp="20261013090000",
    )

    # Act
    collection = _validate(tmp_path)

    # Assert
    assert set(collection.domains) == {fixture.DOMAIN_SID, fixture.PARTNER_SID}


def test_validate_collection_selects_newest_loose_json(tmp_path):
    # Arrange
    for timestamp in ("20261012143015", "20261013090000"):
        for data_type, objects in fixture.collection().items():
            (tmp_path / f"{timestamp}_{data_type}.json").write_text(
                json.dumps(fixture.document(data_type, objects)),
            )

    # Act
    collection = _validate(tmp_path)

    # Assert
    assert {f.provenance.collected_at for f in collection.files} == {
        "2026-10-13T09:00:00",
    }


def test_validate_collection_rejects_partly_superseded_collection(tmp_path):
    # Arrange
    both = fixture.collection()
    for data_type, objects in _partner_data().items():
        both[data_type] = both[data_type] + objects
    fixture.write_zip(tmp_path / "20261012143015_forest.zip", both)
    fixture.write_zip(
        tmp_path / "20261013090000_example.zip",
        timestamp="20261013090000",
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="newest collection of some"):
        _validate(tmp_path)


def test_validate_collection_cannot_order_runs_with_one_override(tmp_path):
    # Arrange
    fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")
    fixture.write_zip(
        tmp_path / "20261013090000_BloodHound.zip",
        timestamp="20261013090000",
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="same collection time"):
        _validate(tmp_path, "2026-10-14T00:00:00")
