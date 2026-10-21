import json
from copy import deepcopy
from unittest.mock import MagicMock

import httpx
import pytest
from cloudflare import Cloudflare

from cartography.intel.cloudflare import access
from tests.data.cloudflare.access import APPLICATIONS
from tests.data.cloudflare.access import POLICIES


def test_transforms_preserve_provider_data_without_mutating_fixtures():
    # Arrange
    applications = deepcopy(APPLICATIONS)
    policies = deepcopy(POLICIES)

    # Act
    application_rows = access.transform_applications(applications, "account-one")
    policy_rows = access.transform_policies(policies, "account-one", "app-one")

    # Assert
    assert applications == APPLICATIONS
    assert policies == POLICIES
    assert application_rows[0]["id"] == "account-one/app-one"
    assert application_rows[0]["application_id"] == "app-one"
    assert application_rows[0]["domain"] == "dashboard.example.com/admin"
    assert application_rows[1]["domain"] is None
    assert policy_rows[0]["id"] == "account-one/app-one/shared-policy"
    assert policy_rows[0]["policy_id"] == "shared-policy"
    assert policy_rows[0]["application_id"] == "account-one/app-one"
    for field in ("include", "require", "exclude"):
        assert json.loads(policy_rows[0][field]) == POLICIES[0][field]
    assert policy_rows[1]["require"] == "[]"
    assert policy_rows[1]["exclude"] is None


@pytest.mark.parametrize("decision", ["allow", "deny", "non_identity", "bypass"])
def test_policy_decisions_are_kept_as_configuration(decision):
    # Arrange
    policy = {"id": "policy", "decision": decision}

    # Act
    row = access.transform_policies([policy], "account", "app")[0]

    # Assert
    assert row["decision"] == decision
    assert all(row[field] is None for field in ("include", "require", "exclude"))


def test_reusable_policy_attachments_keep_their_application_precedence():
    # Arrange
    first_policy = {**POLICIES[0], "precedence": 1}
    second_policy = {**POLICIES[0], "precedence": 10}

    # Act
    first = access.transform_policies([first_policy], "account", "one")[0]
    second = access.transform_policies([second_policy], "account", "two")[0]
    other_account = access.transform_policies([first_policy], "other", "one")[0]

    # Assert
    assert len({first["id"], second["id"], other_account["id"]}) == 3
    assert first["policy_id"] == second["policy_id"] == "shared-policy"
    assert first["precedence"] == 1
    assert second["precedence"] == 10


@pytest.mark.parametrize("with_metadata", [False, True])
def test_sdk_paginates_applications_with_embedded_policies(with_metadata):
    # Arrange: keep the real SDK; no separate policy endpoint may be called.
    calls = []
    records = [
        {**APPLICATIONS[0], "policies": POLICIES},
        {**APPLICATIONS[1], "policies": [{**POLICIES[0], "precedence": 10}]},
    ]

    def handler(request):
        assert request.url.path == "/client/v4/accounts/account/access/apps"
        page = int(request.url.params.get("page", "1"))
        assert page <= 3, "SDK requested an unexpected extra page"
        calls.append(page)
        payload = {"success": True, "result": records[page - 1 : page]}
        if with_metadata:
            payload["result_info"] = {"page": page, "per_page": 1, "total_pages": 2}
        return httpx.Response(200, json=payload)

    with Cloudflare(
        api_token="synthetic",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    ) as client:
        # Act
        applications = access.get_applications(client, "account")

    # Assert
    assert [row["id"] for row in applications] == ["app-one", "app-two"]
    assert applications[0]["created_at"].startswith("2026-01-01")
    assert applications[0]["policies"][0]["include"] == POLICIES[0]["include"]
    assert applications[1]["policies"][0]["precedence"] == 10
    # SDK 5.8.0 stops on an empty terminal page, even with total_pages=2.
    assert calls == [1, 2, 3]


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 503])
@pytest.mark.parametrize("failed_page", [1, 2])
def test_api_errors_skip_access_without_touching_neo4j(status, failed_page, caplog):
    # Arrange: a later-page failure must not load or clean a partial inventory.
    session = MagicMock()
    calls = []

    def handler(request):
        page = int(request.url.params.get("page", "1"))
        calls.append(page)
        if page == failed_page:
            return httpx.Response(
                status, json={"errors": [{"message": "private-response"}]}
            )
        return httpx.Response(200, json={"result": [APPLICATIONS[0]]})

    with Cloudflare(
        api_token="synthetic",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    ) as client:
        # Act
        access.sync(session, client, {"UPDATE_TAG": 1}, "account", [], [])

    # Assert
    assert calls == list(range(1, failed_page + 1))
    assert session.mock_calls == []
    assert "Skipping Access loading and cleanup" in caplog.text
    assert "private-response" not in caplog.text


def test_connection_errors_skip_access_without_touching_neo4j(caplog):
    # Arrange
    session = MagicMock()

    def handler(request):
        raise httpx.ConnectError("private-response", request=request)

    with Cloudflare(
        api_token="synthetic",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    ) as client:
        # Act
        access.sync(session, client, {"UPDATE_TAG": 1}, "account", [], [])

    # Assert
    assert session.mock_calls == []
    assert "Skipping Access loading and cleanup" in caplog.text
    assert "private-response" not in caplog.text


@pytest.mark.parametrize(
    "domain,records,expected",
    [
        (
            "APP.Example.com./admin",
            ["app.example.com", "other.example.com"],
            {"app.example.com"},
        ),
        (
            "*.example.com",
            ["a.example.com", "b.example.com", "example.com", "a.b.example.com"],
            {"a.example.com", "b.example.com"},
        ),
        ("*.*.example.com", ["a.b.example.com", "a.example.com"], {"a.b.example.com"}),
        (
            "*test.example.com",
            ["test.example.com", "alphatest.example.com", "beta.test.example.com"],
            {"test.example.com", "alphatest.example.com"},
        ),
        (
            "example.com/*",
            ["example.com", "notexample.com", "a.example.com"],
            {"example.com"},
        ),
        ("*.example.com", ["*.example.com"], set()),
    ],
)
def test_dns_hostname_correlation_obeys_access_label_boundaries(
    domain, records, expected
):
    # Arrange
    applications = [{"id": "app", "type": "self_hosted", "domain": domain}]
    inventory = [{"id": name, "name": name} for name in records]

    # Act
    row = access.transform_applications(applications, "account", records=inventory)[0]

    # Assert
    assert set(row["dns_record_ids"]) == expected
    assert row["public_domains"] == [domain]


@pytest.mark.parametrize(
    "domain",
    [
        "",
        "127.0.0.1",
        "[::1]",
        "a.example.com:443",
        "a.example.com?x=1",
        "a.example.com/#fragment",
        "https://user:pass@a.example.com",
        "a..example.com",
        "a?.example.com",
        "a**b.example.com",
        "ftp://a.example.com",
        "bad_host.example.com",
    ],
)
def test_unsupported_hostnames_do_not_create_links(domain):
    # Arrange
    applications = [{"id": "app", "type": "self_hosted", "domain": domain}]

    # Act
    row = access.transform_applications(applications, "account")[0]

    # Assert
    assert row["dns_record_ids"] == []
    assert row["zone_ids"] == []
    assert row["public_domains"] == []


def test_multiple_destinations_are_public_only_and_override_legacy_fields():
    # Arrange
    application = {
        "id": "app",
        "type": "self_hosted",
        "domain": "old.example.com",
        "destinations": [
            {"type": "public", "uri": "a.example.com/admin"},
            {"uri": "b.example.net/*"},
            {"type": "private", "hostname": "private.example.com"},
        ],
    }
    zones = [
        {"id": "parent", "name": "example.com"},
        {"id": "child", "name": "a.example.com"},
        {"id": "net", "name": "example.net"},
    ]

    # Act
    row = access.transform_applications([application], "account", zones)[0]
    empty = access.transform_applications(
        [{**application, "destinations": []}], "account", zones
    )[0]

    # Assert
    assert row["public_domains"] == ["a.example.com/admin", "b.example.net/*"]
    assert row["zone_ids"] == ["child", "net"]
    assert empty["public_domains"] == []
    assert empty["zone_ids"] == []


@pytest.mark.parametrize("app_type", ["saas", "bookmark", "infrastructure", None])
def test_non_public_application_types_are_not_correlated(app_type):
    # Arrange
    application = {"id": "app", "type": app_type, "domain": "a.example.com"}

    # Act
    row = access.transform_applications(
        [application], "account", records=[{"id": "record", "name": "a.example.com"}]
    )[0]

    # Assert
    assert row["dns_record_ids"] == []
    assert row["public_domains"] == []


def test_legacy_multiple_domains_keep_paths_and_do_not_match_deceptive_zone_suffixes():
    # Arrange
    app = {
        "id": "app",
        "type": "self_hosted",
        "domain": "one.example.com/admin",
        "self_hosted_domains": ["one.example.com/admin", "two.notexample.com"],
    }

    # Act
    row = access.transform_applications(
        [app], "account", [{"id": "zone", "name": "example.com"}]
    )[0]

    # Assert
    assert row["public_domains"] == ["one.example.com/admin", "two.notexample.com"]
    assert row["zone_ids"] == ["zone"]
