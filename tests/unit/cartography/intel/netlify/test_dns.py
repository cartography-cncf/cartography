from unittest.mock import MagicMock

import requests

import cartography.intel.netlify.dns
import tests.data.netlify.dns

TEST_ACCOUNT_SLUG = "example-team"
TEST_BASE_URL = "https://api.netlify.com/api/v1"
_ZONE_SITE = "7c7c7d7053c60b4be4c87001"
_ZONE_ORPHAN = "7c7c7d7053c60b4be4c87002"


def test_dns_zones_are_scoped_to_the_requested_team() -> None:
    """
    `GET /dns_zones` returns every zone the token can see. Without the `account_slug` filter a
    token with access to several teams would pull another team's zones into this team's cleanup
    scope and then delete them.
    """
    # Arrange
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.links = {}
    response.json.return_value = []
    api_session.get.return_value = response

    # Act
    cartography.intel.netlify.dns.get_netlify_dns_zones(
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_SLUG,
    )

    # Assert
    _, kwargs = api_session.get.call_args
    assert kwargs["params"]["account_slug"] == TEST_ACCOUNT_SLUG


def test_transform_netlify_dns_zones_flattens_a_registered_domain() -> None:
    """
    A domain bought through Netlify comes back with the whole domain registration object on
    `domain`, where the spec documents a string, and Neo4j rejects a map as a property value.
    """
    # Act
    transformed = cartography.intel.netlify.dns.transform_netlify_dns_zones(
        tests.data.netlify.dns.NETLIFY_DNS_ZONES,
    )
    by_id = {zone["id"]: zone for zone in transformed}

    # Assert
    registered = by_id[_ZONE_SITE]
    assert registered["domain"] == "example-site.dev"
    assert registered["domain_registered_at"] == "2025-07-30T16:18:52.098Z"
    assert registered["domain_expires_at"] == "2027-07-30T16:18:52.098Z"
    assert registered["domain_auto_renew"] is True
    assert registered["domain_registration_status"] == "payment_succeeded"
    # The registration carries its own id, name and timestamps; the zone keeps its own
    assert registered["name"] == "example-site.dev"
    assert registered["created_at"] == "2026-07-30T16:18:52.098Z"
    assert registered["updated_at"] == "2026-07-30T16:20:20.019Z"

    # A domain registered elsewhere already matches the spec, so it passes through untouched
    delegated = by_id[_ZONE_ORPHAN]
    assert delegated["domain"] == "orphan.example"
    assert delegated["domain_expires_at"] is None
    assert delegated["domain_auto_renew"] is None
    assert delegated["domain_registration_status"] is None
