import datetime
import json
from pathlib import Path

import pytest

from cartography.intel.bloodhound.collection import BloodHoundImportError
from cartography.intel.bloodhound.collection import open_collection
from cartography.intel.bloodhound.collection import timestamp_from_filename
from cartography.intel.bloodhound.parser import CollectionMethod
from cartography.intel.bloodhound.parser import iter_edges
from cartography.intel.bloodhound.parser import Provenance
from cartography.intel.bloodhound.parser import transform_node
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
    fixture.write_zip(tmp_path / "20261012143015_BloodHound.zip")
    fixture.write_zip(
        tmp_path / "20261013090000_BloodHound.zip",
        timestamp="20261013090000",
    )

    # Act and assert
    with pytest.raises(BloodHoundImportError, match="Import one collection per domain"):
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
        ("Outbound", [("PARTNER", "DOMAIN")]),
        ("Inbound", [("DOMAIN", "PARTNER")]),
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
        if kind == "TRUSTED_BY"
    ]

    # Assert
    assert sorted((names[r["source_id"]], names[r["target_id"]]) for r in trusts) == (
        expected
    )
    for row in trusts:
        assert row["trust_type"] == "External"
        assert row["same_forest"] is False


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
