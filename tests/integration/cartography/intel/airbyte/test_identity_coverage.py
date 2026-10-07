import logging
from unittest.mock import patch

import pytest
import requests

import cartography.intel.airbyte
import cartography.intel.airbyte.users
from cartography.config import Config
from tests.data.airbyte import multi_org
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
from tests.integration.cartography.intel.airbyte.fake_api import FakeAirbyteAPI
from tests.integration.cartography.intel.airbyte.fake_api import FORBIDDEN_DETAIL
from tests.integration.cartography.intel.airbyte.fake_api import make_client
from tests.integration.cartography.intel.airbyte.fake_api import TEST_ACCESS_TOKEN
from tests.integration.cartography.intel.airbyte.fake_api import TEST_CLIENT_SECRET


def _run(neo4j_session, api: FakeAirbyteAPI, update_tag: int) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        airbyte_api_url=multi_org.API_URL,
        airbyte_client_id="synthetic-client-id",
        airbyte_client_secret=TEST_CLIENT_SECRET,
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
        (SHARED_USER, "ADMIN_OF", ORG_BETA): tag,
        (APP_OWNER, "MEMBER_OF", WS_ALPHA): tag,
        (APP_OWNER, "ADMIN_OF", WS_BETA): tag,
        (APP_OWNER, "MEMBER_OF", WS_BETA): tag,
    }


def _revoke(api: FakeAirbyteAPI, org_id: str, user_id: str, scope_id: str) -> None:
    api.permissions[org_id] = [
        p
        for p in api.permissions[org_id]
        if not (p["userId"] == user_id and p["scopeId"] == scope_id)
    ]


def _demote(api: FakeAirbyteAPI, org_id: str, user_id: str) -> None:
    _revoke(api, org_id, user_id, org_id)
    api.permissions[org_id].append(
        permission(user_id, "organization_member", "organization", org_id),
    )


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
    # Arrange: Beta can no longer be read. Alpha demoted an admin and removed
    # SHARED_USER, and Beta removed a user that we cannot observe.
    api.fail("GET", "/users", 403, organizationId=ORG_BETA)
    _demote(api, ORG_ALPHA, ALPHA_USER)
    _revoke(api, ORG_ALPHA, SHARED_USER, ORG_ALPHA)
    _revoke(api, ORG_BETA, BETA_USER, ORG_BETA)

    # Act
    with caplog.at_level(logging.WARNING):
        _run(neo4j_session, api, 2)

    # Assert: Alpha and Gamma are refreshed and cleaned up. Every edge Beta
    # wrote, including SHARED_USER's Beta admin edge, keeps its previous state.
    expected = _baseline(2)
    for key in (
        (ALPHA_USER, "ADMIN_OF", ORG_ALPHA),
        (ORG_ALPHA, "RESOURCE", SHARED_USER),
    ):
        del expected[key]
    for key in (
        (ORG_BETA, "RESOURCE", APP_OWNER),
        (APP_OWNER, "ADMIN_OF", ORG_BETA),
        (ORG_BETA, "RESOURCE", SHARED_USER),
        (SHARED_USER, "ADMIN_OF", ORG_BETA),
        (ORG_BETA, "RESOURCE", BETA_USER),
    ):
        expected[key] = 1
    assert _identity_graph(neo4j_session) == expected

    # Assert: Beta's pipeline inventory was still synced.
    source_tag = neo4j_session.run(
        """
        MATCH (:AirbyteOrganization {id: $org_id})-[r:RESOURCE]->(:AirbyteSource {id: $source_id})
        RETURN r.lastupdated AS tag
        """,
        org_id=ORG_BETA,
        source_id=multi_org.SOURCE_BETA,
    ).single()["tag"]
    assert source_tag == 2

    # Assert: the warning names the organization without leaking secrets or the
    # provider's response.
    assert f"GET /users for organization {ORG_BETA}" in caplog.text
    assert f"1 of 3 organization(s): {ORG_BETA}" in caplog.text
    for secret in (TEST_CLIENT_SECRET, TEST_ACCESS_TOKEN, FORBIDDEN_DETAIL):
        assert secret not in caplog.text


@pytest.mark.parametrize("denial", ["permissions_of_later_user", "later_users_page"])
def test_incomplete_identity_read_keeps_previous_snapshot(neo4j_session, api, denial):
    # Arrange: Alpha added a user and demoted an admin, then denied part of the
    # read.
    api.permissions[ORG_ALPHA].append(
        permission(NEW_ALPHA_USER, "organization_admin", "organization", ORG_ALPHA),
    )
    _demote(api, ORG_ALPHA, ALPHA_USER)
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
        (APP_OWNER, "ADMIN_OF", ORG_ALPHA),
        (ORG_ALPHA, "RESOURCE", ALPHA_USER),
        (ORG_ALPHA, "RESOURCE", SHARED_USER),
        (ALPHA_USER, "ADMIN_OF", ORG_ALPHA),
    ):
        expected[key] = 1
    assert _identity_graph(neo4j_session) == expected


def test_restored_access_resumes_refresh_and_cleanup(neo4j_session, api):
    # Arrange: Beta is denied for one run.
    api.fail("GET", "/users", 403, organizationId=ORG_BETA)
    _run(neo4j_session, api, 2)

    # Arrange: Beta is readable again, demoted SHARED_USER and removed BETA_USER.
    api.clear_failures()
    _demote(api, ORG_BETA, SHARED_USER)
    _revoke(api, ORG_BETA, BETA_USER, ORG_BETA)

    # Act
    _run(neo4j_session, api, 3)

    # Assert
    expected = _baseline(3)
    del expected[(SHARED_USER, "ADMIN_OF", ORG_BETA)]
    del expected[(ORG_BETA, "RESOURCE", BETA_USER)]
    assert _identity_graph(neo4j_session) == expected


def test_empty_users_response_is_a_complete_snapshot(neo4j_session, api):
    # Arrange: Beta answers successfully with no users.
    api.fail("GET", "/users", (200, {"data": []}), organizationId=ORG_BETA)

    # Act
    _run(neo4j_session, api, 2)

    # Assert: unlike a denial, every edge about Beta is cleaned up. The
    # application owner's Beta workspace grant still holds, so it stays.
    expected = {
        key: 2 for key in _baseline(2) if ORG_BETA not in key and BETA_USER not in key
    }
    assert _identity_graph(neo4j_session) == expected


def test_owner_workspace_grants_refresh_while_an_organization_is_denied(
    neo4j_session, api
):
    # Arrange: the last organization synced is denied, and the application
    # owner lost its Alpha workspace grant.
    api.fail("GET", "/users", 403, organizationId=ORG_GAMMA)
    _revoke(api, ORG_ALPHA, APP_OWNER, WS_ALPHA)

    # Act
    _run(neo4j_session, api, 2)

    # Assert: the owner's workspace edges follow its own permissions, which do
    # not depend on any organization's users being readable.
    expected = _baseline(2)
    del expected[(APP_OWNER, "MEMBER_OF", WS_ALPHA)]
    for key in (
        (ORG_GAMMA, "RESOURCE", APP_OWNER),
        (APP_OWNER, "ADMIN_OF", ORG_GAMMA),
        (ORG_GAMMA, "RESOURCE", GAMMA_USER),
    ):
        expected[key] = 1
    assert _identity_graph(neo4j_session) == expected


def test_denial_of_other_endpoints_still_fails(neo4j_session, api):
    # Arrange
    api.fail("GET", "/sources", 403)

    # Act and assert
    with pytest.raises(requests.HTTPError):
        _run(neo4j_session, api, 2)


@pytest.mark.parametrize(
    "method,uri,result,expected",
    [
        # AirbyteClient.get() exchanges the token first, inside the same call.
        ("POST", "/applications/token", 401, requests.HTTPError),
        ("POST", "/applications/token", 403, requests.HTTPError),
        ("GET", "/users", 401, requests.HTTPError),
        ("GET", "/permissions", 429, requests.HTTPError),
        ("GET", "/users", 503, requests.HTTPError),
        (
            "GET",
            "/permissions",
            requests.ConnectionError("reset"),
            requests.ConnectionError,
        ),
        ("GET", "/users", (200, b"<html>gateway</html>"), requests.JSONDecodeError),
    ],
)
def test_failures_other_than_an_identity_denial_are_raised(
    neo4j_session, method, uri, result, expected
):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail(method, uri, result)

    # Act and assert
    with pytest.raises(expected):
        cartography.intel.airbyte.users.sync(
            neo4j_session,
            make_client(api),
            ORG_ALPHA,
            {"UPDATE_TAG": 1, "ORG_ID": ORG_ALPHA},
        )
