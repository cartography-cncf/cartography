"""
Cleanup semantics for the Netlify module.

Every Netlify node is scoped to the team for cleanup, including the ones that also hang off a
site, so a site disappearing between runs has to take its children with it. These tests pin that
behaviour down, and pin down that a resource still present is never collateral damage.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.dns
import cartography.intel.netlify.functions
import cartography.intel.netlify.sites
import tests.data.netlify.dns
import tests.data.netlify.functions
import tests.data.netlify.sites
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_SLUG
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_GIT_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes

_ZONE_SITE = "7c7c7d7053c60b4be4c87001"
_ZONE_ORPHAN = "7c7c7d7053c60b4be4c87002"
_SECOND_TAG = TEST_UPDATE_TAG + 1


def _sync_sites(
    neo4j_session: neo4j.Session,
    sites: list,
    update_tag: int,
) -> None:
    cartography.intel.netlify.sites.sync_netlify_sites(
        neo4j_session,
        sites,
        TEST_ACCOUNT_ID,
        update_tag,
        common_job_parameters(update_tag=update_tag),
    )


def _sync_functions(
    neo4j_session: neo4j.Session,
    sites: list,
    bundles_by_site: dict,
    update_tag: int,
) -> None:
    with patch.object(
        cartography.intel.netlify.functions,
        "get_netlify_functions",
        side_effect=lambda _s, _u, site_id: bundles_by_site.get(site_id, []),
    ):
        cartography.intel.netlify.functions.sync_netlify_functions(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            sites,
            update_tag,
            common_job_parameters(update_tag=update_tag),
        )


def test_stale_site_and_its_children_are_removed(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange: two sites, the first with two functions
    create_test_netlify_account(neo4j_session)
    both_sites = tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT
    bundles = {TEST_SITE_ID: tests.data.netlify.functions.NETLIFY_SITE_FUNCTIONS}
    _sync_sites(neo4j_session, both_sites, TEST_UPDATE_TAG)
    _sync_functions(neo4j_session, both_sites, bundles, TEST_UPDATE_TAG)

    assert check_nodes(neo4j_session, "NetlifySite", ["id"]) == {
        (TEST_SITE_ID,),
        (TEST_GIT_SITE_ID,),
    }
    assert check_nodes(neo4j_session, "NetlifyFunction", ["id"]) == {
        (f"{TEST_SITE_ID}|None|hello",),
        (f"{TEST_SITE_ID}|None|scheduled",),
    }

    # Act: the function-bearing site is deleted on Netlify, so it drops out of the site list and
    # its functions are no longer reported either.
    create_test_netlify_account(neo4j_session, update_tag=_SECOND_TAG)
    remaining = [s for s in both_sites if s["id"] == TEST_GIT_SITE_ID]
    _sync_sites(neo4j_session, remaining, _SECOND_TAG)
    _sync_functions(neo4j_session, remaining, {}, _SECOND_TAG)

    # Assert: the site is gone and so are its functions, which are scoped to the team rather than
    # to the site and would otherwise be orphaned.
    assert check_nodes(neo4j_session, "NetlifySite", ["id"]) == {(TEST_GIT_SITE_ID,)}
    assert check_nodes(neo4j_session, "NetlifyFunction", ["id"]) == set()


def test_stale_dns_record_is_removed_without_touching_its_zone(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    create_test_netlify_account(neo4j_session)
    all_records = tests.data.netlify.dns.NETLIFY_DNS_RECORDS

    def sync_dns(records: list, update_tag: int) -> None:
        with (
            patch.object(
                cartography.intel.netlify.dns,
                "get_netlify_dns_zones",
                return_value=tests.data.netlify.dns.NETLIFY_DNS_ZONES,
            ),
            patch.object(
                cartography.intel.netlify.dns,
                "get_netlify_dns_records",
                side_effect=lambda _s, _u, zone_id: [
                    r for r in records if r["dns_zone_id"] == zone_id
                ],
            ),
        ):
            cartography.intel.netlify.dns.sync_netlify_dns(
                neo4j_session,
                MagicMock(spec=requests.Session),
                TEST_BASE_URL,
                TEST_ACCOUNT_ID,
                TEST_ACCOUNT_SLUG,
                update_tag,
                common_job_parameters(update_tag=update_tag),
            )

    sync_dns(all_records, TEST_UPDATE_TAG)
    assert check_nodes(neo4j_session, "NetlifyDNSRecord", ["id"]) == {
        ("8d8d7d7053c60b4be4c87101",),
        ("8d8d7d7053c60b4be4c87102",),
        ("8d8d7d7053c60b4be4c87103",),
    }

    # Act: one hand-managed record is deleted, the zones are untouched
    create_test_netlify_account(neo4j_session, update_tag=_SECOND_TAG)
    kept = [r for r in all_records if r["id"] != "8d8d7d7053c60b4be4c87102"]
    sync_dns(kept, _SECOND_TAG)

    # Assert: only that record went, and cleanup running records-before-zones did not take the
    # zone with it.
    assert check_nodes(neo4j_session, "NetlifyDNSRecord", ["id"]) == {
        ("8d8d7d7053c60b4be4c87101",),
        ("8d8d7d7053c60b4be4c87103",),
    }
    assert check_nodes(neo4j_session, "NetlifyDNSZone", ["id"]) == {
        (_ZONE_SITE,),
        (_ZONE_ORPHAN,),
    }


def test_cleanup_of_one_domain_leaves_another_alone(
    neo4j_session: neo4j.Session,
) -> None:
    """
    Every scoped cleanup job matches on the same team, so a job written against the wrong schema
    would silently wipe a neighbouring resource type. Sync functions with an empty result and
    check the sites survive.
    """
    # Arrange
    create_test_netlify_account(neo4j_session)
    both_sites = tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT
    _sync_sites(neo4j_session, both_sites, TEST_UPDATE_TAG)
    _sync_functions(
        neo4j_session,
        both_sites,
        {TEST_SITE_ID: tests.data.netlify.functions.NETLIFY_SITE_FUNCTIONS},
        TEST_UPDATE_TAG,
    )

    # Act: a later run where every function was deleted but both sites are still there
    create_test_netlify_account(neo4j_session, update_tag=_SECOND_TAG)
    _sync_sites(neo4j_session, both_sites, _SECOND_TAG)
    _sync_functions(neo4j_session, both_sites, {}, _SECOND_TAG)

    # Assert
    assert check_nodes(neo4j_session, "NetlifyFunction", ["id"]) == set()
    assert check_nodes(neo4j_session, "NetlifySite", ["id"]) == {
        (TEST_SITE_ID,),
        (TEST_GIT_SITE_ID,),
    }
