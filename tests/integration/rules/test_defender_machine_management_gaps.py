import pytest

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.device_security_posture_gaps import (
    _defender_machine_management_gaps,
)


def _flagged_device_ids(
    neo4j_session,
    machine: dict,
    tenant_has_intune: bool = True,
) -> set[str]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (tenant:AzureTenant {id: 'tenant-1'})
        CREATE (tenant)-[:RESOURCE]->(device:DefenderMachine {
            id: 'tenant-1/machine-1',
            computer_dns_name: 'homer-mac.simpson.corp',
            os_platform: 'macOS',
            onboarding_status: $machine.onboarding_status,
            health_status: $machine.health_status
        })
        FOREACH (_ IN CASE WHEN $tenant_has_intune THEN [1] ELSE [] END |
            CREATE (tenant)-[:RESOURCE]->(:IntuneManagedDevice {id: 'intune-device-1'})
        )
        WITH device
        MATCH (intune:IntuneManagedDevice)
        WHERE $machine.enrolled_in_intune
        CREATE (device)-[:ASSOCIATED_WITH]->(intune)
        """,
        machine=machine,
        tenant_has_intune=tenant_has_intune,
    )
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _defender_machine_management_gaps.cypher_query,
    )
    return {row["device_id"] for row in rows}


@pytest.mark.parametrize(
    "machine, flagged",
    [
        (
            {
                "onboarding_status": "Onboarded",
                "health_status": "Active",
                "enrolled_in_intune": False,
            },
            {"tenant-1/machine-1"},
        ),
        (
            {
                "onboarding_status": "Onboarded",
                "health_status": "Active",
                "enrolled_in_intune": True,
            },
            set(),
        ),
        (
            {
                "onboarding_status": "CanBeOnboarded",
                "health_status": "Active",
                "enrolled_in_intune": False,
            },
            set(),
        ),
        (
            {
                "onboarding_status": "Onboarded",
                "health_status": "Inactive",
                "enrolled_in_intune": False,
            },
            set(),
        ),
    ],
    ids=["active-unenrolled", "enrolled", "not-onboarded", "inactive"],
)
def test_flags_only_active_onboarded_machines_without_intune_enrollment(
    neo4j_session,
    machine,
    flagged,
):
    assert _flagged_device_ids(neo4j_session, machine) == flagged


def test_does_not_flag_machines_in_a_tenant_without_intune_data(
    neo4j_session,
) -> None:
    machine = {
        "onboarding_status": "Onboarded",
        "health_status": "Active",
        "enrolled_in_intune": False,
    }

    assert _flagged_device_ids(neo4j_session, machine, tenant_has_intune=False) == set()
