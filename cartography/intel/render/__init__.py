import logging

import neo4j

import cartography.intel.render.blueprints
import cartography.intel.render.customdomains
import cartography.intel.render.dedicatedips
import cartography.intel.render.disks
import cartography.intel.render.envgroups
import cartography.intel.render.environments
import cartography.intel.render.envvars
import cartography.intel.render.headerrules
import cartography.intel.render.ipallowrules
import cartography.intel.render.keyvalue
import cartography.intel.render.logstream
import cartography.intel.render.postgres
import cartography.intel.render.projects
import cartography.intel.render.registrycredentials
import cartography.intel.render.routes
import cartography.intel.render.secretfiles
import cartography.intel.render.services
import cartography.intel.render.snapshots
import cartography.intel.render.tenants
import cartography.intel.render.workspacemembers
from cartography.config import Config
from cartography.intel.render.util import build_session
from cartography.intel.render.util import safe_sync
from cartography.intel.render.util import SKIPPED_SYNC
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Render resource classification, used by every safe_sync() call below:
#
# CORE resources (tenants, projects, environments, services, postgres, keyvalue,
# disks) are the main inventory shape - if fetching one fails, the whole workspace
# sync fails loudly rather than silently proceeding on an incomplete inventory.
# They're called directly, not through safe_sync(), so their exceptions always
# propagate.
#
# ENRICHMENT resources (everything else) add detail around that core inventory. If one
# fails, the rest of the module keeps going: safe_sync(required=False) logs a warning
# and skips that resource type (including its cleanup) for this run. See
# cartography/intel/render/util.py:safe_sync for exactly what's caught.


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
    # workspace-scoped resource below is synced once per workspace. tenants is core:
    # a broken `GET /v1/owners` means we don't even know what to sync.
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

        # Enrichment, no dependency on any other resource type in this workspace, so
        # these run first. registrycredentials runs ahead of services so a fresh
        # sync's first run can resolve RenderService's USES_CREDENTIAL edge
        # immediately rather than one cycle later (low-stakes either way - the edge is
        # a best-effort match).
        safe_sync(
            "registry credentials",
            cartography.intel.render.registrycredentials.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        safe_sync(
            "workspace members",
            cartography.intel.render.workspacemembers.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        safe_sync(
            "log stream",
            cartography.intel.render.logstream.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )

        # Core resources: called directly, not through safe_sync(), so a failure here
        # always propagates and fails this workspace's sync loudly.
        project_ids = cartography.intel.render.projects.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
        )
        environments = cartography.intel.render.environments.sync(
            neo4j_session,
            session,
            owner_id,
            project_ids,
            config.update_tag,
            scoped_job_parameters,
        )
        # run_cleanup=False: custom domains/secret files/env vars/header rules/routes
        # are fetched per-service-id below, so this resource's cleanup is deferred
        # until after those enrichment fetches have had a chance to run - see
        # services.sync()'s run_cleanup docs.
        service_ids, services = cartography.intel.render.services.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
            run_cleanup=False,
        )
        postgres_instances = cartography.intel.render.postgres.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
        )
        key_value_instances = cartography.intel.render.keyvalue.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
        )
        # run_cleanup=False: snapshots are fetched per-disk-id below, so this
        # resource's cleanup is deferred the same way services' is - see
        # disks.sync()'s run_cleanup docs.
        disk_ids = cartography.intel.render.disks.sync(
            neo4j_session,
            session,
            owner_id,
            config.update_tag,
            scoped_job_parameters,
            run_cleanup=False,
        )

        # Enrichment. Optionally scoped to environments, so this must run after
        # environments are loaded.
        safe_sync(
            "dedicated IPs",
            cartography.intel.render.dedicatedips.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )

        # Enrichment: disk children. Needs disks' returned disk ids to know which
        # disks to fetch snapshots for. Runs its own cleanup immediately - it has no
        # children of its own needing this resource's nodes to still exist.
        snapshots_result = safe_sync(
            "disk snapshots",
            cartography.intel.render.snapshots.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            disk_ids=disk_ids,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )

        # Enrichment: service children. Each needs services/service_ids, so must run
        # after services are loaded. Each runs its own cleanup immediately.
        custom_domains_result = safe_sync(
            "custom domains",
            cartography.intel.render.customdomains.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            services=services,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        secret_files_result = safe_sync(
            "secret files",
            cartography.intel.render.secretfiles.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            service_ids=service_ids,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        env_vars_result = safe_sync(
            "env vars",
            cartography.intel.render.envvars.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            service_ids=service_ids,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        header_rules_result = safe_sync(
            "header rules",
            cartography.intel.render.headerrules.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            services=services,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        routes_result = safe_sync(
            "routes",
            cartography.intel.render.routes.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            services=services,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )

        # Enrichment, needs services already loaded in the graph.
        safe_sync(
            "env groups",
            cartography.intel.render.envgroups.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        # Enrichment. Its 4-way conditional match resolves against
        # services/postgres/keyvalue/envgroups, so this must run after all of those
        # are loaded.
        safe_sync(
            "blueprints",
            cartography.intel.render.blueprints.sync,
            False,
            neo4j_session=neo4j_session,
            session=session,
            owner_id=owner_id,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )
        # Enrichment. Reads ipAllowList off the raw objects already fetched above;
        # makes no network calls of its own, so it must run after
        # environments/services/postgres/keyvalue so their GOVERNS targets already
        # exist.
        safe_sync(
            "IP allow rules",
            cartography.intel.render.ipallowrules.sync,
            False,
            neo4j_session=neo4j_session,
            owner_id=owner_id,
            environments=environments,
            services=services,
            postgres_instances=postgres_instances,
            key_value_instances=key_value_instances,
            update_tag=config.update_tag,
            common_job_parameters=scoped_job_parameters,
        )

        # Core cleanup was deferred until after children that are fetched through
        # these parent API objects had a chance to sync. If that child inventory was
        # incomplete, keep the parent nodes too; otherwise the next run might be
        # unable to fetch enough child data to cleanly reconcile the graph.
        if snapshots_result is not SKIPPED_SYNC:
            cartography.intel.render.disks.cleanup(neo4j_session, scoped_job_parameters)
        else:
            logger.warning(
                "Skipping Render disk cleanup for workspace %s because disk snapshot "
                "sync did not complete this run.",
                owner_id,
            )

        service_child_results = [
            custom_domains_result,
            secret_files_result,
            env_vars_result,
            header_rules_result,
            routes_result,
        ]
        if all(result is not SKIPPED_SYNC for result in service_child_results):
            cartography.intel.render.services.cleanup(
                neo4j_session,
                scoped_job_parameters,
            )
        else:
            logger.warning(
                "Skipping Render service cleanup for workspace %s because at least one "
                "service-dependent enrichment sync did not complete this run.",
                owner_id,
            )
