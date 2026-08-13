import pytest

from cartography.intel.render.blueprints import transform


def test_transform_emits_one_row_per_resource_and_maps_type_to_id_column():
    blueprints = [
        {
            "id": "bp-1",
            "name": "cartography-test-blueprint",
            "ownerId": "tea-1",
            "status": "created",
            "autoSync": True,
            "repo": "https://github.com/example/repo",
            "branch": "main",
            "path": "render.yaml",
            "lastSync": "2026-01-02T00:00:00Z",
            "resources": [
                {"id": "srv-1", "name": "web", "type": "web_service"},
                {"id": "crn-1", "name": "nightly", "type": "cron_job"},
                {"id": "dpg-1", "name": "db", "type": "postgres"},
                {"id": "red-1", "name": "cache", "type": "key_value"},
                {"id": "evg-1", "name": "shared", "type": "environment_group"},
            ],
        },
    ]

    rows = transform(blueprints)

    assert all(row["id"] == "bp-1" for row in rows)
    by_service = [row for row in rows if row["service_id"]]
    assert {row["service_id"] for row in by_service} == {"srv-1", "crn-1"}
    assert {row["postgres_id"] for row in rows if row["postgres_id"]} == {"dpg-1"}
    assert {row["key_value_id"] for row in rows if row["key_value_id"]} == {"red-1"}
    assert {row["env_group_id"] for row in rows if row["env_group_id"]} == {"evg-1"}


def test_transform_emits_a_row_with_no_linked_ids_when_no_resources():
    blueprints = [{"id": "bp-1", "name": "empty", "resources": []}]

    rows = transform(blueprints)

    assert rows == [
        {
            "id": "bp-1",
            "name": "empty",
            "ownerId": None,
            "status": None,
            "autoSync": None,
            "repo": None,
            "branch": None,
            "path": None,
            "lastSync": None,
            "service_id": None,
            "postgres_id": None,
            "key_value_id": None,
            "env_group_id": None,
        }
    ]


def test_transform_leaves_unmapped_resource_type_with_no_linked_id():
    """
    A resource type this module doesn't model (e.g. `artifact_source`) still produces
    a row for the blueprint node itself, but none of the four id columns are set, so no
    relationship edge is created for it.
    """
    blueprints = [
        {
            "id": "bp-1",
            "name": "has-artifact-source",
            "resources": [{"id": "art-1", "name": "src", "type": "artifact_source"}],
        },
    ]

    rows = transform(blueprints)

    assert rows == [
        {
            "id": "bp-1",
            "name": "has-artifact-source",
            "ownerId": None,
            "status": None,
            "autoSync": None,
            "repo": None,
            "branch": None,
            "path": None,
            "lastSync": None,
            "service_id": None,
            "postgres_id": None,
            "key_value_id": None,
            "env_group_id": None,
        }
    ]


def test_transform_raises_on_resources_entry_missing_an_id():
    """
    A resources entry present but missing its id must fail loudly rather than silently
    produce a row with no linked id, which would drop the relationship edge with no
    error signal - matching the raise-on-malformed pattern used by envgroups.py.
    """
    blueprints = [
        {
            "id": "bp-1",
            "name": "malformed",
            "resources": [{"name": "no-id-here", "type": "web_service"}],
        },
    ]

    with pytest.raises(ValueError):
        transform(blueprints)


def test_transform_raises_on_blueprint_missing_an_id():
    blueprints = [{"name": "no-id-here"}]

    with pytest.raises(ValueError):
        transform(blueprints)


def test_transform_raises_on_resources_entry_missing_a_type():
    """
    A resources entry missing `type` entirely is malformed data - indistinguishable
    from an unmapped-but-present type (e.g. `artifact_source`) unless we check for it
    explicitly, which would silently drop the row's relationship with no error signal.
    A present-but-unrecognized type is legitimate (see
    test_transform_leaves_unmapped_resource_type_with_no_linked_id) and must not raise.
    """
    blueprints = [
        {
            "id": "bp-1",
            "name": "malformed",
            "resources": [{"id": "srv-1", "name": "no-type-here"}],
        },
    ]

    with pytest.raises(ValueError):
        transform(blueprints)
