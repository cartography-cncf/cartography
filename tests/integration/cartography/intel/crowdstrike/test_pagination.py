from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.crowdstrike
import cartography.intel.crowdstrike.endpoints
import cartography.intel.crowdstrike.spotlight
from cartography.config import Config
from cartography.intel.crowdstrike.spotlight import SPOTLIGHT_FILTER
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


FIRST_VULN_PAGE = _response([VULNERABILITIES[VULN_IDS[0]]], after="cursor-1")


def _spotlight_client(
    requests: list[dict[str, Any]],
    first_page: dict[str, Any],
    *later_pages: dict[str, Any],
) -> MagicMock:
    pages = iter([first_page, *later_pages])

    def combined_query(parameters: dict[str, Any]) -> dict[str, Any]:
        requests.append(dict(parameters))
        return next(pages)

    client = MagicMock()
    client.combinedQueryVulnerabilities.side_effect = combined_query
    return client


def _ingest(
    neo4j_session,
    update_tag: int,
    *later_vuln_pages: dict[str, Any],
    first_vuln_page: dict[str, Any] = FIRST_VULN_PAGE,
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
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
            return_value=_spotlight_client(
                requests,
                first_vuln_page,
                *later_vuln_pages,
            ),
        ),
        patch("cartography.intel.crowdstrike.util.time.sleep"),
    ):
        cartography.intel.crowdstrike.start_crowdstrike_ingestion(
            neo4j_session,
            config,
        )
    return requests


def test_sync_loads_every_page(neo4j_session):
    # Act
    _ingest(neo4j_session, 1, _response([VULNERABILITIES[VULN_IDS[1]]]))

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


def test_transient_failure_is_retried(neo4j_session):
    # Act
    requests = _ingest(
        neo4j_session,
        1,
        _response([], status_code=503),
        _response([VULNERABILITIES[VULN_IDS[1]]]),
    )

    # Assert
    assert [r.get("after") for r in requests] == [None, "cursor-1", "cursor-1"]
    assert check_nodes(neo4j_session, "CrowdstrikeSpotlightVulnerability", ["id"]) == {
        (vuln_id,) for vuln_id in VULN_IDS
    }


def test_expired_cursor_restarts_from_last_updated_timestamp(neo4j_session):
    # Arrange
    _ingest(neo4j_session, 30, _response([VULNERABILITIES[VULN_IDS[1]]]))

    # Act: the restarted search replays the first record and reuses the old
    # search's cursor string, and the second record is gone from Spotlight.
    requests = _ingest(
        neo4j_session,
        31,
        _response([], status_code=404),
        _response([VULNERABILITIES[VULN_IDS[0]]], after="cursor-1"),
        _response([VULNERABILITIES[VULN_IDS[0]]]),
    )

    # Assert
    restart_filter = (
        f"{SPOTLIGHT_FILTER}+updated_timestamp:>="
        f"'{VULNERABILITIES[VULN_IDS[0]]['updated_timestamp']}'"
    )
    assert [(r.get("after"), r["filter"]) for r in requests] == [
        (None, SPOTLIGHT_FILTER),
        ("cursor-1", SPOTLIGHT_FILTER),
        (None, restart_filter),
        ("cursor-1", restart_filter),
    ]
    assert check_nodes(
        neo4j_session,
        "CrowdstrikeSpotlightVulnerability",
        ["id", "lastupdated"],
    ) == {(VULN_IDS[0], 31)}


@pytest.mark.parametrize(
    "failed_pages",
    [
        [_response([], status_code=400)],
        [_response([], status_code=429)] * 4,
        [{"status_code": 200}],
        [_response([VULNERABILITIES[VULN_IDS[0]]], after="cursor-1")],
        [
            _response([], status_code=404),
            _response([VULNERABILITIES[VULN_IDS[0]]], after="cursor-2"),
            _response([], status_code=404),
        ],
        [
            _response(
                [{**VULNERABILITIES[VULN_IDS[0]], "updated_timestamp": None}],
                after="cursor-2",
            ),
            _response([], status_code=404),
        ],
    ],
    ids=[
        "http-error",
        "retries-exhausted",
        "missing-body",
        "repeated-cursor",
        "cursor-expires-without-progress",
        "cursor-expires-without-timestamp",
    ],
)
def test_failed_page_aborts_before_cleanup(neo4j_session, failed_pages):
    # Arrange
    _ingest(neo4j_session, 10, _response([VULNERABILITIES[VULN_IDS[1]]]))

    # Act and assert
    with pytest.raises(CrowdstrikeAPIError, match="combinedQueryVulnerabilities"):
        _ingest(neo4j_session, 11, *failed_pages)

    # Assert
    assert check_nodes(
        neo4j_session,
        "CrowdstrikeSpotlightVulnerability",
        ["id", "lastupdated"],
    ) == {(VULN_IDS[0], 11), (VULN_IDS[1], 10)}


def test_missing_spotlight_scope_syncs_hosts_and_keeps_vulnerabilities(neo4j_session):
    # Arrange
    _ingest(neo4j_session, 20, _response([VULNERABILITIES[VULN_IDS[1]]]))

    # Act
    _ingest(neo4j_session, 21, first_vuln_page=_response([], status_code=403))

    # Assert
    assert check_nodes(neo4j_session, "CrowdstrikeHost", ["id", "lastupdated"]) == {
        (host_id, 21) for host_id in HOST_IDS
    }
    assert check_nodes(
        neo4j_session,
        "CrowdstrikeSpotlightVulnerability",
        ["id", "lastupdated"],
    ) == {(vuln_id, 20) for vuln_id in VULN_IDS}
    assert check_rels(
        neo4j_session,
        "CrowdstrikeHost",
        "id",
        "CrowdstrikeSpotlightVulnerability",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == set(zip(HOST_IDS, VULN_IDS))
    metadata = neo4j_session.run(
        "MATCH (m:ModuleSyncMetadata {id: 'crowdstrike_public_crowdstrike'}) "
        "RETURN m.lastupdated AS lastupdated",
    ).single()
    assert metadata["lastupdated"] == 21
