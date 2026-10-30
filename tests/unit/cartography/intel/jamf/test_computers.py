import pytest

from cartography.intel.jamf.computers import transform
from cartography.intel.jamf.computers import transform_applications


def test_transform_requires_computer_id() -> None:
    with pytest.raises(KeyError, match="id"):
        transform([{"general": {"name": "Springfield-MacBook"}}])


def test_transform_applications_shares_one_node_per_bundle_and_version() -> None:
    chrome = {"name": "Google Chrome.app", "bundleId": "com.google.Chrome"}
    apps = transform_applications(
        [
            {"id": 1, "applications": [{**chrome, "version": "131.0"}]},
            {
                "id": 2,
                "applications": [
                    {**chrome, "version": "131.0"},
                    {**chrome, "version": "130.0"},
                ],
            },
        ]
    )

    assert {(app["id"], tuple(app["computer_ids"])) for app in apps} == {
        ("com.google.Chrome@131.0", (1, 2)),
        ("com.google.Chrome@130.0", (2,)),
    }


def test_transform_applications_falls_back_to_name_without_bundle_id() -> None:
    apps = transform_applications(
        [
            {
                "id": 1,
                "applications": [
                    {"name": "Unsigned Tool.app", "bundleId": None, "version": None},
                    {"name": None, "bundleId": None, "version": "1.0"},
                ],
            },
            {"id": 2, "applications": None},
        ]
    )

    assert [(app["id"], app["computer_ids"]) for app in apps] == [
        ("Unsigned Tool.app@", [1]),
    ]
