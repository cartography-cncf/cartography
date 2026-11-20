import logging

import neo4j

import cartography.intel.render.environments
import cartography.intel.render.projects
import cartography.intel.render.services
import cartography.intel.render.tenants
from cartography.config import Config
from cartography.intel.render.util import build_session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_render_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Render data. Otherwise skip.
    """
    if not config.render_api_key:
        logger.info(
            "Render import is not configured - skipping this module. "
            "Set render_api_key to enable the Render sync stage.",
        )
        return

    session = build_session(config.render_api_key)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # A Render API key can reach every workspace its holder belongs to, so every
    # workspace-scoped resource below is synced once per workspace.
    tenants = cartography.intel.render.tenants.sync(
        neo4j_session,
        session,
        config.update_tag,
        common_job_parameters,
    )
    if not tenants:
        logger.warning("Render API key has access to no workspaces - nothing to sync.")
        return

    for tenant in tenants:
        owner_id = tenant["id"]
        logger.info("Syncing Render workspace %s", owner_id)
        scoped_job_parameters = {**common_job_parameters, "OWNER_ID": owner_id}

        # Cleanup for RenderProject/RenderEnvironment is deferred until every
        # descendant has finished loading (run bottom-up below), so a transient
        # failure partway through this tenant's descendant fetches doesn't leave a
        # still-valid descendant pointing at a project/environment that cleanup
        # already deleted this run - see projects.py/environments.py's sync()
        # docstrings.
        project_ids = cartography.intel.render.projects.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
            run_cleanup=False,
        )

        cartography.intel.render.environments.sync(
            neo4j_session,
            session,
            owner_id,
            project_ids,
            config.update_tag,
            scoped_job_parameters,
            run_cleanup=False,
        )

        cartography.intel.render.services.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
        )

        cartography.intel.render.environments.cleanup(
            neo4j_session,
            scoped_job_parameters,
        )
        cartography.intel.render.projects.cleanup(
            neo4j_session,
            scoped_job_parameters,
        )
