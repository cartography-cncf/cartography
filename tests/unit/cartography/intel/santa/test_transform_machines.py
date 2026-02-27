from cartography.intel.santa.machines import transform_machine_snapshots
from tests.data.santa.machines import MACHINE_SNAPSHOTS


def test_transform_machine_snapshots_extracts_machines_and_users() -> None:
    machines, users = transform_machine_snapshots(MACHINE_SNAPSHOTS, "Santa")

    assert {machine["id"] for machine in machines} == {"C02ABC123", "C02DEF456"}
    assert {machine["hostname"] for machine in machines} == {"donut-mac", "lisa-mac"}

    donut_machine = next(
        machine for machine in machines if machine["id"] == "C02ABC123"
    )
    assert donut_machine["primary_user_id"] == "homer@simpson.corp"
    assert donut_machine["source_name"] == "Santa"

    assert {user["id"] for user in users} == {
        "homer@simpson.corp",
        "lisa@simpson.corp",
    }
    assert {user["email"] for user in users} == {
        "homer@simpson.corp",
        "lisa@simpson.corp",
    }


def test_transform_machine_snapshots_handles_missing_user_and_identifier() -> None:
    snapshots = [
        {
            "platform": "macOS",
            "source": {"name": "Santa"},
            "system_info": {"hostname": "no-id-mac"},
        },
        {
            "serial_number": "C02XYZ999",
            "platform": "macOS",
            "source": {"name": "Santa"},
            "system_info": {"hostname": "anonymous-mac"},
        },
    ]

    machines, users = transform_machine_snapshots(snapshots, "Santa")

    assert machines == [
        {
            "id": "C02XYZ999",
            "hostname": "anonymous-mac",
            "serial_number": "C02XYZ999",
            "platform": "macOS",
            "model": None,
            "os_version": None,
            "source_name": "Santa",
            "last_seen": None,
        }
    ]
    assert users == []
