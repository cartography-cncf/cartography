import logging
from typing import Any
from typing import Callable

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.nullify.findings
import cartography.intel.nullify.repositories
import cartography.intel.nullify.teams
import cartography.intel.nullify.tenant
import cartography.intel.nullify.users
from cartography.config import Config
from cartography.intel.nullify.util import build_base_url
from cartography.intel.nullify.util import NullifyEnvelopeError
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _run(label: str, fn: Callable[..., Any], *args: Any) -> Any:
    """
    Run a resource sync, isolating expected per-resource failures. On a request error or
    a malformed response envelope the resource is skipped entirely - its load/cleanup
    never runs, so previously-ingested data is preserved (no destructive
    empty-then-cleanup) - and the rest of the module continues. Returns the sync's
    result, or None if it raised.

    Catches RequestException (not just HTTPError): the retry adapter raises RetryError
    once 429/5xx retries are exhausted, and connection/timeout errors are also
    RequestException, not HTTPError. Also catches NullifyEnvelopeError so an unexpected
    response shape skips the resource instead of deleting its nodes.
    """
    try:
        return fn(*args)
    except (requests.exceptions.RequestException, NullifyEnvelopeError) as exc:
        logger.warning("Skipping Nullify %s due to API error: %s", label, exc)
        return None


@timeit
def start_nullify_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Nullify data. Otherwise warn and exit.
    """
    if not config.nullify_tenant or not config.nullify_token:
        logger.info(
            "Nullify import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    base_url = build_base_url(config.nullify_tenant, config.nullify_base_url)

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {config.nullify_token}"})

    tenant_id = config.nullify_tenant
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
        "BASE_URL": base_url,
    }

    # The tenant is the root node; everything else hangs off it via RESOURCE.
    cartography.intel.nullify.tenant.sync(neo4j_session, tenant_id, config.update_tag)

    # Inventory first: repositories are the FOUND_IN target for findings, and users are
    # the MEMBER_OF/LEADS target for teams, so both must exist before their dependents.
    _run(
        "repositories",
        cartography.intel.nullify.repositories.sync,
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    _run(
        "users",
        cartography.intel.nullify.users.sync,
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
    _run(
        "teams",
        cartography.intel.nullify.teams.sync,
        neo4j_session,
        api_session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )

    # Findings. Each type is isolated so one failing endpoint neither aborts the module
    # nor (since its load/cleanup is skipped) deletes previously-ingested findings.
    finding_syncs = (
        ("SAST findings", cartography.intel.nullify.findings.sync_sast_findings),
        (
            "dependency findings",
            cartography.intel.nullify.findings.sync_dependency_findings,
        ),
        (
            "container findings",
            cartography.intel.nullify.findings.sync_container_findings,
        ),
        ("secret findings", cartography.intel.nullify.findings.sync_secret_findings),
        ("CSPM findings", cartography.intel.nullify.findings.sync_cspm_findings),
    )
    for label, fn in finding_syncs:
        _run(
            label,
            fn,
            neo4j_session,
            api_session,
            base_url,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )
