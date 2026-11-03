from cartography.intel.scaleway.iot.hubs import transform
from tests.data.scaleway.iot import SCALEWAY_IOT_DEVICES
from tests.data.scaleway.iot import SCALEWAY_IOT_HUBS
from tests.data.scaleway.iot import TEST_DEVICE_ID
from tests.data.scaleway.iot import TEST_HUB_ID
from tests.data.scaleway.iot import TEST_PROJECT_ID


def test_transform_scopes_hubs_and_devices_by_project():
    hubs_by_project, devices_by_project = transform(
        SCALEWAY_IOT_HUBS,
        {TEST_HUB_ID: SCALEWAY_IOT_DEVICES},
        projects_id=[TEST_PROJECT_ID],
    )

    assert list(hubs_by_project.keys()) == [TEST_PROJECT_ID]
    assert [hub["id"] for hub in hubs_by_project[TEST_PROJECT_ID]] == [TEST_HUB_ID]
    assert list(devices_by_project.keys()) == [TEST_PROJECT_ID]
    assert [device["id"] for device in devices_by_project[TEST_PROJECT_ID]] == [
        TEST_DEVICE_ID,
    ]


def test_transform_skips_hubs_outside_the_synced_projects():
    # A hub whose project isn't part of the synced organization's projects (e.g.
    # a project deleted between the project sync and this call) must be dropped,
    # not loaded under an unknown PROJECT_ID.
    hubs_by_project, devices_by_project = transform(
        SCALEWAY_IOT_HUBS,
        {TEST_HUB_ID: SCALEWAY_IOT_DEVICES},
        projects_id=["some-other-project-id"],
    )

    assert hubs_by_project == {}
    assert devices_by_project == {}


def test_transform_handles_a_hub_with_no_devices():
    hubs_by_project, devices_by_project = transform(
        SCALEWAY_IOT_HUBS,
        {TEST_HUB_ID: []},
        projects_id=[TEST_PROJECT_ID],
    )

    assert [hub["id"] for hub in hubs_by_project[TEST_PROJECT_ID]] == [TEST_HUB_ID]
    assert devices_by_project == {}
