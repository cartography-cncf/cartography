from __future__ import annotations

import asyncio
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_raw_paginated
from cartography.intel.okta.common import is_missing_scope_error
from cartography.intel.okta.common import OktaApiError
from cartography.models.okta.api_token import OktaApiTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def _get_okta_api_tokens(okta_client: OktaClient) -> list[dict[str, Any]]:
    return await collect_raw_paginated(okta_client, "/api/v1/api-tokens")


def _transform_okta_api_tokens(
    tokens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for token in tokens:
        network = token.get("network") or {}
        transformed.append(
            {
                "id": token["id"],
                "name": token.get("name"),
                "client_name": token.get("clientName"),
                "user_id": token.get("userId"),
                "token_window": token.get("tokenWindow"),
                "created": token.get("created"),
                "expires_at": token.get("expiresAt"),
                "okta_last_updated": token.get("lastUpdated"),
                "network_connection": network.get("connection"),
                "network_include_zone_ids": network.get("include") or [],
                "network_exclude_zone_ids": network.get("exclude") or [],
            },
        )
    return transformed


def _load_okta_api_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaApiTokenSchema(),
        tokens,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_api_tokens(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        OktaApiTokenSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_okta_api_tokens(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta API token metadata.

    Run after the user and network zone syncs: tokens link to the `OktaUser`
    that owns them and to the `OktaNetworkZone` nodes in their network condition.
    """
    logger.info("Syncing Okta API tokens")
    try:
        raw_tokens = asyncio.run(_get_okta_api_tokens(okta_client))
    except OktaApiError as exc:
        # Token listing requires okta.apiTokens.read. Existing tokens often lack
        # it; skip this sub-sync so the rest of Okta ingestion still runs.
        if is_missing_scope_error(exc):
            logger.warning(
                "Unable to sync Okta API tokens - api token needs okta.apiTokens.read",
            )
            return
        raise
    tokens = _transform_okta_api_tokens(raw_tokens)
    _load_okta_api_tokens(neo4j_session, tokens, common_job_parameters)
    _cleanup_okta_api_tokens(neo4j_session, common_job_parameters)
    logger.info("Loaded %s Okta API tokens", len(tokens))
