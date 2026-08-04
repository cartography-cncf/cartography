"""Snowflake listings.

A listing is what makes a share discoverable. There is no REST endpoint, so listings
come from ``SHOW LISTINGS``. Because a published listing with EXTERNAL distribution
puts the share behind it on the public Snowflake Marketplace, the state and
distribution of every listing are recorded verbatim.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import share_key
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.listing import SnowflakeListingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every listing owned by the account, or None when not permitted."""
    try:
        return client.run_sql("SHOW LISTINGS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable("listings", "SHOW LISTINGS is not permitted")
        return None


def transform(
    listings: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape listing rows into nodes, resolving the share each one publishes."""
    transformed: list[dict[str, Any]] = []

    for listing in listings:
        global_name = listing["global_name"]
        share_name = to_text(listing.get("share_name"))
        transformed.append(
            {
                "id": sf_id(account_id, "listing", sf_fqn(global_name)),
                "global_name": global_name,
                "name": listing["name"],
                "title": to_text(listing.get("title")),
                "state": to_text(listing.get("state")),
                "review_state": to_text(listing.get("review_state")),
                "distribution": to_text(listing.get("distribution")),
                "is_monetized": to_bool(listing.get("is_monetized")),
                "is_application": to_bool(listing.get("is_application")),
                "is_targeted": to_bool(listing.get("is_targeted")),
                "is_limited_trial": to_bool(listing.get("is_limited_trial")),
                "share_name": share_name,
                # A listing only ever publishes a share this account owns, so this
                # account is the provider the share is keyed under. Null for an
                # application listing that publishes no share, which suppresses the
                # edge instead of pointing it at a nonexistent node.
                "share_id": (
                    sf_id(account_id, "share", share_key(account_id, share_name))
                    if share_name
                    else None
                ),
                "owner": to_text(listing.get("owner")),
                "comment": to_text(listing.get("comment")),
                "published_on": iso_to_datetime(listing.get("published_on")),
                "created_on": iso_to_datetime(listing.get("created_on")),
            },
        )

    return transformed


def load_listings(
    neo4j_session: neo4j.Session,
    listings: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeListingSchema(),
        listings,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeListingSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync listings.

    Runs after shares so every publishing edge resolves on the first pass.

    Returns whether the listing could be read. When it could not, the caller skips
    listing cleanup so previously collected listings are not deleted.
    """
    listings = get(client)
    if listings is None:
        return False

    transformed = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake listings for account %s.",
        len(transformed),
        client.account_id,
    )
    load_listings(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
