import json
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from io import BytesIO
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from azure.core.exceptions import ClientAuthenticationError
from urllib3.connectionpool import HTTPSConnectionPool
from urllib3.response import HTTPResponse

from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.microsoft import defender
from cartography.intel.microsoft.defender import alerts as defender_alerts
from cartography.intel.microsoft.defender import client as defender_client
from cartography.intel.microsoft.defender import machines as defender_machines
from tests.data.microsoft.defender import ALERTS
from tests.data.microsoft.defender import MACHINES
from tests.data.microsoft.defender import TENANT_ID


def _response(payload, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    return response


def test_machine_pagination_uses_skip_when_full_page_has_no_next_link():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [_response({"value": MACHINES}), _response({"value": []})]
    credential = MagicMock()
    credential.get_token.return_value.token = "test-token"

    # Act
    result = defender_client.get_collection(
        session,
        credential,
        defender_machines.MACHINES_URL,
        defender_machines.MDE_SCOPE,
        {"$top": 2},
        use_skip=True,
    )

    # Assert
    assert result == MACHINES
    assert session.get.call_args_list[1].kwargs["params"] == {"$top": 2, "$skip": 2}
    assert session.get.call_args.kwargs["allow_redirects"] is False
    assert credential.get_token.call_args.args == (defender_machines.MDE_SCOPE,)


def test_alert_pagination_keeps_provider_cursor_and_uses_graph_scope():
    # Arrange
    session = MagicMock()
    next_link = defender_alerts.ALERTS_URL + "?$skiptoken=next"
    in_progress = {**ALERTS[0], "id": "alert-2", "status": "inProgress"}
    session.get.side_effect = [
        _response({"value": ALERTS, "@odata.nextLink": next_link}),
        _response({"value": []}),
        # The first alert changed status between queries; it is returned once.
        _response({"value": [in_progress, {**ALERTS[0], "status": "inProgress"}]}),
    ]
    credential = MagicMock()

    # Act
    result = defender_alerts.get_alerts(session, credential)

    # Assert
    assert [alert["id"] for alert in result] == [ALERTS[0]["id"], "alert-2"]
    params = [call.kwargs["params"] for call in session.get.call_args_list]
    assert params == [
        {
            "$top": 100,
            "$filter": "serviceSource eq 'microsoftDefenderForEndpoint' and status eq 'new'",
        },
        None,
        {
            "$top": 100,
            "$filter": "serviceSource eq 'microsoftDefenderForEndpoint' and status eq 'inProgress'",
        },
    ]
    assert session.get.call_args_list[1].args == (next_link,)
    assert credential.get_token.call_args.args == (defender_alerts.GRAPH_SCOPE,)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"value": None},
        {"value": [{}]},
        {"value": [{"id": None}]},
        {"value": ["invalid"]},
    ],
)
def test_malformed_collection_is_not_treated_as_empty(payload):
    # Arrange
    session = MagicMock()
    session.get.return_value = _response(payload)

    # Act and assert
    with pytest.raises(ValueError):
        defender_alerts.get_alerts(session, MagicMock())


@pytest.mark.parametrize(
    "next_link",
    [
        "http://graph.microsoft.com/v1.0/security/alerts_v2?next=1",
        "https://example.test/v1.0/security/alerts_v2?next=1",
        "https://graph.microsoft.com/v1.0/users?next=1",
        "https://graph.microsoft.com:443/v1.0/security/alerts_v2?next=1",
        123,
        "",
    ],
)
def test_untrusted_next_link_fails_before_sending_token(next_link):
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"value": [], "@odata.nextLink": next_link})

    # Act and assert
    with pytest.raises(ValueError):
        defender_alerts.get_alerts(session, MagicMock())
    assert session.get.call_count == 1


def test_repeated_pagination_fails():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response(
        {
            "value": [],
            "@odata.nextLink": defender_alerts.ALERTS_URL + "?$skiptoken=next",
        }
    )

    # Act and assert
    with pytest.raises(ValueError, match="repeated nextLink"):
        defender_alerts.get_alerts(session, MagicMock())


def test_advancing_pagination_is_bounded() -> None:
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response(
            {
                "value": [{"id": str(i)}],
                "@odata.nextLink": defender_alerts.ALERTS_URL + f"?$skiptoken={i}",
            }
        )
        for i in range(2)
    ]

    # Act and assert
    with (
        patch.object(defender_client, "DEFAULT_MAX_PAGES", 2),
        pytest.raises(ValueError, match="pagination limit"),
    ):
        defender_alerts.get_alerts(session, MagicMock())
    assert session.get.call_count == 2


def test_retry_after_is_capped_through_real_http_adapter() -> None:
    # Arrange: replace network I/O only; the actual requests/urllib3 retry loop runs.
    responses = [
        HTTPResponse(
            status=status,
            body=BytesIO(b'{"value": []}'),
            headers={"Retry-After": "3600"},
            preload_content=False,
        )
        for status in (429, 503, 200)
    ]
    credential = MagicMock()
    credential.get_token.return_value.token = "synthetic-token"

    # Act
    with (
        defender_client.create_session() as session,
        patch.object(
            HTTPSConnectionPool, "_make_request", side_effect=responses
        ) as send,
        patch("urllib3.util.retry.time.sleep") as sleep,
    ):
        result = defender_machines.get_machines(session, credential)

    # Assert
    assert result == []
    assert send.call_count == 3
    assert sleep.call_args_list == [call(8), call(8)]


def test_optional_timestamps_are_native_and_bad_metadata_keeps_inventory() -> None:
    # Arrange
    machines = [{"id": "machine", "firstSeen": None, "lastSeen": "invalid"}]

    # Act
    machine = defender_machines.transform_machines(machines, TENANT_ID)[0]
    alert = defender_alerts.transform_alerts(ALERTS, TENANT_ID)[0]

    # Assert
    assert machine["id"] == f"{TENANT_ID}/machine"
    assert machine["firstSeen"] is None
    assert machine["lastSeen"] is None
    assert alert["createdDateTime"] == datetime(2026, 9, 17, 9, tzinfo=timezone.utc)
    assert alert["lastUpdateDateTime"] is None


@pytest.mark.parametrize(
    "value",
    ["2026-09-17t09:00:00z", "2026-09-17T09:00:00.0000000Z"],
)
def test_rfc3339_timestamps_parse(value):
    # Act
    machine = defender_machines.transform_machines(
        [{"id": "machine", "lastSeen": value}], TENANT_ID
    )[0]

    # Assert
    assert machine["lastSeen"] == datetime(2026, 9, 17, 9, tzinfo=timezone.utc)


def test_repeated_machine_records_fail_instead_of_looping_on_ignored_skip():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"value": MACHINES})

    # Act and assert
    with pytest.raises(ValueError, match="repeated a record"):
        defender_client.get_collection(
            session,
            MagicMock(),
            defender_machines.MACHINES_URL,
            defender_machines.MDE_SCOPE,
            {"$top": 2},
            use_skip=True,
        )


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
def test_http_errors_are_not_treated_as_empty_inventory(status):
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"value": []}, status)

    # Act and assert
    with pytest.raises(requests.HTTPError):
        defender_machines.get_machines(session, MagicMock())


def test_authentication_failure_does_not_issue_api_request():
    # Arrange
    session, credential = MagicMock(), MagicMock()
    credential.get_token.side_effect = ClientAuthenticationError("expired credential")

    # Act and assert
    with pytest.raises(ClientAuthenticationError):
        defender_machines.get_machines(session, credential)
    session.get.assert_not_called()


def test_transforms_scope_provider_ids_and_device_evidence():
    # Act
    machines = defender_machines.transform_machines(MACHINES, TENANT_ID)
    alerts = defender_alerts.transform_alerts(ALERTS, TENANT_ID)

    # Assert
    assert machines[0]["id"] == f"{TENANT_ID}/machine-1"
    assert alerts[0]["machine_ids"] == [
        f"{TENANT_ID}/{machine}"
        for machine in ("machine-1", "machine-2", "machine-outside-retention")
    ]
    assert (
        defender_machines.transform_machines(MACHINES, "other-tenant")[0]["id"]
        != machines[0]["id"]
    )


@pytest.mark.parametrize(
    "aad_device_id", [None, "", "00000000-0000-0000-0000-000000000000"]
)
def test_missing_entra_ids_do_not_join_unregistered_intune_devices(aad_device_id):
    # Act
    result = defender_machines.transform_machines(
        [{"id": "machine", "aadDeviceId": aad_device_id}], TENANT_ID
    )

    # Assert
    assert result[0]["aadDeviceId"] is None
    assert result[0]["aad_device_id_normalized"] is None


def test_cross_tenant_alert_fails():
    # Act and assert
    with pytest.raises(ValueError, match="different tenant"):
        defender_alerts.transform_alerts(ALERTS, "other-tenant")


def test_missing_application_credentials_fail_before_constructing_credentials():
    # Arrange
    config = Config(neo4j_uri="bolt://localhost:7687", microsoft_tenant_id=TENANT_ID)

    # Act and assert
    with (
        patch.object(defender.credentials, "make_credential") as make_credential,
        pytest.raises(ValueError, match="service principal credentials"),
    ):
        defender.start_defender_ingestion(MagicMock(), config)
    make_credential.assert_not_called()


def test_cli_accepts_defender_requested_sync(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_MICROSOFT_SECRET", "test-secret")
    cli = CLI(MagicMock(), "test")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        exit_code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "microsoft",
                "--microsoft-tenant-id",
                TENANT_ID,
                "--microsoft-client-id",
                "client-id",
                "--microsoft-client-secret-env-var",
                "TEST_MICROSOFT_SECRET",
                "--microsoft-requested-syncs",
                "defender_machines,defender_alerts",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.microsoft_requested_syncs == "defender_machines,defender_alerts"
    assert config.microsoft_client_secret == "test-secret"


@contextmanager
def _patched_sync(machines=MACHINES, alerts=ALERTS):
    """Patch API reads and graph writes; yield the names of datasets written."""
    calls: dict[str, list[str]] = {"loaded": [], "cleaned": []}

    def fake(result):
        return (
            {"side_effect": result}
            if isinstance(result, Exception)
            else {"return_value": result}
        )

    with (
        patch.object(defender_machines, "get_machines", **fake(machines)),
        patch.object(defender_alerts, "get_alerts", **fake(alerts)),
        patch.object(
            defender_machines,
            "load_machines",
            side_effect=lambda *_: calls["loaded"].append("machines"),
        ),
        patch.object(
            defender_alerts,
            "load_alerts",
            side_effect=lambda *_: calls["loaded"].append("alerts"),
        ),
        patch.object(
            defender_machines,
            "cleanup_machines",
            side_effect=lambda *_: calls["cleaned"].append("machines"),
        ),
        patch.object(
            defender_alerts,
            "cleanup_alerts",
            side_effect=lambda *_: calls["cleaned"].append("alerts"),
        ),
    ):
        yield calls


def _sync(requested=defender.DEFENDER_RESOURCES):
    defender.sync(MagicMock(), MagicMock(), MagicMock(), TENANT_ID, 1, requested)


@pytest.mark.parametrize("status", [401, 403])
def test_denied_machines_are_skipped_without_cleanup(status, caplog):
    # Act
    with (
        _patched_sync(
            machines=requests.HTTPError(response=_response({}, status))
        ) as calls,
        caplog.at_level("WARNING"),
    ):
        _sync()

    # Assert: alerts still sync and clean up; machines are neither loaded nor cleaned.
    assert calls == {"loaded": ["alerts"], "cleaned": ["alerts"]}
    assert "Machine.Read.All" in caplog.text


def test_tenant_without_defender_skips_quietly(caplog):
    # Arrange
    error = ClientAuthenticationError(
        "AADSTS500011: The resource principal named "
        "https://api.securitycenter.microsoft.com was not found in the tenant."
    )

    # Act
    with _patched_sync(machines=error) as calls, caplog.at_level("INFO"):
        _sync()

    # Assert
    assert calls["loaded"] == ["alerts"]
    assert "not provisioned" in caplog.text


def test_no_recent_machines_404_is_skipped():
    # Act
    with _patched_sync(
        machines=requests.HTTPError(response=_response({}, 404))
    ) as calls:
        _sync()

    # Assert
    assert calls["loaded"] == ["alerts"]


@pytest.mark.parametrize(
    "error",
    [
        requests.HTTPError(response=_response({}, 500)),
        ClientAuthenticationError("AADSTS7000215: Invalid client secret provided."),
        ValueError("Defender API returned an unsafe or repeated nextLink"),
    ],
)
def test_other_failures_abort_before_writes(error):
    # Act and assert
    with _patched_sync(machines=error) as calls, pytest.raises(type(error)):
        _sync()
    assert calls == {"loaded": [], "cleaned": []}


def test_alert_404_is_not_skipped():
    # Act and assert: 404 is only a documented empty response for machines.
    with (
        _patched_sync(alerts=requests.HTTPError(response=_response({}, 404))) as calls,
        pytest.raises(requests.HTTPError),
    ):
        _sync()
    assert calls == {"loaded": [], "cleaned": []}


@pytest.mark.parametrize(
    "requested,expected",
    [
        (["defender_machines"], ["machines"]),
        (["defender_alerts"], ["alerts"]),
    ],
)
def test_only_requested_datasets_are_read_and_written(requested, expected):
    # Act
    with _patched_sync() as calls:
        _sync(requested)
        machines_read = defender_machines.get_machines.called
        alerts_read = defender_alerts.get_alerts.called

    # Assert
    assert calls["loaded"] == expected
    assert calls["cleaned"] == expected
    assert machines_read is ("machines" in expected)
    assert alerts_read is ("alerts" in expected)


def test_no_requested_dataset_skips_credentials():
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id=TENANT_ID,
        microsoft_client_id="client-id",
        microsoft_client_secret="client-secret",
        microsoft_requested_syncs="users",
    )

    # Act
    with patch.object(defender.credentials, "make_credential") as make_credential:
        defender.start_defender_ingestion(MagicMock(), config)

    # Assert
    make_credential.assert_not_called()
