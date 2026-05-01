import logging
import time
from collections.abc import Callable
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import TypeVar

import backoff
import neo4j
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient

from cartography.client.core.tx import ensure_indexes
from cartography.client.core.tx import ensure_indexes_for_matchlinks
from cartography.client.core.tx import load_graph_data
from cartography.client.core.tx import run_write_query
from cartography.graph.querybuilder import build_conditional_label_queries
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.querybuilder import build_matchlink_query
from cartography.helpers import batch
from cartography.intel.gcp.util import GCP_API_BACKOFF_BASE
from cartography.intel.gcp.util import gcp_api_backoff_handler
from cartography.intel.gcp.util import GCP_API_BACKOFF_MAX
from cartography.intel.gcp.util import gcp_api_giveup_handler
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES
from cartography.intel.gcp.util import is_retryable_gcp_http_error
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

ARTIFACT_REGISTRY_LOAD_BATCH_SIZE = 1000
DEFAULT_ARTIFACT_REGISTRY_WORKERS = 8

ItemT = TypeVar("ItemT")
ResultT = TypeVar("ResultT")


def _load_with_progress(
    neo4j_session: neo4j.Session,
    query: str,
    data: list[dict[str, Any]],
    *,
    batch_size: int,
    progress_description: str,
    **kwargs: Any,
) -> None:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0.")

    total = len(data)
    total_batches = (total + batch_size - 1) // batch_size
    cumulative = 0
    for batch_number, data_batch in enumerate(batch(data, size=batch_size), 1):
        started_at = time.monotonic()
        load_graph_data(
            neo4j_session,
            query,
            data_batch,
            batch_size=len(data_batch),
            **kwargs,
        )
        cumulative += len(data_batch)
        logger.info(
            "Loaded %s batch %d/%d: batch_size=%d elapsed=%.2fs cumulative=%d/%d.",
            progress_description,
            batch_number,
            total_batches,
            len(data_batch),
            time.monotonic() - started_at,
            cumulative,
            total,
        )


def apply_conditional_labels(
    neo4j_session: neo4j.Session,
    node_schema: CartographyNodeSchema,
    **kwargs: Any,
) -> None:
    for query in build_conditional_label_queries(node_schema):
        run_write_query(neo4j_session, query, **kwargs)


def load_nodes_without_relationships(
    neo4j_session: neo4j.Session,
    node_schema: CartographyNodeSchema,
    data: list[dict[str, Any]],
    *,
    batch_size: int,
    progress_description: str,
    apply_labels: bool = True,
    **kwargs: Any,
) -> None:
    if not data:
        return

    ensure_indexes(neo4j_session, node_schema)
    query = build_ingestion_query(node_schema, selected_relationships=set())
    _load_with_progress(
        neo4j_session,
        query,
        data,
        batch_size=batch_size,
        progress_description=progress_description,
        **kwargs,
    )
    if apply_labels:
        apply_conditional_labels(neo4j_session, node_schema, **kwargs)

    node_count = len(data)
    stat_handler.incr(f"node.{node_schema.label.lower()}.loaded", node_count)
    logger.info("Loaded %d %s nodes", node_count, node_schema.label)


def load_matchlinks_with_progress(
    neo4j_session: neo4j.Session,
    rel_schema: CartographyRelSchema,
    data: list[dict[str, Any]],
    *,
    batch_size: int,
    progress_description: str,
    **kwargs: Any,
) -> None:
    if not data:
        return

    if "_sub_resource_label" not in kwargs:
        raise ValueError(
            f"Required kwarg '_sub_resource_label' not provided for {rel_schema.rel_label}."
        )
    if "_sub_resource_id" not in kwargs:
        raise ValueError(
            f"Required kwarg '_sub_resource_id' not provided for {rel_schema.rel_label}."
        )

    ensure_indexes_for_matchlinks(neo4j_session, rel_schema)
    query = build_matchlink_query(rel_schema)
    _load_with_progress(
        neo4j_session,
        query,
        data,
        batch_size=batch_size,
        progress_description=progress_description,
        **kwargs,
    )

    rel_count = len(data)
    src_label = (rel_schema.source_node_label or "unknown").lower()
    tgt_label = rel_schema.target_node_label.lower()
    stat_handler.incr(
        f"relationship.{src_label}.{rel_schema.rel_label.lower()}.{tgt_label}.loaded",
        rel_count,
    )
    logger.info(
        "Loaded %d (%s)-[%s]->(%s) relationships",
        rel_count,
        rel_schema.source_node_label,
        rel_schema.rel_label,
        rel_schema.target_node_label,
    )


@backoff.on_exception(  # type: ignore[misc]
    backoff.expo,
    GoogleAPICallError,
    max_tries=GCP_API_MAX_RETRIES,
    giveup=lambda e: not is_retryable_gcp_http_error(e),
    on_backoff=gcp_api_backoff_handler,
    on_giveup=gcp_api_giveup_handler,
    logger=None,
    base=GCP_API_BACKOFF_BASE,
    max_value=GCP_API_BACKOFF_MAX,
)
def list_artifact_registry_resources(
    fetcher: Callable[[], Iterable[ResultT]],
) -> list[ResultT]:
    # Retries rematerialize the pager from the beginning; these list calls are read-only.
    return list(fetcher())


def fetch_artifact_registry_resources(
    *,
    items: list[ItemT],
    fetch_for_item: Callable[[ItemT], ResultT],
    resource_type: str,
    project_id: str,
    max_workers: int = DEFAULT_ARTIFACT_REGISTRY_WORKERS,
) -> list[ResultT]:
    if not items:
        return []

    worker_count = max(1, min(max_workers, len(items)))
    logger.info(
        "Fetching Artifact Registry %s for project %s across %d item(s) with max_workers=%d.",
        resource_type,
        project_id,
        len(items),
        worker_count,
    )

    if worker_count <= 1:
        return [fetch_for_item(item) for item in items]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(fetch_for_item, items))


@timeit
def get_artifact_registry_locations(
    client: ArtifactRegistryClient,
    project_id: str,
) -> list[str] | None:
    """
    Gets all available Artifact Registry locations for a project.
    """
    try:
        locations = list_artifact_registry_resources(
            lambda: client.list_locations(
                request={"name": f"projects/{project_id}"}
            ).locations
        )
        location_ids = [
            location.location_id for location in locations if location.location_id
        ]

        logger.info(
            "Found %d Artifact Registry locations for project %s.",
            len(location_ids),
            project_id,
        )
        return location_ids

    except PermissionDenied as e:
        logger.warning(
            "Missing permissions for Artifact Registry locations in project %s. "
            "Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            type(e).__name__,
        )
        return None
    except (DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get Artifact Registry locations for project %s due to auth error. "
            "Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            type(e).__name__,
        )
        return None
    except GoogleAPICallError:
        logger.error(
            "Unexpected error getting Artifact Registry locations for project %s.",
            project_id,
            exc_info=True,
        )
        raise
