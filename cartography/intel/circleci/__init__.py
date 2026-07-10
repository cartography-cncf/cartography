import logging
from typing import Any
from typing import Callable

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.circleci.checkout_keys
import cartography.intel.circleci.components
import cartography.intel.circleci.context_env_vars
import cartography.intel.circleci.contexts
import cartography.intel.circleci.environments
import cartography.intel.circleci.groups
import cartography.intel.circleci.oidc
import cartography.intel.circleci.organizations
import cartography.intel.circleci.pipelines
import cartography.intel.circleci.policies
import cartography.intel.circleci.project_env_vars
import cartography.intel.circleci.projects
import cartography.intel.circleci.triggers
import cartography.intel.circleci.webhooks
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _run(label: str, fn: Callable[..., Any], *args: Any) -> Any:
    """
    Run a resource sync, isolating expected per-resource API failures. On a
    request error the resource is skipped entirely - because its load/cleanup
    never runs, previously-ingested data is preserved (no destructive
    empty-then-cleanup) - and the rest of the module continues. Returns the
    sync's result, or None if it raised, so callers can distinguish "failed"
    (None) from "empty" ([]).

    Catches RequestException (not just HTTPError): the retry adapter raises
    RetryError once 429/5xx retries are exhausted, and connection/timeout errors
    are also RequestException, not HTTPError.
    """
    try:
        return fn(*args)
    except requests.exceptions.RequestException as exc:
        logger.warning("Skipping CircleCI %s due to API error: %s", label, exc)
        return None


@timeit
def start_circleci_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of CircleCI data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.circleci_token:
        logger.info(
            "CircleCI import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Circle-Token": config.circleci_token})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.circleci_base_url,
    }

    # Organizations are the tenant; everything else is scoped under an org.
    orgs = cartography.intel.circleci.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # API v2 has no list-projects endpoint, so discover slugs from each org's
    # pipeline feed and union with any operator-configured slugs.
    project_slugs: set[str] = set(config.circleci_project_slugs or [])
    for org in orgs:
        if not org.get("slug"):
            continue
        # Isolate discovery per org: one org's pipeline-feed error must not abort
        # the whole module (configured slugs + downstream resources still run).
        try:
            project_slugs.update(
                cartography.intel.circleci.projects.discover_project_slugs(
                    api_session,
                    common_job_parameters["BASE_URL"],
                    org["slug"],
                )
            )
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Could not discover CircleCI projects for org %s: %s",
                org["slug"],
                exc,
            )

    # Projects are synced BEFORE org-scoped resources so that context ->
    # RESTRICTED_TO -> project and component -> project links can attach during
    # those syncs (the targets must already exist).
    if project_slugs:
        projects = _run(
            "projects",
            cartography.intel.circleci.projects.sync,
            neo4j_session,
            api_session,
            common_job_parameters,
            sorted(project_slugs),
        )
        # Each per-project resource below loads then cleans up within a single
        # PROJECT_ID scope, so a project's cleanup only ever deletes its own
        # stale nodes. Any future per-project resource that fans out over
        # sub-items (as triggers do over definitions) must accumulate across
        # those items and clean up once, never per-item inside this loop.
        for project in projects or []:
            project_job_parameters = {
                **common_job_parameters,
                "ORG_ID": project["organization_id"],
                "PROJECT_ID": project["id"],
            }
            slug = project["slug"]
            # Isolate per-project failures so one inaccessible/erroring project
            # does not abort the remaining projects and org-scoped resources.
            try:
                cartography.intel.circleci.project_env_vars.sync(
                    neo4j_session, api_session, project_job_parameters, slug
                )
                cartography.intel.circleci.checkout_keys.sync(
                    neo4j_session, api_session, project_job_parameters, slug
                )
                cartography.intel.circleci.webhooks.sync(
                    neo4j_session, api_session, project_job_parameters, slug
                )
                pipelines = cartography.intel.circleci.pipelines.sync(
                    neo4j_session, api_session, project_job_parameters
                )
                cartography.intel.circleci.triggers.sync(
                    neo4j_session, api_session, project_job_parameters, pipelines
                )
                cartography.intel.circleci.oidc.sync_project(
                    neo4j_session,
                    api_session,
                    project_job_parameters,
                    project["organization_id"],
                    project["id"],
                )
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Skipping remaining resources for CircleCI project %s due to API error: %s",
                    slug,
                    exc,
                )

    # Org-scoped resources. Each sync is isolated via _run so a single resource's
    # API failure neither aborts the module nor (since its load/cleanup is skipped)
    # deletes previously-ingested data. Contexts link to their restricted projects
    # here via the one-to-many RESTRICTED_TO relationship (projects ingested above).
    for org in orgs:
        org_id = org["id"]
        org_job_parameters = {**common_job_parameters, "ORG_ID": org_id}

        contexts = _run(
            f"contexts (org {org_id})",
            cartography.intel.circleci.contexts.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        # Only sync env vars if contexts were fetched: passing [] after a context
        # failure would let cleanup wipe previously-ingested env vars.
        if contexts is not None:
            _run(
                f"context env vars (org {org_id})",
                cartography.intel.circleci.context_env_vars.sync,
                neo4j_session,
                api_session,
                org_job_parameters,
                org_id,
                contexts,
            )
        _run(
            f"oidc (org {org_id})",
            cartography.intel.circleci.oidc.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        _run(
            f"groups (org {org_id})",
            cartography.intel.circleci.groups.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        _run(
            f"policies (org {org_id})",
            cartography.intel.circleci.policies.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        _run(
            f"environments (org {org_id})",
            cartography.intel.circleci.environments.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        _run(
            f"components (org {org_id})",
            cartography.intel.circleci.components.sync,
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
