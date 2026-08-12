import pytest

from cartography.intel.render.envgroups import transform


def test_transform_emits_one_row_per_linked_service():
    groups = [
        {
            "id": "evg-1",
            "name": "shared",
            "ownerId": "tea-1",
            "serviceLinks": [{"id": "srv-1"}, {"id": "srv-2"}],
        },
    ]

    rows = transform(groups)

    assert {row["service_id"] for row in rows} == {"srv-1", "srv-2"}
    assert all(row["id"] == "evg-1" for row in rows)


def test_transform_emits_a_row_with_no_service_id_when_unlinked():
    groups = [{"id": "evg-1", "name": "unlinked", "serviceLinks": []}]

    rows = transform(groups)

    assert rows == [
        {
            "id": "evg-1",
            "name": "unlinked",
            "ownerId": None,
            "environmentId": None,
            "createdAt": None,
            "updatedAt": None,
            "service_id": None,
        }
    ]


def test_transform_raises_on_service_link_missing_an_id():
    """
    A serviceLinks entry present but missing its id must fail loudly rather than
    silently produce a row with service_id=None, which would drop the LINKED_TO edge
    with no error signal - inconsistent with this module's raise-on-malformed pattern.
    """
    groups = [
        {
            "id": "evg-1",
            "name": "shared",
            "serviceLinks": [{"name": "no-id-here", "type": "web"}],
        },
    ]

    with pytest.raises(ValueError):
        transform(groups)
