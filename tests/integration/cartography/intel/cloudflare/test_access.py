import json
from copy import deepcopy

import httpx
import pytest
from cloudflare import Cloudflare

from cartography.intel.cloudflare import access
from cartography.intel.cloudflare.accounts import load_accounts
from cartography.intel.cloudflare.dnsrecords import load_dnsrecords
from cartography.intel.cloudflare.zones import load_zones
from tests.data.cloudflare.access import APPLICATIONS
from tests.data.cloudflare.access import DNS_RECORDS
from tests.data.cloudflare.access import DNS_ZONES
from tests.data.cloudflare.access import POLICIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

ACCOUNT = "access-test-account"
OTHER_ACCOUNT = "other-access-test-account"


def _client(
    applications, policies, failed_path=None, failed_page=1, status=403, calls=None
):
    """Mock only the provider HTTP boundary; keep the real SDK and graph flows."""
    applications = [
        {**app, "policies": policies.get(app["id"], [])} for app in applications
    ]

    def handler(request):
        page = int(request.url.params.get("page", "1"))
        assert page <= 3, "SDK requested an unexpected extra page"
        if calls is not None:
            calls.append((request.url.path.removeprefix("/client/v4"), page))
        if (
            request.url.path.removeprefix("/client/v4") == failed_path
            and page == failed_page
        ):
            return httpx.Response(
                status, json={"errors": [{"message": "test failure"}]}
            )
        assert request.url.path.endswith("/access/apps")
        records = applications
        # SDK 5.8.0 continues until an empty page, independently of result_info.
        return httpx.Response(
            200,
            json={
                "result": records[page - 1 : page],
                "result_info": {
                    "page": page,
                    "per_page": 1,
                    "total_pages": max(1, len(records)),
                },
            },
        )

    return Cloudflare(
        api_token="synthetic",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    )


def _sync(
    session,
    applications=APPLICATIONS,
    policies=None,
    account=ACCOUNT,
    tag=1,
    dns_records=None,
    **kwargs,
):
    zones = [{**zone, "id": f"{account}/{zone['id']}"} for zone in DNS_ZONES]
    if dns_records is None:
        dns_records = DNS_RECORDS
    records = [
        {"id": f"{account}/{record['id']}", "name": record["name"]}
        for record in dns_records
        if record.get("proxied") and record.get("type") in ("A", "AAAA", "CNAME")
    ]
    policy_data = {"app-one": POLICIES, "app-two": [{**POLICIES[0], "precedence": 10}]}
    with _client(
        applications, policy_data if policies is None else policies, **kwargs
    ) as client:
        access.sync(
            session,
            client,
            {"UPDATE_TAG": tag, "account_id": account},
            account,
            zones,
            records,
        )


@pytest.fixture(autouse=True)
def _clean_access_graph(neo4j_session):
    # Arrange a clean graph for every test, including parametrized cases.
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    load_accounts(neo4j_session, [{"id": ACCOUNT}, {"id": OTHER_ACCOUNT}], 1)
    yield
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


def test_sync_loads_properties_and_account_and_application_relationships(neo4j_session):
    # Arrange
    expected_applications = {
        (f"{ACCOUNT}/app-one", "self_hosted"),
        (f"{ACCOUNT}/app-two", "bookmark"),
    }

    # Act
    _sync(neo4j_session)

    # Assert
    assert (
        check_nodes(neo4j_session, "CloudflareAccessApplication", ["id", "type"])
        == expected_applications
    )
    assert check_nodes(
        neo4j_session, "CloudflareAccessPolicy", ["id", "decision", "precedence"]
    ) == {
        (f"{ACCOUNT}/app-one/shared-policy", "allow", 1),
        (f"{ACCOUNT}/app-one/bypass-policy", "bypass", 2),
        (f"{ACCOUNT}/app-two/shared-policy", "allow", 10),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccount",
        "id",
        "CloudflareAccessApplication",
        "id",
        "RESOURCE",
    ) == {
        (ACCOUNT, f"{ACCOUNT}/app-one"),
        (ACCOUNT, f"{ACCOUNT}/app-two"),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccount",
        "id",
        "CloudflareAccessPolicy",
        "id",
        "RESOURCE",
    ) == {
        (ACCOUNT, f"{ACCOUNT}/app-one/shared-policy"),
        (ACCOUNT, f"{ACCOUNT}/app-one/bypass-policy"),
        (ACCOUNT, f"{ACCOUNT}/app-two/shared-policy"),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareAccessPolicy",
        "id",
        "HAS_POLICY",
    ) == {
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/shared-policy"),
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/bypass-policy"),
        (f"{ACCOUNT}/app-two", f"{ACCOUNT}/app-two/shared-policy"),
    }
    assert check_nodes(
        neo4j_session,
        "CloudflareAccessPolicy",
        ["id", "include", "require", "exclude", "session_duration", "created_at"],
    ) >= {
        (
            f"{ACCOUNT}/app-one/shared-policy",
            json.dumps(POLICIES[0]["include"], sort_keys=True),
            json.dumps(POLICIES[0]["require"], sort_keys=True),
            json.dumps(POLICIES[0]["exclude"], sort_keys=True),
            "8h",
            POLICIES[0]["created_at"],
        )
    }
    assert check_nodes(
        neo4j_session,
        "CloudflareAccessApplication",
        ["id", "domain", "aud", "session_duration", "updated_at"],
    ) >= {
        (
            f"{ACCOUNT}/app-one",
            APPLICATIONS[0]["domain"],
            "aud-one",
            "24h",
            "2026-01-02T00:00:00Z",
        )
    }


def test_repeated_sync_updates_in_place_without_duplicate_nodes_or_edges(neo4j_session):
    # Arrange
    _sync(neo4j_session)
    applications = deepcopy(APPLICATIONS)
    applications[0]["name"] = "Renamed application"

    # Act
    _sync(neo4j_session, applications=applications, tag=2)

    # Assert
    assert check_nodes(
        neo4j_session, "CloudflareAccessApplication", ["id", "name", "lastupdated"]
    ) == {
        (f"{ACCOUNT}/app-one", "Renamed application", 2),
        (f"{ACCOUNT}/app-two", "Bookmark", 2),
    }
    assert check_nodes(
        neo4j_session, "CloudflareAccessPolicy", ["id", "lastupdated"]
    ) == {
        (f"{ACCOUNT}/app-one/shared-policy", 2),
        (f"{ACCOUNT}/app-one/bypass-policy", 2),
        (f"{ACCOUNT}/app-two/shared-policy", 2),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareAccessPolicy",
        "id",
        "HAS_POLICY",
    ) == {
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/shared-policy"),
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/bypass-policy"),
        (f"{ACCOUNT}/app-two", f"{ACCOUNT}/app-two/shared-policy"),
    }


def test_cleanup_removes_stale_applications_and_policies_only_in_current_account(
    neo4j_session,
):
    # Arrange: identical raw provider IDs under two accounts must not merge.
    _sync(neo4j_session)
    _sync(neo4j_session, account=OTHER_ACCOUNT)

    # Act: app-one disappears; app-two loses its only policy.
    _sync(neo4j_session, applications=[APPLICATIONS[1]], policies={}, tag=2)

    # Assert
    assert check_nodes(neo4j_session, "CloudflareAccessApplication", ["id"]) == {
        (f"{ACCOUNT}/app-two",),
        (f"{OTHER_ACCOUNT}/app-one",),
        (f"{OTHER_ACCOUNT}/app-two",),
    }
    assert check_nodes(neo4j_session, "CloudflareAccessPolicy", ["id"]) == {
        (f"{OTHER_ACCOUNT}/app-one/shared-policy",),
        (f"{OTHER_ACCOUNT}/app-one/bypass-policy",),
        (f"{OTHER_ACCOUNT}/app-two/shared-policy",),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareAccessPolicy",
        "id",
        "HAS_POLICY",
    ) == {
        (f"{OTHER_ACCOUNT}/app-one", f"{OTHER_ACCOUNT}/app-one/shared-policy"),
        (f"{OTHER_ACCOUNT}/app-one", f"{OTHER_ACCOUNT}/app-one/bypass-policy"),
        (f"{OTHER_ACCOUNT}/app-two", f"{OTHER_ACCOUNT}/app-two/shared-policy"),
    }


def test_successfully_empty_inventory_cleans_the_account(neo4j_session):
    # Arrange
    _sync(neo4j_session)

    # Act
    _sync(neo4j_session, applications=[], policies={}, tag=2)

    # Assert
    assert check_nodes(neo4j_session, "CloudflareAccessApplication", ["id"]) == set()
    assert check_nodes(neo4j_session, "CloudflareAccessPolicy", ["id"]) == set()


@pytest.mark.parametrize("page", [1, 2])
@pytest.mark.parametrize("status", [403, 500])
def test_failed_or_partial_fetch_preserves_previous_graph(neo4j_session, page, status):
    # Arrange: a failure after earlier successful pages must not change the graph.
    _sync(neo4j_session)
    calls = []
    failed_path = f"/accounts/{ACCOUNT}/access/apps"

    # Act: any provider failure skips this account's Access writes and cleanup.
    _sync(
        neo4j_session,
        tag=2,
        failed_path=failed_path,
        failed_page=page,
        status=status,
        calls=calls,
    )

    # Assert: the requested failure page was reached, including later pages.
    assert (failed_path, page) in calls
    assert check_nodes(
        neo4j_session, "CloudflareAccessApplication", ["id", "lastupdated"]
    ) == {
        (f"{ACCOUNT}/app-one", 1),
        (f"{ACCOUNT}/app-two", 1),
    }
    assert check_nodes(
        neo4j_session, "CloudflareAccessPolicy", ["id", "lastupdated"]
    ) == {
        (f"{ACCOUNT}/app-one/shared-policy", 1),
        (f"{ACCOUNT}/app-one/bypass-policy", 1),
        (f"{ACCOUNT}/app-two/shared-policy", 1),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareAccessPolicy",
        "id",
        "HAS_POLICY",
    ) == {
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/shared-policy"),
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/app-one/bypass-policy"),
        (f"{ACCOUNT}/app-two", f"{ACCOUNT}/app-two/shared-policy"),
    }


def _seed_dns(session, account=ACCOUNT):
    for zone in DNS_ZONES:
        zone_id = f"{account}/{zone['id']}"
        load_zones(session, [{**zone, "id": zone_id}], account, 1)
        records = [
            {**record, "id": f"{account}/{record['id']}"}
            for record in DNS_RECORDS
            if record["zone_id"] == zone["id"]
        ]
        load_dnsrecords(session, records, account, zone_id, 1)


@pytest.mark.parametrize(
    "domain,expected_records,expected_zones",
    [
        ("DASHBOARD.Example.Com./admin", {"dashboard"}, {"zone"}),
        ("*.example.com", {"dashboard", "ipv6", "alias"}, {"zone"}),
        ("a.child.example.com", {"child"}, {"child-zone"}),
    ],
)
def test_dns_links_use_known_proxied_records_and_same_account_zones(
    neo4j_session, domain, expected_records, expected_zones
):
    # Arrange: the same hostnames exist in both accounts.
    _seed_dns(neo4j_session)
    _seed_dns(neo4j_session, OTHER_ACCOUNT)
    apps = [{"id": "app", "type": "self_hosted", "domain": domain}]

    # Act
    _sync(neo4j_session, applications=apps, policies={})

    # Assert
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareDNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {(f"{ACCOUNT}/app", f"{ACCOUNT}/{record}") for record in expected_records}
    assert check_rels(
        neo4j_session,
        "CloudflareZone",
        "id",
        "CloudflareAccessApplication",
        "id",
        "HAS_APPLICATION",
    ) == {(f"{ACCOUNT}/{zone}", f"{ACCOUNT}/app") for zone in expected_zones}
    # check_nodes builds a set and cannot hash list-valued properties.
    assert neo4j_session.run(
        "MATCH (a:CloudflareAccessApplication) RETURN a.public_domains AS domains"
    ).single()["domains"] == [domain]


def test_dns_links_cover_multiple_public_destinations_only(neo4j_session):
    # Arrange
    _seed_dns(neo4j_session)
    apps = [
        {
            "id": "app",
            "type": "self_hosted",
            "domain": "dashboard.example.com",
            "destinations": [
                {"type": "public", "uri": "a.child.example.com/admin"},
                {"type": "public", "uri": "a.example.net/*"},
                {"type": "private", "hostname": "dashboard.example.com"},
            ],
        }
    ]

    # Act
    _sync(neo4j_session, applications=apps, policies={})

    # Assert
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareDNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {
        (f"{ACCOUNT}/app", f"{ACCOUNT}/child"),
        (f"{ACCOUNT}/app", f"{ACCOUNT}/net"),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareZone",
        "id",
        "CloudflareAccessApplication",
        "id",
        "HAS_APPLICATION",
    ) == {
        (f"{ACCOUNT}/child-zone", f"{ACCOUNT}/app"),
        (f"{ACCOUNT}/net-zone", f"{ACCOUNT}/app"),
    }


def test_dns_edges_are_replaced_and_removed_without_touching_other_accounts(
    neo4j_session,
):
    # Arrange
    _seed_dns(neo4j_session)
    _seed_dns(neo4j_session, OTHER_ACCOUNT)
    apps = [{"id": "app", "type": "self_hosted", "domain": "dashboard.example.com"}]
    _sync(neo4j_session, applications=apps, policies={})
    _sync(neo4j_session, applications=apps, policies={}, account=OTHER_ACCOUNT)

    # Act: move the application to a different domain and zone.
    moved = [{**apps[0], "domain": "a.example.net/admin"}]
    _sync(neo4j_session, applications=moved, policies={}, tag=2)

    # Assert
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareDNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {
        (f"{ACCOUNT}/app", f"{ACCOUNT}/net"),
        (f"{OTHER_ACCOUNT}/app", f"{OTHER_ACCOUNT}/dashboard"),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareZone",
        "id",
        "CloudflareAccessApplication",
        "id",
        "HAS_APPLICATION",
    ) == {
        (f"{ACCOUNT}/net-zone", f"{ACCOUNT}/app"),
        (f"{OTHER_ACCOUNT}/zone", f"{OTHER_ACCOUNT}/app"),
    }

    # Arrange: the application becomes private-only, without disappearing.
    private = [
        {**moved[0], "destinations": [{"type": "private", "hostname": "a.example.net"}]}
    ]

    # Act
    _sync(neo4j_session, applications=private, policies={}, tag=3)

    # Assert
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareDNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {
        (f"{OTHER_ACCOUNT}/app", f"{OTHER_ACCOUNT}/dashboard"),
    }
    assert check_rels(
        neo4j_session,
        "CloudflareZone",
        "id",
        "CloudflareAccessApplication",
        "id",
        "HAS_APPLICATION",
    ) == {
        (f"{OTHER_ACCOUNT}/zone", f"{OTHER_ACCOUNT}/app"),
    }


def test_dns_only_change_and_failed_access_fetch_preserve_correct_edges(neo4j_session):
    # Arrange
    _seed_dns(neo4j_session)
    _sync(neo4j_session)

    # Act: fail on a later application page before any graph write.
    _sync(
        neo4j_session,
        tag=2,
        failed_path=f"/accounts/{ACCOUNT}/access/apps",
        failed_page=2,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "CloudflareAccessApplication",
        "id",
        "CloudflareDNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {
        (f"{ACCOUNT}/app-one", f"{ACCOUNT}/dashboard"),
    }

    # Arrange: the DNS record becomes DNS-only, but the application stays configured.
    load_dnsrecords(
        neo4j_session,
        [
            {
                "id": f"{ACCOUNT}/dashboard",
                "name": "dashboard.example.com",
                "type": "A",
                "proxied": False,
            }
        ],
        ACCOUNT,
        f"{ACCOUNT}/zone",
        2,
    )

    # Act
    _sync(
        neo4j_session,
        tag=3,
        dns_records=[record for record in DNS_RECORDS if record["id"] != "dashboard"],
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "CloudflareAccessApplication",
            "id",
            "CloudflareDNSRecord",
            "id",
            "MATCHES_HOSTNAME",
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "CloudflareZone",
        "id",
        "CloudflareAccessApplication",
        "id",
        "HAS_APPLICATION",
    ) == {
        (f"{ACCOUNT}/zone", f"{ACCOUNT}/app-one"),
    }
