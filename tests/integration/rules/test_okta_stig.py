from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.intel.okta.authenticators import _load_okta_authenticators
from cartography.intel.okta.users import _load_okta_users
from cartography.rules.data.rules.okta_stig import okta_inactive_users_not_disabled
from cartography.rules.data.rules.okta_stig import (
    okta_verify_fips_compliance_not_required,
)

TEST_ORG_ID = "synthetic-okta-org"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "OKTA_ORG_ID": TEST_ORG_ID,
}

NOW = datetime.now(timezone.utc)


def _days_ago(days: int) -> datetime:
    return NOW - timedelta(days=days)


def _user(user_id: str, status: str, last_login, created) -> dict:
    return {
        "id": user_id,
        "login": f"{user_id}@example.invalid",
        "email": f"{user_id}@example.invalid",
        "status": status,
        "last_login": last_login,
        "created": created,
    }


TEST_USERS = [
    _user("active-recent", "ACTIVE", _days_ago(2), _days_ago(400)),
    _user("active-stale", "ACTIVE", _days_ago(60), _days_ago(400)),
    _user("active-boundary", "ACTIVE", _days_ago(34), _days_ago(400)),
    _user("active-never-logged-in-old", "ACTIVE", None, _days_ago(90)),
    _user("active-never-logged-in-new", "ACTIVE", None, _days_ago(5)),
    # Older syncs and the test fixtures store timestamps as ISO 8601 strings.
    _user(
        "password-expired-stale-string",
        "PASSWORD_EXPIRED",
        "2019-01-01T00:00:01.000Z",
        "2018-01-01T00:00:01.000Z",
    ),
    _user("locked-out-stale", "LOCKED_OUT", _days_ago(50), _days_ago(400)),
    _user("suspended-stale", "SUSPENDED", _days_ago(200), _days_ago(400)),
    _user("deprovisioned-stale", "DEPROVISIONED", _days_ago(200), _days_ago(400)),
    _user("provisioned-never-activated", "PROVISIONED", None, _days_ago(200)),
]

TEST_AUTHENTICATORS: list[dict[str, Any]] = [
    {
        "id": "aut-okta-verify-optional",
        "key": "okta_verify",
        "name": "Okta Verify",
        "status": "ACTIVE",
        "settings_compliance": '{"fips": "OPTIONAL"}',
    },
    {
        "id": "aut-okta-verify-required",
        "key": "okta_verify",
        "name": "Okta Verify",
        "status": "ACTIVE",
        "settings_compliance": '{"fips": "REQUIRED"}',
    },
    {
        "id": "aut-okta-verify-unset",
        "key": "okta_verify",
        "name": "Okta Verify",
        "status": "ACTIVE",
        "settings_compliance": None,
    },
    {
        "id": "aut-okta-verify-inactive",
        "key": "okta_verify",
        "name": "Okta Verify",
        "status": "INACTIVE",
        "settings_compliance": '{"fips": "OPTIONAL"}',
    },
    {
        "id": "aut-webauthn",
        "key": "webauthn",
        "name": "Security Key or Biometric",
        "status": "ACTIVE",
        "settings_compliance": None,
    },
]


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "MERGE (o:OktaOrganization {id: $org_id}) SET o.lastupdated = $update_tag",
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _run_query(neo4j_session, query: str) -> list[dict]:
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def _count(neo4j_session, query: str) -> int:
    return _run_query(neo4j_session, query)[0]["count"]


def test_okta_inactive_users_not_disabled(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _load_okta_users(neo4j_session, TEST_USERS, COMMON_JOB_PARAMETERS)
    fact = okta_inactive_users_not_disabled.facts[0]

    # Act
    findings = _run_query(neo4j_session, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    total = _count(neo4j_session, fact.cypher_count_query)

    # Assert
    expected = {
        "active-stale",
        "active-never-logged-in-old",
        "password-expired-stale-string",
        "locked-out-stale",
    }
    assert {row["user_id"] for row in findings} == expected
    assert {row["u"]["id"] for row in visual_rows} == expected
    assert total == 7
    by_id = {row["user_id"]: row for row in findings}
    assert by_id["active-stale"]["days_inactive"] == 60
    assert by_id["active-never-logged-in-old"]["last_login"] is None
    assert by_id["active-never-logged-in-old"]["days_inactive"] == 90
    assert all(row["org_id"] == TEST_ORG_ID for row in findings)
    parsed = okta_inactive_users_not_disabled.parse_results(fact, findings)
    assert {finding.user_id for finding in parsed} == expected


def test_okta_verify_fips_compliance_not_required(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _load_okta_authenticators(neo4j_session, TEST_AUTHENTICATORS, COMMON_JOB_PARAMETERS)
    fact = okta_verify_fips_compliance_not_required.facts[0]

    # Act
    findings = _run_query(neo4j_session, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    total = _count(neo4j_session, fact.cypher_count_query)

    # Assert
    expected = {"aut-okta-verify-optional", "aut-okta-verify-unset"}
    assert {row["authenticator_id"] for row in findings} == expected
    assert {row["a"]["id"] for row in visual_rows} == expected
    assert total == 3
    parsed = okta_verify_fips_compliance_not_required.parse_results(fact, findings)
    assert {finding.authenticator_id for finding in parsed} == expected
