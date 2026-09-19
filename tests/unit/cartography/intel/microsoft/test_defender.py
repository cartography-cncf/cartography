import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from azure.core.exceptions import ClientAuthenticationError

from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.microsoft import defender
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
    result = defender.get_collection(
        session,
        credential,
        defender.MACHINES_URL,
        defender.MDE_SCOPE,
        {"$top": 2},
        use_skip=True,
    )

    # Assert
    assert result == MACHINES
    assert session.get.call_args_list[1].kwargs["params"] == {"$top": 2, "$skip": 2}
    assert session.get.call_args.kwargs["allow_redirects"] is False
    assert credential.get_token.call_args.args == (defender.MDE_SCOPE,)


def test_alert_pagination_keeps_provider_cursor_and_uses_graph_scope():
    # Arrange
    session = MagicMock()
    next_link = defender.ALERTS_URL + "?$skiptoken=next"
    session.get.side_effect = [
        _response({"value": ALERTS, "@odata.nextLink": next_link}),
        _response({"value": []}),
    ]
    credential = MagicMock()

    # Act
    result = defender.get_alerts(session, credential)

    # Assert
    assert result == ALERTS
    assert session.get.call_args_list[0].kwargs["params"] == {
        "$top": 100,
        "$filter": "serviceSource eq 'microsoftDefenderForEndpoint' and status ne 'resolved'",
    }
    assert session.get.call_args.args == (next_link,)
    assert session.get.call_args.kwargs["params"] is None
    assert credential.get_token.call_args.args == (defender.GRAPH_SCOPE,)


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
        defender.get_alerts(session, MagicMock())


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
        defender.get_alerts(session, MagicMock())
    assert session.get.call_count == 1


def test_repeated_pagination_fails():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response(
        {"value": [], "@odata.nextLink": defender.ALERTS_URL + "?$skiptoken=next"}
    )

    # Act and assert
    with pytest.raises(ValueError, match="repeated nextLink"):
        defender.get_alerts(session, MagicMock())


def test_repeated_machine_records_fail_instead_of_looping_on_ignored_skip():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"value": MACHINES})

    # Act and assert
    with pytest.raises(ValueError, match="repeated a record"):
        defender.get_collection(
            session,
            MagicMock(),
            defender.MACHINES_URL,
            defender.MDE_SCOPE,
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
        defender.get_machines(session, MagicMock())


def test_authentication_failure_does_not_issue_api_request():
    # Arrange
    session, credential = MagicMock(), MagicMock()
    credential.get_token.side_effect = ClientAuthenticationError("expired credential")

    # Act and assert
    with pytest.raises(ClientAuthenticationError):
        defender.get_machines(session, credential)
    session.get.assert_not_called()


def test_transforms_scope_provider_ids_and_device_evidence():
    # Act
    machines = defender.transform_machines(MACHINES, TENANT_ID)
    alerts = defender.transform_alerts(ALERTS, TENANT_ID)

    # Assert
    assert machines[0]["id"] == f"{TENANT_ID}/machine-1"
    assert alerts[0]["machine_ids"] == [
        f"{TENANT_ID}/{machine}"
        for machine in ("machine-1", "machine-2", "machine-outside-retention")
    ]
    assert (
        defender.transform_machines(MACHINES, "other-tenant")[0]["id"]
        != machines[0]["id"]
    )


@pytest.mark.parametrize(
    "aad_device_id", [None, "", "00000000-0000-0000-0000-000000000000"]
)
def test_missing_entra_ids_do_not_join_unregistered_intune_devices(aad_device_id):
    # Act
    result = defender.transform_machines(
        [{"id": "machine", "aadDeviceId": aad_device_id}], TENANT_ID
    )

    # Assert
    assert result[0]["aadDeviceId"] is None


def test_cross_tenant_alert_fails():
    # Act and assert
    with pytest.raises(ValueError, match="different tenant"):
        defender.transform_alerts(ALERTS, "other-tenant")


def test_unconfigured_defender_does_not_construct_credentials():
    # Arrange
    config = Config(neo4j_uri="bolt://localhost:7687")

    # Act
    with patch.object(defender.credentials, "make_credential") as make_credential:
        defender.start_defender_ingestion(MagicMock(), config)

    # Assert
    make_credential.assert_not_called()


def test_cli_enables_defender_with_existing_microsoft_credentials(monkeypatch):
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
                "--microsoft-defender",
            ]
        )

    # Assert
    assert exit_code == 0
    config = run.call_args.args[1]
    assert config.microsoft_defender is True
    assert config.microsoft_tenant_id == TENANT_ID
    assert config.microsoft_client_secret == "test-secret"
