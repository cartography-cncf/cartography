"""
Integration tests for the Netlify network and data-collection resources: DNS zones, DNS records,
TLS certificates and forms.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.certificates
import cartography.intel.netlify.dns
import cartography.intel.netlify.forms
import cartography.intel.netlify.sites
import tests.data.netlify.dns
import tests.data.netlify.misc
import tests.data.netlify.sites
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import find_secret_in_graph
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_SLUG
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_ZONE_SITE = "7c7c7d7053c60b4be4c87001"
_ZONE_ORPHAN = "7c7c7d7053c60b4be4c87002"
_SITES = tests.data.netlify.sites.NETLIFY_SITES


def _arrange(neo4j_session: neo4j.Session) -> None:
    create_test_netlify_account(neo4j_session)
    cartography.intel.netlify.sites.load_netlify_sites(
        neo4j_session,
        cartography.intel.netlify.sites.transform_netlify_sites(_SITES),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.netlify.dns,
    "get_netlify_dns_records",
    side_effect=lambda _s, _u, zone_id: [
        r
        for r in tests.data.netlify.dns.NETLIFY_DNS_RECORDS
        if r["dns_zone_id"] == zone_id
    ],
)
@patch.object(
    cartography.intel.netlify.dns,
    "get_netlify_dns_zones",
    return_value=tests.data.netlify.dns.NETLIFY_DNS_ZONES,
)
def test_sync_netlify_dns(
    mock_zones,
    mock_records,
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.dns.sync_netlify_dns(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        TEST_ACCOUNT_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes
    assert check_nodes(
        neo4j_session,
        "NetlifyDNSZone",
        ["id", "name", "dedicated", "ipv6_enabled"],
    ) == {
        (_ZONE_SITE, "example-site.dev", False, True),
        (_ZONE_ORPHAN, "orphan.example", False, False),
    }

    # Assert Nodes: the domain registration object was flattened onto the zone that carries one,
    # and the zone whose apex domain is registered elsewhere keeps its plain `domain` string
    assert check_nodes(
        neo4j_session,
        "NetlifyDNSZone",
        [
            "id",
            "domain",
            "domain_expires_at",
            "domain_auto_renew",
            "domain_registration_status",
        ],
    ) == {
        (
            _ZONE_SITE,
            "example-site.dev",
            "2027-07-30T16:18:52.098Z",
            True,
            "payment_succeeded",
        ),
        (_ZONE_ORPHAN, "orphan.example", None, None, None),
    }

    # Netlify reports delegation problems on the zone, which is the dangling-delegation signal
    assert neo4j_session.run(
        "MATCH (z:NetlifyDNSZone{id: $id}) RETURN z.errors AS errors",
        id=_ZONE_ORPHAN,
    ).single()["errors"] == [
        "NS records for orphan.example do not point to Netlify DNS",
    ]

    # Assert Nodes: `hostname` was copied to `name` for the ontology mapping
    assert check_nodes(
        neo4j_session,
        "NetlifyDNSRecord",
        ["id", "name", "type", "value", "managed"],
    ) == {
        (
            "8d8d7d7053c60b4be4c87101",
            "example-site.dev",
            "NETLIFY",
            "example-site.netlify.app",
            True,
        ),
        (
            "8d8d7d7053c60b4be4c87102",
            "blog.example-site.dev",
            "CNAME",
            "some-tenant.example-saas.com",
            False,
        ),
        ("8d8d7d7053c60b4be4c87103", "orphan.example", "CAA", "letsencrypt.org", False),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifyDNSZone",
        "id",
        "NetlifyDNSRecord",
        "id",
        "HAS_DNS_RECORD",
    ) == {
        (_ZONE_SITE, "8d8d7d7053c60b4be4c87101"),
        (_ZONE_SITE, "8d8d7d7053c60b4be4c87102"),
        (_ZONE_ORPHAN, "8d8d7d7053c60b4be4c87103"),
    }
    # Only the zone attached to a site gets the site edge
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDNSZone",
        "id",
        "HAS_DNS_ZONE",
    ) == {(TEST_SITE_ID, _ZONE_SITE)}

    # Assert the ontology labels and their projected properties
    assert check_nodes(
        neo4j_session,
        "DNSZone",
        ["id", "_ont_name", "_ont_public", "_ont_source"],
    ) == {
        (_ZONE_SITE, "example-site.dev", True, "netlify"),
        (_ZONE_ORPHAN, "orphan.example", True, "netlify"),
    }
    assert check_nodes(
        neo4j_session,
        "DNSRecord",
        ["_ont_name", "_ont_type", "_ont_value"],
    ) == {
        ("example-site.dev", "NETLIFY", "example-site.netlify.app"),
        ("blog.example-site.dev", "CNAME", "some-tenant.example-saas.com"),
        ("orphan.example", "CAA", "letsencrypt.org"),
    }


def test_dns_zones_are_scoped_to_the_requested_team() -> None:
    """
    `GET /dns_zones` returns every zone the token can see. Without the `account_slug` filter a
    token with access to several teams would pull another team's zones into this team's cleanup
    scope and then delete them.
    """
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.links = {}
    response.json.return_value = []
    api_session.get.return_value = response

    cartography.intel.netlify.dns.get_netlify_dns_zones(
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_SLUG,
    )

    _, kwargs = api_session.get.call_args
    assert kwargs["params"]["account_slug"] == TEST_ACCOUNT_SLUG


def test_transform_netlify_dns_zones_flattens_a_registered_domain() -> None:
    """
    A domain bought through Netlify comes back with the whole domain registration object on
    `domain`, where the spec documents a string, and Neo4j rejects a map as a property value.
    """
    transformed = cartography.intel.netlify.dns.transform_netlify_dns_zones(
        tests.data.netlify.dns.NETLIFY_DNS_ZONES,
    )
    by_id = {zone["id"]: zone for zone in transformed}

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


def test_netlify_dns_zone_never_stores_the_domain_auth_code(
    neo4j_session: neo4j.Session,
) -> None:
    """
    `auth_code` on the domain registration is the EPP transfer authorization code: whoever holds
    it can move the domain to another registrar, so it must never reach the graph.
    """
    create_test_netlify_account(neo4j_session)
    cartography.intel.netlify.dns.load_netlify_dns_zones(
        neo4j_session,
        cartography.intel.netlify.dns.transform_netlify_dns_zones(
            tests.data.netlify.dns.NETLIFY_DNS_ZONES,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert find_secret_in_graph(neo4j_session, "super-secret-epp-transfer-code") == []


@patch.object(
    cartography.intel.netlify.certificates,
    "get_netlify_certificate",
    return_value=tests.data.netlify.misc.NETLIFY_CERTIFICATE,
)
def test_sync_netlify_certificates(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.certificates.sync_netlify_certificates(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: Netlify returns the certificate with no identifier of any kind, and the id
    # deliberately excludes expires_at so a renewal updates the node instead of replacing it.
    assert check_nodes(
        neo4j_session,
        "NetlifyCertificate",
        ["id", "domain", "state", "expires_at"],
    ) == {
        (
            f"{TEST_SITE_ID}_ssl",
            "example-site.dev",
            "issued",
            "2026-10-28T16:19:23.884Z",
        ),
    }

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyCertificate",
        "id",
        "HAS_CERTIFICATE",
    ) == {(TEST_SITE_ID, f"{TEST_SITE_ID}_ssl")}

    # Assert the ontology label and its projected properties
    assert check_nodes(
        neo4j_session,
        "Certificate",
        ["_ont_domain", "_ont_expiry", "_ont_source"],
    ) == {("example-site.dev", "2026-10-28T16:19:23.884Z", "netlify")}


def test_certificate_endpoint_returning_null_yields_no_node() -> None:
    """
    A site with no custom domain answers the TLS endpoint with a JSON `null` body rather than a
    404. Treating that as a certificate would create a node with a null domain.
    """
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.json.return_value = None
    api_session.get.return_value = response

    assert (
        cartography.intel.netlify.certificates.get_netlify_certificate(
            api_session,
            TEST_BASE_URL,
            TEST_SITE_ID,
        )
        is None
    )


@patch.object(
    cartography.intel.netlify.forms,
    "get_netlify_forms",
    return_value=tests.data.netlify.misc.NETLIFY_FORMS,
)
def test_sync_netlify_forms(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    _arrange(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.forms.sync_netlify_forms(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        _SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: the field descriptors were reduced to their names, which say what kind of
    # data the form collects without ingesting any of it.
    assert check_nodes(
        neo4j_session,
        "NetlifyForm",
        ["id", "name", "submission_count"],
    ) == {("afaf7d7053c60b4be4c87301", "contact", 12)}
    assert sorted(
        neo4j_session.run(
            "MATCH (f:NetlifyForm) RETURN f.field_names AS names",
        ).single()["names"],
    ) == ["email", "name"]

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyForm",
        "id",
        "HAS_FORM",
    ) == {(TEST_SITE_ID, "afaf7d7053c60b4be4c87301")}
