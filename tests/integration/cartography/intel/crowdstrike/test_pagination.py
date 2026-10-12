from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.crowdstrike
import cartography.intel.crowdstrike.endpoints
import cartography.intel.crowdstrike.spotlight
from cartography.config import Config
from cartography.intel.crowdstrike.util import CrowdstrikeAPIError
from tests.data.crowdstrike.endpoints import GET_HOSTS
from tests.data.crowdstrike.spotlight import GET_SPOTLIGHT_VULNERABILITIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

HOST_IDS = ["host-1", "host-2"]
VULN_IDS = ["host-1_vuln-1", "host-2_vuln-2"]
HOSTS = {host_id: {**GET_HOSTS[0], "device_id": host_id} for host_id in HOST_IDS}
VULNERABILITIES = {
    vuln_id: {**GET_SPOTLIGHT_VULNERABILITIES[0], "id": vuln_id, "aid": host_id}
    for vuln_id, host_id in zip(VULN_IDS, HOST_IDS)
}


def _response(
    resources: list[Any],
    status_code: int = 200,
    **pagination: Any,
) -> dict[str, Any]:
    errors = [] if status_code == 200 else [{"code": status_code, "message": "err"}]
    return {
        "status_code": status_code,
        "body": {
            "meta": {"pagination": pagination},
            "resources": resources,
            "errors": errors,
        },
    }


def _hosts_client() -> MagicMock:
    client = MagicMock()
    client.QueryDevicesByFilterScroll.side_effect = [
        _response([HOST_IDS[0]], offset="scroll-1", total=2),
        _response([HOST_IDS[1]], offset="scroll-2", total=2),
    ]
    client.GetDeviceDetails.side_effect = lambda ids: _response(
        [HOSTS[i] for i in ids.split(",")],
    )
    return client


def _spotlight_client(second_page: dict[str, Any]) -> MagicMock:
    client = MagicMock()
    client.queryVulnerabilities.side_effect = [
        _response([VULN_IDS[0]], after="cursor-1"),
        second_page,
    ]
    client.getVulnerabilities.side_effect = lambda ids: _response(
        [VULNERABILITIES[i] for i in ids.split(",")],
    )
    return client


def _ingest(neo4j_session, update_tag: int, second_vuln_page: dict[str, Any]) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        crowdstrike_client_id="client-id",
        crowdstrike_client_secret="client-secret",
    )
    with (
        patch.object(cartography.intel.crowdstrike, "get_authorization"),
        patch.object(
            cartography.intel.crowdstrike.endpoints,
            "Hosts",
            return_value=_hosts_client(),
        ),
        patch.object(
            cartography.intel.crowdstrike.spotlight,
            "Spotlight_Vulnerabilities",
            return_value=_spotlight_client(second_vuln_page),
        ),
    ):
        cartography.intel.crowdstrike.start_crowdstrike_ingestion(
            neo4j_session,
            config,
        )


def test_sync_loads_every_page(neo4j_session):
    # Act
    _ingest(neo4j_session, 1, _response([VULN_IDS[1]]))

    # Assert
    assert check_nodes(neo4j_session, "CrowdstrikeHost", ["id"]) == {
        (host_id,) for host_id in HOST_IDS
    }
    assert check_rels(
        neo4j_session,
        "CrowdstrikeHost",
        "id",
        "CrowdstrikeSpotlightVulnerability",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == set(zip(HOST_IDS, VULN_IDS))


@pytest.mark.parametrize(
    "failed_page",
    [
        _response([], status_code=429),
        {"status_code": 200},
        _response([VULN_IDS[0]], after="cursor-1"),
    ],
    ids=["http-error", "missing-body", "repeated-cursor"],
)
def test_failed_page_aborts_before_cleanup(neo4j_session, failed_page):
    # Arrange
    _ingest(neo4j_session, 10, _response([VULN_IDS[1]]))

    # Act and assert
    with pytest.raises(CrowdstrikeAPIError, match="queryVulnerabilities"):
        _ingest(neo4j_session, 11, failed_page)

    # Assert
    assert check_nodes(
        neo4j_session,
        "CrowdstrikeSpotlightVulnerability",
        ["id", "lastupdated"],
    ) == {(VULN_IDS[0], 11), (VULN_IDS[1], 10)}
