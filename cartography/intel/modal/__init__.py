import asyncio
import logging
from typing import Any
from typing import Awaitable
from typing import Callable

import neo4j

import cartography.intel.modal.apps
import cartography.intel.modal.environment_roles
import cartography.intel.modal.environments
import cartography.intel.modal.functions
import cartography.intel.modal.images
import cartography.intel.modal.members
import cartography.intel.modal.proxy_tokens
import cartography.intel.modal.sandboxes
import cartography.intel.modal.service_users
import cartography.intel.modal.workloads
import cartography.intel.modal.workspace
from cartography.config import Config
from cartography.intel.modal.util import MODAL_API_ERRORS
from cartography.intel.modal.util import ModalClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_modal_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest a Modal workspace.

    Modal's client opens its own gRPC connection bound to the event loop that created it,
    so the whole module runs inside a single ``asyncio.run``, the same shape as
    ``cartography.intel.microsoft.entra``.
    """
    if not config.modal_token_id or not config.modal_token_secret:
        logger.info(
            "Modal import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    asyncio.run(_sync(neo4j_session, config))


async def _run(
    label: str,
    fn: Callable[..., Awaitable[Any]],
    *args: Any,
) -> Any:
    """Run one resource sync, isolating it from the rest of the module.

    On an API error the resource is skipped entirely. Because its load and cleanup never
    run, previously-ingested data is preserved rather than being emptied and then deleted
    by a cleanup that saw nothing. Returns None if it raised, so callers can tell "failed"
    (None) apart from "empty" ([]).
    """
    try:
        return await fn(*args)
    except MODAL_API_ERRORS as exc:
        logger.warning("Skipping Modal %s due to API error: %s", label, exc)
        return None


def _select_environments(
    environments: list[dict[str, Any]],
    allowlist: list[str] | None,
) -> list[dict[str, Any]]:
    """Narrow the per-environment fan-out to the configured allowlist.

    Every environment is still ingested as a node by the caller; only their *contents* are
    filtered here. See the ModalEnvironment sync for why loading the full list matters.
    """
    if not allowlist:
        return environments
    wanted = set(allowlist)
    selected = [env for env in environments if env["name"] in wanted]
    unknown = wanted - {env["name"] for env in environments}
    if unknown:
        logger.warning(
            "These Modal environments were requested but do not exist in the workspace: %s",
            ", ".join(sorted(unknown)),
        )
    return selected


async def _sync(neo4j_session: neo4j.Session, config: Config) -> None:
    client = await ModalClient.create(
        config.modal_token_id,
        config.modal_token_secret,
    )

    workspace = await cartography.intel.modal.workspace.sync(
        neo4j_session,
        client,
        {"UPDATE_TAG": config.update_tag},
    )
    workspace_id = workspace["id"]
    logger.info("Syncing Modal workspace %s (%s)", workspace.get("name"), workspace_id)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": workspace_id,
    }

    environments = await _run(
        "environments",
        cartography.intel.modal.environments.sync,
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Workspace-global resources. Members and service users are loaded before any
    # environment roles, because the role bindings match on those nodes.
    await _run(
        "workspace members",
        cartography.intel.modal.members.sync,
        neo4j_session,
        client,
        common_job_parameters,
    )
    await _run(
        "service users",
        cartography.intel.modal.service_users.sync,
        neo4j_session,
        client,
        common_job_parameters,
    )
    await _run(
        "proxy tokens",
        cartography.intel.modal.proxy_tokens.sync,
        neo4j_session,
        client,
        common_job_parameters,
    )

    if environments is None:
        logger.warning(
            "Skipping Modal environment-scoped resources because the environment list "
            "could not be fetched.",
        )
        return

    for environment in _select_environments(environments, config.modal_environments):
        environment_job_parameters = {
            **common_job_parameters,
            "ENVIRONMENT_ID": environment["id"],
            "ENVIRONMENT_NAME": environment["name"],
        }
        name = environment["name"]
        logger.info("Syncing Modal environment %s", name)

        await _run(
            f"environment roles ({name})",
            cartography.intel.modal.environment_roles.sync,
            neo4j_session,
            client,
            environment_job_parameters,
        )

        # Images before sandboxes, so the sandbox HAS_IMAGE edge can resolve.
        await _run(
            f"images ({name})",
            cartography.intel.modal.images.sync,
            neo4j_session,
            client,
            environment_job_parameters,
        )

        # Apps before functions, sandboxes and tasks: they are the WORKLOAD_PARENT target.
        # `_run` returns None on failure, which is distinct from an empty environment, so
        # the children are skipped rather than run against a half-loaded app set.
        apps = await _run(
            f"apps ({name})",
            cartography.intel.modal.apps.sync,
            neo4j_session,
            client,
            environment_job_parameters,
        )

        await _run(
            f"sandboxes ({name})",
            cartography.intel.modal.sandboxes.sync,
            neo4j_session,
            client,
            environment_job_parameters,
        )

        if apps is None:
            logger.warning(
                "Skipping Modal functions and tasks for environment %s because the app "
                "list could not be fetched.",
                name,
            )
            continue

        await _run(
            f"functions ({name})",
            cartography.intel.modal.functions.sync,
            neo4j_session,
            client,
            environment_job_parameters,
            apps,
        )
        await _run(
            f"tasks and clusters ({name})",
            cartography.intel.modal.workloads.sync,
            neo4j_session,
            client,
            environment_job_parameters,
            apps,
        )
