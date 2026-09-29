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
from cartography.intel.zoom.users import cleanup as cleanup_users
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
            for i in (1, 2):
                load(
                    neo4j_session,
                    ZoomMeetingSchema(),
                    meetings.transform(
                        [{**MEETING, "id": 12345678900 + i, "host_id": f"user-{i}"}],
                        account,
                    ),
                    ACCOUNT_ID=account,
                    OWNER_ID=f"{account}:user:user-{i}",
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
    assert check_rels(neo4j_session, "ZoomUser", "id", label, "id", "RESOURCE") == {
        (f"{account}:user:user-{i}", f"{account}:{suffix}{i}")
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

    # Act: a complete users inventory removes the departed owner's snapshot.
    load(
        neo4j_session,
        ZoomUserSchema(),
        users("account-a")[:1],
        ACCOUNT_ID="account-a",
        lastupdated=3,
    )
    module.sync(
        neo4j_session,
        client_for(empty_first=True),
        "account-a",
        3,
        users("account-a")[:1],
    )
    cleanup_users(neo4j_session, "account-a", 3)

    # Assert
    assert check_nodes(neo4j_session, label, ["id", "lastupdated"]) == {
        (f"account-b:{suffix}{i}", 1) for i in (1, 2)
    }
    assert ("account-a:user:user-1",) in (
        check_nodes(neo4j_session, "ZoomUser", ["id"]) or set()
    )


@pytest.mark.parametrize(  # type: ignore[misc]
    "module,status,plan_type",
    [
        (recordings, "inactive", 2),
        (recordings, "active", 1),
        (meetings, "pending", 2),
        (meetings, "active", 4),
    ],
)
def test_ineligible_owner_retains_prior_snapshot(
    neo4j_session: neo4j.Session, module: ModuleType, status: str, plan_type: int
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
    module.sync(neo4j_session, client_for(), account, 1, users(account))
    changed = [{**user, "status": status, "type": plan_type} for user in users(account)]
    client = client_for(empty_first=True)

    # Act
    module.sync(neo4j_session, client, account, 2, changed)

    # Assert
    client.get_paginated.assert_not_called()
    label = "ZoomMeeting" if module is meetings else "ZoomRecording"
    suffix = "meeting:1234567890" if module is meetings else "recording:instance-"
    assert check_nodes(neo4j_session, label, ["id", "lastupdated"]) == {
        (f"{account}:{suffix}{i}", 1) for i in (1, 2)
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
    for host in ("user-1", "user-2"):
        load(
            neo4j_session,
            schema,
            module.transform([r for r in raw if r["host_id"] == host], account),
            ACCOUNT_ID=account,
            OWNER_ID=f"{account}:user:{host}",
            lastupdated=1,
        )

    # Act
    module.sync(
        neo4j_session,
        client_for(empty_first=True, denied_second=True),
        account,
        2,
        users(account),
    )

    # Assert: all 1001 stale nodes were removed, not merely the first batch.
    remaining = check_nodes(neo4j_session, label, ["id"])
    assert remaining is not None
    assert len(remaining) == 1001
    assert check_nodes(neo4j_session, label, ["host_id"]) == {("user-2",)}

    # Act: a complete empty user inventory removes every owned snapshot.
    module.sync(neo4j_session, client_for(), account, 3, [])
    cleanup_users(neo4j_session, account, 3)

    # Assert
    assert check_nodes(neo4j_session, label, ["id"]) == set()
    assert check_nodes(neo4j_session, "ZoomUser", ["id"]) == set()


@pytest.mark.parametrize("code", [3301, 3001])  # type: ignore[misc]
def test_processing_recording_preserves_owner_and_continues_only_for_known_error(
    neo4j_session: neo4j.Session, code: int
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
    client = client_for()

    def get(path: str, params: Any = None) -> dict[str, Any]:
        if path == "/meetings/instance-1/recordings/settings":
            response = requests.Response()
            response.status_code = 404
            response._content = json.dumps({"code": code}).encode()
            raise requests.HTTPError(response=response)
        return RECORDING_SETTINGS

    client.get.side_effect = get

    # Act: processing is recoverable, other missing-recording errors remain fatal.
    if code == 3301:
        recordings.sync(neo4j_session, client, account, 2, users(account))
    else:
        with pytest.raises(requests.HTTPError):
            recordings.sync(neo4j_session, client, account, 2, users(account))

    # Assert: the failed owner's posture and relationships remain unchanged.
    assert check_nodes(
        neo4j_session,
        "ZoomRecording",
        ["id", "lastupdated", "password_protected", "share_recording"],
    ) == {
        ("account-a:recording:instance-1", 1, True, "publicly"),
        ("account-a:recording:instance-2", 2 if code == 3301 else 1, True, "publicly"),
    }
    assert check_rels(
        neo4j_session, "ZoomAccount", "id", "ZoomRecording", "id", "RESOURCE"
    ) == {(account, f"account-a:recording:instance-{i}") for i in (1, 2)}
    assert check_rels(
        neo4j_session, "ZoomRecording", "id", "ZoomUser", "id", "HOSTED_BY"
    ) == {
        (f"account-a:recording:instance-{i}", f"account-a:user:user-{i}")
        for i in (1, 2)
    }


@pytest.mark.parametrize("old_host_removed", [False, True])  # type: ignore[misc]
@pytest.mark.parametrize(  # type: ignore[misc]
    "module,label", [(meetings, "ZoomMeeting"), (recordings, "ZoomRecording")]
)
def test_host_transfer_preserves_identity_and_replaces_host_relationship(
    neo4j_session: neo4j.Session,
    module: ModuleType,
    label: str,
    old_host_removed: bool,
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
    module.sync(neo4j_session, client_for(), account, 1, users(account))
    suffix = "meeting:12345678901" if module is meetings else "recording:instance-1"
    before = check_nodes(neo4j_session, label, ["id", "firstseen"])
    assert before is not None
    firstseen = dict(before)[f"{account}:{suffix}"]
    client = client_for()
    raw = {
        **(MEETING if module is meetings else RECORDING),
        "host_id": "user-2",
        "uuid": "instance-1",
    }
    client.get_paginated.side_effect = lambda path, key, params=None: (
        [raw] if path.startswith("/users/user-2/") else []
    )
    client.get.return_value = raw if module is meetings else RECORDING_SETTINGS
    client.get.side_effect = None

    # Offboarding can delete the old host after transferring its resources.
    current_users = users(account)[1:] if old_host_removed else users(account)
    load(
        neo4j_session,
        ZoomUserSchema(),
        current_users,
        ACCOUNT_ID=account,
        lastupdated=2,
    )

    # Act: the old host is read first, before the new host loads the same resource.
    module.sync(neo4j_session, client, account, 2, current_users)
    cleanup_users(neo4j_session, account, 2)

    # Assert
    assert check_nodes(neo4j_session, label, ["id", "firstseen", "lastupdated"]) == {
        (f"{account}:{suffix}", firstseen, 2)
    }
    assert check_rels(neo4j_session, label, "id", "ZoomUser", "id", "HOSTED_BY") == {
        (f"{account}:{suffix}", f"{account}:user:user-2")
    }
    assert check_rels(neo4j_session, "ZoomUser", "id", label, "id", "RESOURCE") == {
        (f"{account}:user:user-2", f"{account}:{suffix}")
    }
