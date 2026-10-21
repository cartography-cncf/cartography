from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.device_security_posture_gaps import (
    _defender_machine_management_gaps,
)


def _flagged_device_ids(neo4j_session) -> set[str]:
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _defender_machine_management_gaps.cypher_query,
    )
    return {row["device_id"] for row in rows}


def test_flags_only_active_onboarded_machines_without_intune_enrollment(
    neo4j_session,
) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (tenant:AzureTenant {id: 'tenant-1'})
        CREATE (tenant)-[:RESOURCE]->(intune:IntuneManagedDevice {id: 'intune-device-1'})
        CREATE (tenant)-[:RESOURCE]->(:DefenderMachine {
            id: 'tenant-1/unenrolled',
            onboarding_status: 'Onboarded',
            health_status: 'Active'
        })
        CREATE (tenant)-[:RESOURCE]->(enrolled:DefenderMachine {
            id: 'tenant-1/enrolled',
            onboarding_status: 'Onboarded',
            health_status: 'Active'
        })
        CREATE (enrolled)-[:ASSOCIATED_WITH]->(intune)
        CREATE (tenant)-[:RESOURCE]->(:DefenderMachine {
            id: 'tenant-1/not-onboarded',
            onboarding_status: 'CanBeOnboarded',
            health_status: 'Active'
        })
        CREATE (tenant)-[:RESOURCE]->(:DefenderMachine {
            id: 'tenant-1/inactive',
            onboarding_status: 'Onboarded',
            health_status: 'Inactive'
        })
        """,
    )

    assert _flagged_device_ids(neo4j_session) == {"tenant-1/unenrolled"}


def test_flags_only_machines_in_tenants_with_intune_data(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (with_intune:AzureTenant {id: 'tenant-1'})
        CREATE (with_intune)-[:RESOURCE]->(:IntuneManagedDevice {id: 'intune-device-1'})
        CREATE (with_intune)-[:RESOURCE]->(:DefenderMachine {
            id: 'tenant-1/unenrolled',
            onboarding_status: 'Onboarded',
            health_status: 'Active'
        })
        CREATE (without_intune:AzureTenant {id: 'tenant-2'})
        CREATE (without_intune)-[:RESOURCE]->(:DefenderMachine {
            id: 'tenant-2/unenrolled',
            onboarding_status: 'Onboarded',
            health_status: 'Active'
        })
        """,
    )

    assert _flagged_device_ids(neo4j_session) == {"tenant-1/unenrolled"}
