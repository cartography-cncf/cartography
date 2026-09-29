import json
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import neo4j
import pytest
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom import meetings
from cartography.intel.zoom import recordings
from cartography.intel.zoom.client import ZoomClient
from cartography.models.zoom.account import ZoomAccountSchema
from cartography.models.zoom.meeting import ZoomMeetingSchema
from cartography.models.zoom.recording import ZoomRecordingSchema
from cartography.models.zoom.user import ZoomUserSchema
from tests.data.zoom.exposure import MEETING
from tests.data.zoom.exposure import RECORDING
from tests.data.zoom.exposure import RECORDING_SETTINGS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)  # type: ignore[misc]
def clean_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n")


def users(account: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{account}:user:user-{i}",
            "zoom_id": f"user-{i}",
            "email": f"user-{i}@example.com",
            "status": "active",
            "type": 2,
        }
        for i in (1, 2)
    ]


def client_for(*, empty_first: bool = False, denied_second: bool = False) -> MagicMock:
    client = MagicMock(spec=ZoomClient)
    client.session = MagicMock()
    client.fork.return_value = client

    def get_paginated(path: str, key: str, params: Any = None) -> list[dict[str, Any]]:
        owner = path.split("/")[2]
        if empty_first and owner == "user-1":
            return []
        number = int(owner[-1])
        fixture = RECORDING if path.endswith("recordings") else MEETING
        return [
            {
                **fixture,
                "host_id": owner,
                "id": 12345678900 + number,
                "uuid": f"instance-{number}",
            }
        ]

    def get(path: str, params: Any = None) -> dict[str, Any]:
        identifier = path.split("/")[2]
        number = int(identifier[-1])
        if denied_second and number == 2:
            response = requests.Response()
            response.status_code = 403
            response._content = json.dumps(
                {"code": 200, "message": "Forbidden"}
            ).encode()
            raise requests.HTTPError(response=response)
        if path.endswith("settings"):
            return RECORDING_SETTINGS
        return {**MEETING, "host_id": f"user-{number}", "id": 12345678900 + number}

    client.get_paginated.side_effect = get_paginated
    client.get.side_effect = get
    return client


@pytest.mark.parametrize(  # type: ignore[misc]
    "module,label", [(meetings, "ZoomMeeting"), (recordings, "ZoomRecording")]
)
def test_owner_cleanup_preserves_denied_enrichment_and_other_accounts(
    neo4j_session: neo4j.Session,
    module: ModuleType,
    label: str,
) -> None:
    # Arrange
    for account in ("account-a", "account-b"):
        load(neo4j_session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
        load(
            neo4j_session,
            ZoomUserSchema(),
            users(account),
            ACCOUNT_ID=account,
            lastupdated=1,
        )
        if module is recordings:
            load(
                neo4j_session,
                ZoomMeetingSchema(),
                meetings.transform(
                    [
                        {**MEETING, "id": 12345678900 + i, "host_id": f"user-{i}"}
                        for i in (1, 2)
                    ],
                    account,
                ),
                ACCOUNT_ID=account,
                lastupdated=1,
            )

    # Act
    for account in ("account-a", "account-b"):
        module.sync(neo4j_session, client_for(), account, 1, users(account))

    # Assert
    suffix = "meeting:1234567890" if module is meetings else "recording:instance-"
    expected = {
        (f"{account}:{suffix}{i}", 1)
        for account in ("account-a", "account-b")
        for i in (1, 2)
    }
    assert check_nodes(neo4j_session, label, ["id", "lastupdated"]) == expected
    assert check_rels(neo4j_session, "ZoomAccount", "id", label, "id", "RESOURCE") == {
        (account, f"{account}:{suffix}{i}")
        for account in ("account-a", "account-b")
        for i in (1, 2)
    }
    assert check_rels(neo4j_session, label, "id", "ZoomUser", "id", "HOSTED_BY") == {
        (f"{account}:{suffix}{i}", f"{account}:user:user-{i}")
        for account in ("account-a", "account-b")
        for i in (1, 2)
    }
    if module is recordings:
        assert check_rels(
            neo4j_session, label, "id", "ZoomMeeting", "id", "RECORDED_FROM"
        ) == {
            (f"{account}:{suffix}{i}", f"{account}:meeting:1234567890{i}")
            for account in ("account-a", "account-b")
            for i in (1, 2)
        }

    # Act: one owner's authoritative empty list and another owner's denied details.
    module.sync(
        neo4j_session,
        client_for(empty_first=True, denied_second=True),
        "account-a",
        2,
        users("account-a"),
    )

    # Assert: deny preserves posture and tag, not just node existence.
    assert check_nodes(neo4j_session, label, ["id", "lastupdated"]) == expected - {
        (f"account-a:{suffix}1", 1)
    }
    assert check_nodes(neo4j_session, label, ["password_protected"]) == {(True,)}

    # Act: removed owner can be pruned from complete users inventory independently.
    module.sync(
        neo4j_session,
        client_for(empty_first=True),
        "account-a",
        3,
        users("account-a")[:1],
    )

    # Assert
    assert check_nodes(neo4j_session, label, ["id", "lastupdated"]) == {
        (f"account-b:{suffix}{i}", 1) for i in (1, 2)
    }


def test_ineligible_recording_owner_retains_prior_snapshot(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    account = "account-a"
    load(neo4j_session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
    load(
        neo4j_session,
        ZoomUserSchema(),
        users(account),
        ACCOUNT_ID=account,
        lastupdated=1,
    )
    recordings.sync(neo4j_session, client_for(), account, 1, users(account))
    changed = [{**user, "status": "inactive"} for user in users(account)]
    client = client_for(empty_first=True)

    # Act
    recordings.sync(neo4j_session, client, account, 2, changed)

    # Assert
    client.get_paginated.assert_not_called()
    assert check_nodes(neo4j_session, "ZoomRecording", ["id", "lastupdated"]) == {
        ("account-a:recording:instance-1", 1),
        ("account-a:recording:instance-2", 1),
    }


@pytest.mark.parametrize(  # type: ignore[misc]
    "module,label", [(meetings, "ZoomMeeting"), (recordings, "ZoomRecording")]
)
def test_cleanup_exhausts_multiple_batches(
    neo4j_session: neo4j.Session, module: ModuleType, label: str
) -> None:
    # Arrange: both stale-owner and removed-owner inventories exceed one batch.
    account = "account-a"
    load(neo4j_session, ZoomAccountSchema(), [{"id": account}], lastupdated=1)
    load(
        neo4j_session,
        ZoomUserSchema(),
        users(account),
        ACCOUNT_ID=account,
        lastupdated=1,
    )
    raw = [
        {
            **(MEETING if module is meetings else RECORDING),
            "id": number,
            "uuid": f"instance-{number}",
            "host_id": "user-1" if number <= 1001 else "user-2",
            "settings": (
                MEETING["settings"] if module is meetings else RECORDING_SETTINGS
            ),
        }
        for number in range(1, 2003)
    ]
    schema = ZoomMeetingSchema() if module is meetings else ZoomRecordingSchema()
    load(
        neo4j_session,
        schema,
        module.transform(raw, account),
        ACCOUNT_ID=account,
        lastupdated=1,
    )

    # Act
    module.cleanup(neo4j_session, account, "user-1", 2)

    # Assert: all 1001 stale nodes were removed, not merely the first batch.
    remaining = check_nodes(neo4j_session, label, ["id"])
    assert remaining is not None
    assert len(remaining) == 1001
    assert check_nodes(neo4j_session, label, ["host_id"]) == {("user-2",)}

    # Act: a complete empty user inventory removes every orphan in batches.
    module.sync(neo4j_session, client_for(), account, 3, [])

    # Assert
    assert check_nodes(neo4j_session, label, ["id"]) == set()
