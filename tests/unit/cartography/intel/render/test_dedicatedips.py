import pytest

from cartography.intel.render.dedicatedips import transform


def test_transform_emits_one_row_per_associated_environment():
    dedicated_ips = [
        {
            "id": "dip-1",
            "name": "shared",
            "environmentIds": ["evn-1", "evn-2"],
        },
    ]

    rows = transform(dedicated_ips)

    assert {row["environment_id"] for row in rows} == {"evn-1", "evn-2"}
    assert all(row["id"] == "dip-1" for row in rows)


def test_transform_emits_a_row_with_no_environment_id_when_applies_to_all():
    dedicated_ips = [{"id": "dip-1", "name": "shared", "environmentIds": []}]

    rows = transform(dedicated_ips)

    assert len(rows) == 1
    assert rows[0]["environment_id"] is None


def test_transform_raises_on_empty_environment_id_entry():
    dedicated_ips = [{"id": "dip-1", "name": "shared", "environmentIds": [""]}]

    with pytest.raises(ValueError):
        transform(dedicated_ips)


def test_transform_raises_on_missing_id():
    with pytest.raises(ValueError):
        transform([{"name": "shared", "environmentIds": []}])
