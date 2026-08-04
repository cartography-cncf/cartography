import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import get_app_layout
from cartography.intel.modal.util import MODAL_API_ERRORS
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.function import ModalFunctionSchema
from cartography.models.modal.klass import ModalClassSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    apps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ingest the functions and classes of every app in one environment.

    Enumeration fans out per app, so it can be partial: if any app's layout fails, cleanup is
    skipped for the whole environment rather than deleting live functions we simply failed to
    see this run.
    """
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw_functions: list[dict[str, Any]] = []
    raw_classes: list[dict[str, Any]] = []
    complete = True
    for app in apps:
        try:
            layout = await get_app_layout(client, app["id"])
        except MODAL_API_ERRORS as exc:
            # Only expected API failures degrade to "partial enumeration, skip cleanup".
            # A programming or protocol error must propagate rather than be laundered into a
            # partial success that silently preserves stale data.
            logger.warning(
                "Could not fetch the layout of Modal app %s: %s", app["id"], exc
            )
            complete = False
            continue
        raw_functions.extend(layout["functions"])
        raw_classes.extend(layout["classes"])

    classes = transform_classes(raw_classes, environment_name)
    load_classes(neo4j_session, classes, environment_id, update_tag)

    functions = transform(raw_functions, classes, environment_name)
    load_functions(neo4j_session, functions, environment_id, update_tag)

    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Modal function cleanup for environment %s: at least one app layout "
            "could not be read this run, so stale nodes are preserved rather than risk "
            "deleting live functions.",
            environment_name,
        )
    return functions


def transform_classes(
    raw: list[dict[str, Any]], environment_name: str
) -> list[dict[str, Any]]:
    return [{**klass, "environment_name": environment_name} for klass in raw]


def transform(
    raw: list[dict[str, Any]],
    classes: list[dict[str, Any]],
    environment_name: str,
) -> list[dict[str, Any]]:
    """Attach the owning class id to each method function.

    Modal names a class's functions "<Class>.<method>" (and "<Class>.*" for the class service
    function), so the class is resolved from that prefix. A function whose prefix matches no
    known class gets class_id=None and therefore no HAS_METHOD edge.

    The lookup is keyed by (app_id, class name), not by name alone: `classes` spans every app
    in the environment, and two apps may each define a class with the same name, which would
    otherwise link a function to the wrong app's class.
    """
    class_ids_by_app_and_name = {
        (klass["app_id"], klass["name"]): klass["id"] for klass in classes
    }
    functions = []
    for function in raw:
        class_id = None
        name = function.get("name") or ""
        if "." in name:
            class_id = class_ids_by_app_and_name.get(
                (function.get("app_id"), name.split(".", 1)[0])
            )
        functions.append(
            {
                **function,
                "class_id": class_id,
                "environment_name": environment_name,
            }
        )
    return functions


@timeit
def load_classes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalClassSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_functions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalFunctionSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalFunctionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalClassSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
