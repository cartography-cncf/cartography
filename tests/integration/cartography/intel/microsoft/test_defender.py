import asyncio
import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.client.core.tx import load
from cartography.intel.microsoft import defender
from cartography.intel.microsoft.intune.managed_devices import sync_managed_devices
from cartography.models.microsoft.entra.tenant import EntraTenantSchema
from tests.data.microsoft.defender import AAD_DEVICE_ID
from tests.data.microsoft.defender import ALERTS
from tests.data.microsoft.defender import MACHINES
from tests.data.microsoft.defender import TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

OTHER_TENANT = "00000000-1111-2222-3333-555555555555"


def _response(payload, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    return response


def _api_session(machines, alerts):
    session = MagicMock()
    session.get.side_effect = [
        _response({"value": machines}),
        _response({"value": alerts}),
    ]
    return session


@pytest.fixture(autouse=True)
def reset_defender_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    load(
        neo4j_session,
        EntraTenantSchema(),
        [{"id": TENANT_ID}, {"id": OTHER_TENANT}],
        lastupdated=1,
    )


async def _sync_intune(neo4j_session, tenant_id, device_id):
    async def devices(_client):
        yield ManagedDevice(
            id=device_id,
            device_name="laptop.example.test",
            azure_a_d_device_id=AAD_DEVICE_ID,
        )

    with patch(
        "cartography.intel.microsoft.intune.managed_devices.get_managed_devices",
        side_effect=devices,
    ):
        await sync_managed_devices(
            neo4j_session, None, tenant_id, 1, {"TENANT_ID": tenant_id, "UPDATE_TAG": 1}
        )


def test_sync_links_real_intune_transform_and_cleans_only_current_tenant(neo4j_session):
    # Arrange
    asyncio.run(_sync_intune(neo4j_session, TENANT_ID, "intune-1"))
    asyncio.run(_sync_intune(neo4j_session, OTHER_TENANT, "intune-other"))
    other_alerts = [{**alert, "tenantId": OTHER_TENANT} for alert in ALERTS]
    defender.sync(
        neo4j_session,
        _api_session(MACHINES, other_alerts),
        MagicMock(),
        OTHER_TENANT,
        1,
    )

    # Act
    defender.sync(
        neo4j_session, _api_session(MACHINES, ALERTS), MagicMock(), TENANT_ID, 1
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        ["id", "_ont_severity", "_ont_status", "_ont_source"],
    ) == {
        (f"{tenant}/alert-1", "medium", "open", "microsoft")
        for tenant in (TENANT_ID, OTHER_TENANT)
    }
    assert check_nodes(neo4j_session, "DefenderMachine", ["id", "health_status"]) == {
        (f"{tenant}/{machine['id']}", machine["healthStatus"])
        for tenant in (TENANT_ID, OTHER_TENANT)
        for machine in MACHINES
    }
    assert check_rels(
        neo4j_session, "AzureTenant", "id", "DefenderMachine", "id", "RESOURCE"
    ) == {
        (tenant, f"{tenant}/{machine['id']}")
        for tenant in (TENANT_ID, OTHER_TENANT)
        for machine in MACHINES
    }
    assert check_rels(
        neo4j_session, "AzureTenant", "id", "DefenderAlert", "id", "RESOURCE"
    ) == {(tenant, f"{tenant}/alert-1") for tenant in (TENANT_ID, OTHER_TENANT)}
    assert check_rels(
        neo4j_session,
        "DefenderMachine",
        "id",
        "IntuneManagedDevice",
        "id",
        "ASSOCIATED_WITH",
    ) == {
        (f"{TENANT_ID}/machine-1", "intune-1"),
        (f"{OTHER_TENANT}/machine-1", "intune-other"),
    }
    assert check_rels(
        neo4j_session, "DefenderAlert", "id", "DefenderMachine", "id", "AFFECTS"
    ) == {
        (f"{tenant}/alert-1", f"{tenant}/{machine}")
        for tenant in (TENANT_ID, OTHER_TENANT)
        for machine in ("machine-1", "machine-2")
    }

    # Act: one machine ages out and the alert resolves; the remaining machine loses its Entra ID.
    defender.sync(
        neo4j_session,
        _api_session([{"id": "machine-1"}], []),
        MagicMock(),
        TENANT_ID,
        2,
    )

    # Assert
    assert check_nodes(neo4j_session, "DefenderMachine", ["id"]) == {
        (f"{TENANT_ID}/machine-1",),
        (f"{OTHER_TENANT}/machine-1",),
        (f"{OTHER_TENANT}/machine-2",),
    }
    assert check_nodes(neo4j_session, "DefenderAlert", ["id"]) == {
        (f"{OTHER_TENANT}/alert-1",)
    }
    assert check_rels(
        neo4j_session,
        "DefenderMachine",
        "id",
        "IntuneManagedDevice",
        "id",
        "ASSOCIATED_WITH",
    ) == {
        (f"{OTHER_TENANT}/machine-1", "intune-other"),
    }


def test_later_alert_page_failure_preserves_previous_nodes_and_edges(neo4j_session):
    # Arrange
    defender.sync(
        neo4j_session, _api_session(MACHINES, ALERTS), MagicMock(), TENANT_ID, 1
    )
    session = MagicMock()
    session.get.side_effect = [
        _response({"value": []}),
        _response(
            {
                "value": ALERTS,
                "@odata.nextLink": defender.ALERTS_URL + "?$skiptoken=page2",
            }
        ),
        _response({"error": {"code": "Forbidden"}}, 403),
    ]

    # Act
    with pytest.raises(requests.HTTPError):
        defender.sync(neo4j_session, session, MagicMock(), TENANT_ID, 2)

    # Assert
    assert check_nodes(neo4j_session, "DefenderMachine", ["id", "lastupdated"]) == {
        (f"{TENANT_ID}/machine-1", 1),
        (f"{TENANT_ID}/machine-2", 1),
    }
    assert check_nodes(neo4j_session, "DefenderAlert", ["id", "lastupdated"]) == {
        (f"{TENANT_ID}/alert-1", 1)
    }
    assert check_rels(
        neo4j_session, "DefenderAlert", "id", "DefenderMachine", "id", "AFFECTS"
    ) == {
        (f"{TENANT_ID}/alert-1", f"{TENANT_ID}/machine-1"),
        (f"{TENANT_ID}/alert-1", f"{TENANT_ID}/machine-2"),
    }


@pytest.mark.parametrize(
    "severity,status,normalized_severity,normalized_status",
    [
        ("informational", "inProgress", "info", "open"),
        ("unknown", "unknownFutureValue", None, None),
    ],
)
def test_security_issue_mapping_preserves_unknown_values(
    neo4j_session,
    severity,
    status,
    normalized_severity,
    normalized_status,
):
    # Arrange
    alerts = [{**ALERTS[0], "severity": severity, "status": status}]

    # Act
    defender.sync(
        neo4j_session, _api_session(MACHINES, alerts), MagicMock(), TENANT_ID, 1
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        [
            "severity",
            "status",
            "_ont_severity",
            "_ont_status",
            "_ont_type",
            "_ont_first_seen",
        ],
    ) == {
        (
            severity,
            status,
            normalized_severity,
            normalized_status,
            "antivirus",
            "2026-09-17T09:00:00Z",
        )
    }
