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
from cartography.models.okta.log_stream import OktaLogStreamSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
async def _get_okta_log_streams(okta_client: OktaClient) -> list[dict[str, Any]]:
    # Raw JSON: the SDK's Splunk settings model requires the write-only token,
    # which the API never returns, so typed parsing fails on every Splunk stream.
    return await collect_raw_paginated(okta_client, "/api/v1/logStreams")


def _transform_okta_log_streams(
    log_streams: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for log_stream in log_streams:
        settings = log_stream.get("settings") or {}
        transformed.append(
            {
                "id": log_stream["id"],
                "name": log_stream.get("name"),
                "type": log_stream.get("type"),
                "status": log_stream.get("status"),
                "created": log_stream.get("created"),
                "okta_last_updated": log_stream.get("lastUpdated"),
                "aws_account_id": settings.get("accountId"),
                "aws_region": settings.get("region"),
                "aws_event_source_name": settings.get("eventSourceName"),
                "splunk_host": settings.get("host"),
                "splunk_edition": settings.get("edition"),
            },
        )
    return transformed


def _load_okta_log_streams(
    neo4j_session: neo4j.Session,
    log_streams: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaLogStreamSchema(),
        log_streams,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_log_streams(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        OktaLogStreamSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_okta_log_streams(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Okta log streams")
    try:
        raw_log_streams = asyncio.run(_get_okta_log_streams(okta_client))
    except OktaApiError as exc:
        # Log stream listing requires okta.logStreams.read. Existing tokens often
        # lack it; skip this sub-sync so the rest of Okta ingestion still runs.
        if is_missing_scope_error(exc):
            logger.warning(
                "Unable to sync Okta log streams - api token needs "
                "okta.logStreams.read",
            )
            return
        raise
    log_streams = _transform_okta_log_streams(raw_log_streams)
    _load_okta_log_streams(neo4j_session, log_streams, common_job_parameters)
    _cleanup_okta_log_streams(neo4j_session, common_job_parameters)
    # Record that log streams were read, so consumers can tell an org with no
    # log streams apart from one whose log streams could not be synced.
    merge_module_sync_metadata(
        neo4j_session,
        group_type="OktaOrganization",
        group_id=common_job_parameters["OKTA_ORG_ID"],
        synced_type="OktaLogStream",
        update_tag=common_job_parameters["UPDATE_TAG"],
        stat_handler=stat_handler,
    )
    logger.info("Loaded %s Okta log streams", len(log_streams))
