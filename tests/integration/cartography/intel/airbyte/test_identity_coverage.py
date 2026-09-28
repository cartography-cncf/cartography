import logging
from unittest.mock import patch

import pytest
import requests

import cartography.intel.airbyte
from cartography.config import Config
from tests.data.airbyte import multi_org
from tests.data.airbyte.fake_api import FakeAirbyteAPI
from tests.data.airbyte.fake_api import make_client
from tests.data.airbyte.multi_org import ALPHA_USER
from tests.data.airbyte.multi_org import APP_OWNER
from tests.data.airbyte.multi_org import BETA_USER
from tests.data.airbyte.multi_org import GAMMA_USER
from tests.data.airbyte.multi_org import NEW_ALPHA_USER
from tests.data.airbyte.multi_org import ORG_ALPHA
from tests.data.airbyte.multi_org import ORG_BETA
from tests.data.airbyte.multi_org import ORG_GAMMA
from tests.data.airbyte.multi_org import permission
from tests.data.airbyte.multi_org import SHARED_USER
from tests.data.airbyte.multi_org import WS_ALPHA
from tests.data.airbyte.multi_org import WS_BETA
from tests.data.airbyte.multi_org import WS_GAMMA


def _run(neo4j_session, api: FakeAirbyteAPI, update_tag: int) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        airbyte_api_url=multi_org.API_URL,
        airbyte_client_id="synthetic-client-id",
        airbyte_client_secret="synthetic-client-secret",
    )
    with patch.object(
        cartography.intel.airbyte,
        "AirbyteClient",
        side_effect=lambda **kwargs: make_client(api),
    ):
        cartography.intel.airbyte.start_airbyte_ingestion(neo4j_session, config)


def _identity_graph(neo4j_session) -> dict[tuple[str, str, str], int]:
    """Every user membership and access edge, mapped to its lastupdated."""
    result = neo4j_session.run(
        """
        MATCH (o:AirbyteOrganization)-[r:RESOURCE]->(u:AirbyteUser)
        RETURN o.id AS src, type(r) AS rel, u.id AS dst, r.lastupdated AS tag
        UNION
        MATCH (u:AirbyteUser)-[r:ADMIN_OF|MEMBER_OF]->(t)
        RETURN u.id AS src, type(r) AS rel, t.id AS dst, r.lastupdated AS tag
        """,
    )
    return {(r["src"], r["rel"], r["dst"]): r["tag"] for r in result}


def _user_ids(neo4j_session) -> set[str]:
    return {
        r["id"] for r in neo4j_session.run("MATCH (u:AirbyteUser) RETURN u.id AS id")
    }


def _baseline(tag: int) -> dict[tuple[str, str, str], int]:
    """The identity graph after a complete sync of initial_permissions()."""
    return {
        (ORG_ALPHA, "RESOURCE", APP_OWNER): tag,
        (ORG_ALPHA, "RESOURCE", ALPHA_USER): tag,
        (ORG_ALPHA, "RESOURCE", SHARED_USER): tag,
        (ORG_BETA, "RESOURCE", APP_OWNER): tag,
        (ORG_BETA, "RESOURCE", SHARED_USER): tag,
        (ORG_BETA, "RESOURCE", BETA_USER): tag,
        (ORG_GAMMA, "RESOURCE", APP_OWNER): tag,
        (ORG_GAMMA, "RESOURCE", GAMMA_USER): tag,
        (APP_OWNER, "ADMIN_OF", ORG_ALPHA): tag,
        (APP_OWNER, "ADMIN_OF", ORG_BETA): tag,
        (APP_OWNER, "ADMIN_OF", ORG_GAMMA): tag,
        (ALPHA_USER, "ADMIN_OF", ORG_ALPHA): tag,
        (ALPHA_USER, "MEMBER_OF", WS_ALPHA): tag,
        (SHARED_USER, "MEMBER_OF", WS_ALPHA): tag,
        (SHARED_USER, "ADMIN_OF", WS_BETA): tag,
        (SHARED_USER, "MEMBER_OF", WS_BETA): tag,
        (BETA_USER, "MEMBER_OF", WS_BETA): tag,
        (GAMMA_USER, "MEMBER_OF", WS_GAMMA): tag,
    }


def _revoke(api: FakeAirbyteAPI, org_id: str, user_id: str, scope_id: str) -> None:
    api.permissions[org_id] = [
        p
        for p in api.permissions[org_id]
        if not (p["userId"] == user_id and p["scopeId"] == scope_id)
    ]


@pytest.fixture
def api(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    api = FakeAirbyteAPI()
    _run(neo4j_session, api, 1)
    assert _identity_graph(neo4j_session) == _baseline(1)
    return api


def test_users_denial_does_not_stop_inventory_or_later_organizations(
    neo4j_session,
    api,
    caplog,
):
    # Arrange: Beta can no longer be read, Alpha revoked a permission, and Beta
    # removed a user that we cannot observe.
    api.fail("GET", "/users", 403, organizationId=ORG_BETA)
    _revoke(api, ORG_ALPHA, ALPHA_USER, ORG_ALPHA)
    _revoke(api, ORG_BETA, BETA_USER, WS_BETA)
    api.requests.clear()

    # Act
    with caplog.at_level(logging.WARNING):
        _run(neo4j_session, api, 2)

    # Assert: Alpha and Gamma are refreshed and cleaned up. Beta's users and
    # their edges keep their previous state, including SHARED_USER's Beta edges,
    # which Alpha's cleanup must not delete. APP_OWNER reads its own permissions
    # across organizations, so its Beta admin edge is refreshed by Alpha's sync.
    expected = _baseline(2)
    del expected[(ALPHA_USER, "ADMIN_OF", ORG_ALPHA)]
    for key in (
        (ORG_BETA, "RESOURCE", APP_OWNER),
        (ORG_BETA, "RESOURCE", SHARED_USER),
        (ORG_BETA, "RESOURCE", BETA_USER),
        (SHARED_USER, "ADMIN_OF", WS_BETA),
        (SHARED_USER, "MEMBER_OF", WS_BETA),
        (BETA_USER, "MEMBER_OF", WS_BETA),
    ):
        expected[key] = 1
    assert _identity_graph(neo4j_session) == expected

    # Assert: Beta's pipeline inventory was still synced after the denial, and
    # Gamma was reached.
    denied = api.requests.index(
        ("GET", "/users", {"organizationId": ORG_BETA, "offset": "0"})
    )
    later_requests = [(method, uri) for method, uri, _ in api.requests[denied + 1 :]]
    for uri in ("/sources", "/destinations", "/tags", "/connections"):
        assert ("GET", uri) in later_requests
    source_tag = neo4j_session.run(
        """
        MATCH (:AirbyteOrganization {id: $org_id})-[r:RESOURCE]->(s:AirbyteSource {id: $source_id})
        RETURN r.lastupdated AS tag
        """,
        org_id=ORG_BETA,
        source_id=multi_org.SOURCE_BETA,
    ).single()["tag"]
    assert source_tag == 2
    assert (ORG_GAMMA, "RESOURCE", GAMMA_USER) in _identity_graph(neo4j_session)

    # Assert: the caller is told which organization is missing identity data.
    assert f"GET /users for organization {ORG_BETA}" in caplog.text
    assert (
        "users and permissions were not refreshed for 1 of 3 organization(s): "
        f"{ORG_BETA}" in caplog.text
    )


@pytest.mark.parametrize("denial", ["permissions_of_later_user", "later_users_page"])
def test_incomplete_identity_read_keeps_previous_snapshot(neo4j_session, api, denial):
    # Arrange: Alpha added and revoked access, then denied part of the read.
    api.permissions[ORG_ALPHA].append(
        permission(NEW_ALPHA_USER, "workspace_admin", "workspace", WS_ALPHA),
    )
    _revoke(api, ORG_ALPHA, ALPHA_USER, ORG_ALPHA)
    if denial == "permissions_of_later_user":
        api.fail(
            "GET", "/permissions", 403, userId=SHARED_USER, organizationId=ORG_ALPHA
        )
    else:
        api.users_page_size = 1
        api.fail("GET", "/users", 403, organizationId=ORG_ALPHA, offset="2")

    # Act
    _run(neo4j_session, api, 2)

    # Assert: no part of Alpha's partial read was written or cleaned up.
    expected = _baseline(2)
    for key in (
        (ORG_ALPHA, "RESOURCE", APP_OWNER),
        (ORG_ALPHA, "RESOURCE", ALPHA_USER),
        (ORG_ALPHA, "RESOURCE", SHARED_USER),
        (ALPHA_USER, "ADMIN_OF", ORG_ALPHA),
        (ALPHA_USER, "MEMBER_OF", WS_ALPHA),
        (SHARED_USER, "MEMBER_OF", WS_ALPHA),
    ):
        expected[key] = 1
    assert _identity_graph(neo4j_session) == expected
    assert NEW_ALPHA_USER not in _user_ids(neo4j_session)


def test_restored_access_resumes_refresh_and_cleanup(neo4j_session, api):
    # Arrange: while Beta is denied, SHARED_USER leaves Alpha.
    api.fail("GET", "/users", 403, organizationId=ORG_BETA)
    _revoke(api, ORG_ALPHA, SHARED_USER, WS_ALPHA)

    # Act
    _run(neo4j_session, api, 2)

    # Assert: SHARED_USER is still in Beta, so the user and its edges are kept.
    # Its Alpha workspace edge is only removed once Beta can be read again.
    identity = _identity_graph(neo4j_session)
    assert (ORG_ALPHA, "RESOURCE", SHARED_USER) not in identity
    assert identity[(ORG_BETA, "RESOURCE", SHARED_USER)] == 1
    assert identity[(SHARED_USER, "MEMBER_OF", WS_ALPHA)] == 1
    assert identity[(SHARED_USER, "ADMIN_OF", WS_BETA)] == 1

    # Arrange: Beta is readable again, downgraded SHARED_USER and removed BETA_USER.
    api.clear_failures()
    _revoke(api, ORG_BETA, SHARED_USER, WS_BETA)
    api.permissions[ORG_BETA].append(
        permission(SHARED_USER, "workspace_reader", "workspace", WS_BETA),
    )
    _revoke(api, ORG_BETA, BETA_USER, WS_BETA)

    # Act
    _run(neo4j_session, api, 3)

    # Assert
    expected = {
        key: 3
        for key in _baseline(3)
        if SHARED_USER not in key and BETA_USER not in key
    }
    expected[(ORG_BETA, "RESOURCE", SHARED_USER)] = 3
    expected[(SHARED_USER, "MEMBER_OF", WS_BETA)] = 3
    assert _identity_graph(neo4j_session) == expected
    assert BETA_USER not in _user_ids(neo4j_session)


def test_empty_users_response_is_a_complete_snapshot(neo4j_session, api, caplog):
    # Arrange: Beta answers successfully with no users.
    api.fail("GET", "/users", (200, {"data": []}), organizationId=ORG_BETA)

    # Act
    with caplog.at_level(logging.WARNING):
        _run(neo4j_session, api, 2)

    # Assert: Beta's memberships are cleaned up. SHARED_USER stays for Alpha, and
    # APP_OWNER's Beta admin edge comes from its own permissions read by Alpha.
    expected = {
        key: 2
        for key in _baseline(2)
        if ORG_BETA not in key and WS_BETA not in key and BETA_USER not in key
    }
    expected[(APP_OWNER, "ADMIN_OF", ORG_BETA)] = 2
    assert _identity_graph(neo4j_session) == expected
    assert BETA_USER not in _user_ids(neo4j_session)
    assert "incomplete identity coverage" not in caplog.text


def test_denial_of_other_endpoints_still_fails(neo4j_session, api):
    # Arrange
    api.fail("GET", "/sources", 403)

    # Act and assert
    with pytest.raises(requests.HTTPError) as exc_info:
        _run(neo4j_session, api, 2)
    assert exc_info.value.response.status_code == 403
