import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

from grpclib.const import Status
from grpclib.exceptions import GRPCError

import cartography.intel.modal.apps
import cartography.intel.modal.environments
import cartography.intel.modal.functions
import cartography.intel.modal.images
import cartography.intel.modal.sandboxes
import cartography.intel.modal.workloads
import tests.data.modal.compute as fx
from tests.integration.cartography.intel.modal.test_environments import (
    _ensure_local_neo4j_has_test_environments,
)
from tests.integration.cartography.intel.modal.test_workspace import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ENVIRONMENT_ID = "en-C3umado26sLFrhYfZjoWjL"
TEST_ENVIRONMENT_NAME = "main"


def _params(update_tag=TEST_UPDATE_TAG):
    return {
        "UPDATE_TAG": update_tag,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "ENVIRONMENT_ID": TEST_ENVIRONMENT_ID,
        "ENVIRONMENT_NAME": TEST_ENVIRONMENT_NAME,
    }


def _seed_tenancy(neo4j_session):
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_environments(neo4j_session)


def _sync_apps(neo4j_session, apps=None, update_tag=TEST_UPDATE_TAG):
    with patch.object(
        cartography.intel.modal.apps,
        "list_apps",
        return_value=fx.MODAL_APPS if apps is None else apps,
    ):
        return asyncio.run(
            cartography.intel.modal.apps.sync(
                neo4j_session, MagicMock(), _params(update_tag)
            )
        )


def _sync_images(neo4j_session, update_tag=TEST_UPDATE_TAG):
    with patch.object(
        cartography.intel.modal.images,
        "list_image_tags",
        return_value=fx.MODAL_IMAGES,
    ):
        return asyncio.run(
            cartography.intel.modal.images.sync(
                neo4j_session, MagicMock(), _params(update_tag)
            )
        )


def _sync_functions(neo4j_session, apps, layouts=None, update_tag=TEST_UPDATE_TAG):
    table = fx.MODAL_APP_LAYOUTS if layouts is None else layouts

    async def fake_layout(_client, app_id):
        if app_id not in table:
            # Must be a real Modal API failure: only those degrade to "skip cleanup".
            raise GRPCError(Status.UNAVAILABLE, f"layout unavailable for {app_id}")
        return table[app_id]

    with patch.object(
        cartography.intel.modal.functions, "get_app_layout", side_effect=fake_layout
    ):
        return asyncio.run(
            cartography.intel.modal.functions.sync(
                neo4j_session, MagicMock(), _params(update_tag), apps
            )
        )


def _sync_sandboxes(
    neo4j_session, rows=None, complete=True, update_tag=TEST_UPDATE_TAG, apps=()
):
    """Sync sandboxes with the v1 listing mocked.

    `apps` drives the v2 fan-out; the default of no apps means only the v1 listing runs, which
    is what most of these tests exercise.
    """
    with patch.object(
        cartography.intel.modal.sandboxes,
        "list_sandboxes",
        return_value=(
            list(fx.MODAL_SANDBOXES) if rows is None else list(rows),
            complete,
        ),
    ):
        return asyncio.run(
            cartography.intel.modal.sandboxes.sync(
                neo4j_session,
                MagicMock(),
                _params(update_tag),
                None if apps is None else list(apps),
            )
        )


def _sync_workloads(neo4j_session, apps, update_tag=TEST_UPDATE_TAG):
    async def fake_tasks(_client, _env, app_id):
        return fx.MODAL_TASKS[app_id]

    with (
        patch.object(
            cartography.intel.modal.workloads,
            "list_clusters",
            return_value=fx.MODAL_CLUSTERS,
        ),
        patch.object(
            cartography.intel.modal.workloads, "list_tasks", side_effect=fake_tasks
        ),
    ):
        return asyncio.run(
            cartography.intel.modal.workloads.sync(
                neo4j_session, MagicMock(), _params(update_tag), apps
            )
        )


def test_load_modal_apps(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_apps(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "ModalApp", ["id", "name", "state"]) == {
        (fx.TEST_APP_ID, "cartography-e2e-app", "APP_STATE_DEPLOYED"),
        (fx.TEST_STOPPED_APP_ID, None, "APP_STATE_STOPPED"),
    }
    assert check_rels(
        neo4j_session,
        "ModalApp",
        "id",
        "ModalEnvironment",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (fx.TEST_APP_ID, TEST_ENVIRONMENT_ID),
        (fx.TEST_STOPPED_APP_ID, TEST_ENVIRONMENT_ID),
    }


def test_modal_app_ontology_status_and_name_coalesce(neo4j_session):
    """A stopped app must normalise to 'deleting', and an unnamed ephemeral app must fall
    back to its description for the ontology name."""
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_apps(neo4j_session)

    # Assert
    result = neo4j_session.run(
        "MATCH (a:ModalApp) RETURN a.id AS id, a._ont_name AS name, a._ont_status AS status"
    )
    by_id = {r["id"]: (r["name"], r["status"]) for r in result}
    assert by_id[fx.TEST_APP_ID] == ("cartography-e2e-app", "active")
    assert by_id[fx.TEST_STOPPED_APP_ID] == ("one-off job", "deleting")


def test_load_modal_functions_and_classes(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)

    # Act
    _sync_functions(neo4j_session, apps)

    # Assert
    # A web endpoint is reachable; whether it requires auth is unknowable from the API.
    assert check_nodes(
        neo4j_session, "ModalFunction", ["name", "exposed_internet"]
    ) == {
        ("plain_function", False),
        ("web_endpoint", True),
        ("Worker.*", False),
        ("GhostClass.run", False),
    }
    assert check_nodes(
        neo4j_session, "ModalFunction", ["name", "web_url", "is_web_endpoint"]
    ) == {
        ("plain_function", None, False),
        (
            "web_endpoint",
            "https://example--cartography-e2e-app-web-endpoint.modal.run",
            True,
        ),
        ("Worker.*", None, False),
        ("GhostClass.run", None, False),
    }
    assert check_nodes(neo4j_session, "ModalClass", ["id", "name"]) == {
        (fx.TEST_CLASS_ID, "Worker"),
    }
    # Every function points at its app with the canonical workload edge.
    assert check_rels(
        neo4j_session, "ModalFunction", "name", "ModalApp", "id", "WORKLOAD_PARENT"
    ) == {
        ("plain_function", fx.TEST_APP_ID),
        ("web_endpoint", fx.TEST_APP_ID),
        ("Worker.*", fx.TEST_APP_ID),
        ("GhostClass.run", fx.TEST_APP_ID),
    }
    # HAS_METHOD resolves from the "<Class>." name prefix, and only for a known class:
    # GhostClass.run must NOT produce an edge.
    assert check_rels(
        neo4j_session,
        "ModalClass",
        "name",
        "ModalFunction",
        "name",
        "HAS_METHOD",
    ) == {("Worker", "Worker.*")}


def test_modal_function_partial_layout_skips_cleanup(neo4j_session):
    """If one app's layout cannot be read, cleanup must be skipped so functions we merely
    failed to see are not deleted."""
    # Arrange: full sync, then a stale function exists under a known app.
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)
    _sync_functions(neo4j_session, apps)
    assert len(check_nodes(neo4j_session, "ModalFunction", ["id"])) == 4

    # Act: the second run can only read the empty app's layout, so enumeration is partial.
    partial = {fx.TEST_STOPPED_APP_ID: fx.MODAL_APP_LAYOUTS[fx.TEST_STOPPED_APP_ID]}
    _sync_functions(
        neo4j_session, apps, layouts=partial, update_tag=TEST_UPDATE_TAG + 1
    )

    # Assert: the previously-seen functions survive rather than being wiped.
    assert len(check_nodes(neo4j_session, "ModalFunction", ["id"])) == 4


def test_modal_function_cleanup_removes_deleted_when_complete(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)
    _sync_functions(neo4j_session, apps)

    # Act: a complete second run in which the app now exposes only one function.
    trimmed = {
        fx.TEST_APP_ID: {
            "functions": [fx.MODAL_APP_LAYOUTS[fx.TEST_APP_ID]["functions"][0]],
            "classes": [],
        },
        fx.TEST_STOPPED_APP_ID: {"functions": [], "classes": []},
    }
    _sync_functions(
        neo4j_session, apps, layouts=trimmed, update_tag=TEST_UPDATE_TAG + 1
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalFunction", ["name"]) == {
        ("plain_function",)
    }
    assert check_nodes(neo4j_session, "ModalClass", ["id"]) == set()


def test_load_modal_images_and_tags(neo4j_session):
    """One node per tag, so an image published under several tags keeps all of them.

    Keying the image node on the image id alone made every tag but the last vanish on load.
    """
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_images(neo4j_session)

    # Assert: the image node is deduplicated, the tag nodes are not.
    assert check_nodes(neo4j_session, "ModalImage", ["id"]) == {
        (fx.TEST_IMAGE_ID,),
        ("im-2ndNamedImageXXXXXXXX",),
    }
    assert check_nodes(neo4j_session, "ModalImageTag", ["id", "tag"]) == {
        (f"{fx.TEST_IMAGE_ID}:my-base-image:latest", "my-base-image:latest"),
        (f"{fx.TEST_IMAGE_ID}:my-base-image:v1.2.0", "my-base-image:v1.2.0"),
        ("im-2ndNamedImageXXXXXXXX:other-image:latest", "other-image:latest"),
    }
    # Both aliases point at the same image, which is the whole point of the split.
    assert check_rels(
        neo4j_session, "ModalImageTag", "tag", "ModalImage", "id", "IMAGE"
    ) == {
        ("my-base-image:latest", fx.TEST_IMAGE_ID),
        ("my-base-image:v1.2.0", fx.TEST_IMAGE_ID),
        ("other-image:latest", "im-2ndNamedImageXXXXXXXX"),
    }


def test_modal_images_carry_no_ontology_image_labels(neo4j_session):
    """Neither node claims the ontology image labels: Modal exposes no digest, so they could
    never join a registry image and would pollute the RESOLVED_IMAGE analysis.
    """
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_images(neo4j_session)

    # Assert
    for label, forbidden in (("ModalImage", "Image"), ("ModalImageTag", "ImageTag")):
        records = list(
            neo4j_session.run(f"MATCH (n:{label}) RETURN labels(n) AS labels")
        )
        assert records, f"no {label} nodes to check"
        for record in records:
            assert forbidden not in set(record["labels"])


def test_load_modal_sandboxes_and_tunnels(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)
    _sync_apps(neo4j_session)
    _sync_images(neo4j_session)

    # Act
    _sync_sandboxes(neo4j_session)

    # Assert
    # A tunnel is a forwarded port reachable from the internet; the finished sandbox has none.
    assert check_nodes(neo4j_session, "ModalSandbox", ["id", "exposed_internet"]) == {
        (fx.TEST_SANDBOX_ID, True),
        ("sb-JeuHHabrBlXBhVE3eHSTn5", True),
        ("sb-3FinishedSandboxXXXXXX", False),
    }
    assert check_nodes(
        neo4j_session, "ModalSandbox", ["id", "state", "memory_mb", "region"]
    ) == {
        (fx.TEST_SANDBOX_ID, "RUNNING", 128, "us-east-1"),
        # Multi-region sandbox: the scalar region stays null.
        ("sb-JeuHHabrBlXBhVE3eHSTn5", "PENDING", 512, None),
        ("sb-3FinishedSandboxXXXXXX", "GENERIC_STATUS_FAILURE", 128, None),
    }
    assert check_rels(
        neo4j_session, "ModalSandbox", "id", "ModalApp", "id", "WORKLOAD_PARENT"
    ) == {
        (fx.TEST_SANDBOX_ID, fx.TEST_APP_ID),
        ("sb-JeuHHabrBlXBhVE3eHSTn5", fx.TEST_APP_ID),
        ("sb-3FinishedSandboxXXXXXX", fx.TEST_APP_ID),
    }
    # HAS_IMAGE resolves only for the named image; the anonymous build image has no node.
    assert check_rels(
        neo4j_session, "ModalSandbox", "id", "ModalImage", "id", "HAS_IMAGE"
    ) == {
        (fx.TEST_SANDBOX_ID, fx.TEST_IMAGE_ID),
        ("sb-3FinishedSandboxXXXXXX", fx.TEST_IMAGE_ID),
    }
    # EXPOSE points from the entrypoint to the asset it puts at risk.
    assert check_rels(
        neo4j_session,
        "ModalSandboxTunnel",
        "id",
        "ModalSandbox",
        "id",
        "EXPOSE",
    ) == {
        (f"{fx.TEST_SANDBOX_ID}/8080", fx.TEST_SANDBOX_ID),
        ("sb-JeuHHabrBlXBhVE3eHSTn5/9000", "sb-JeuHHabrBlXBhVE3eHSTn5"),
    }


def test_modal_sandbox_tunnel_flags_cleartext_exposure(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_sandboxes(neo4j_session)

    # Assert
    assert check_nodes(
        neo4j_session,
        "ModalSandboxTunnel",
        ["container_port", "has_unencrypted_endpoint", "unencrypted_port"],
    ) == {
        (8080, False, None),
        (9000, True, 9000),
    }


def test_modal_sandbox_ontology_state_normalisation(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)

    # Act
    _sync_sandboxes(neo4j_session)

    # Assert
    result = neo4j_session.run(
        "MATCH (s:ModalSandbox) RETURN s.id AS id, s._ont_state AS state, "
        "s._ont_namespace AS namespace"
    )
    by_id = {r["id"]: (r["state"], r["namespace"]) for r in result}
    assert by_id[fx.TEST_SANDBOX_ID] == ("running", TEST_ENVIRONMENT_NAME)
    assert by_id["sb-JeuHHabrBlXBhVE3eHSTn5"] == ("pending", TEST_ENVIRONMENT_NAME)
    assert by_id["sb-3FinishedSandboxXXXXXX"] == ("error", TEST_ENVIRONMENT_NAME)


def test_modal_sandbox_incomplete_pagination_skips_cleanup(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)
    _sync_sandboxes(neo4j_session)
    assert len(check_nodes(neo4j_session, "ModalSandbox", ["id"])) == 3

    # Act: a run whose pagination did not complete returns a subset.
    _sync_sandboxes(
        neo4j_session,
        rows=[fx.MODAL_SANDBOXES[0]],
        complete=False,
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert: nothing is deleted on partial enumeration.
    assert len(check_nodes(neo4j_session, "ModalSandbox", ["id"])) == 3


def test_load_modal_tasks_and_clusters(neo4j_session):
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)

    # Act
    _sync_workloads(neo4j_session, apps)

    # Assert
    assert check_nodes(neo4j_session, "ModalCluster", ["id", "app_id"]) == {
        (fx.TEST_CLUSTER_ID, fx.TEST_APP_ID),
    }
    assert check_nodes(neo4j_session, "ModalTask", ["id"]) == {
        ("ta-01KYQX24W4D7NW306JQ5D98X7S",),
        ("ta-01KYQX2WEK8T065MFN98455J9S",),
    }
    assert check_rels(
        neo4j_session, "ModalTask", "id", "ModalApp", "id", "WORKLOAD_PARENT"
    ) == {
        ("ta-01KYQX24W4D7NW306JQ5D98X7S", fx.TEST_APP_ID),
        ("ta-01KYQX2WEK8T065MFN98455J9S", fx.TEST_APP_ID),
    }
    # Membership is inverted from the cluster's task_ids, so only the listed task is bound.
    assert check_rels(
        neo4j_session, "ModalTask", "id", "ModalCluster", "id", "MEMBER_OF"
    ) == {("ta-01KYQX24W4D7NW306JQ5D98X7S", fx.TEST_CLUSTER_ID)}
    assert check_rels(
        neo4j_session, "ModalCluster", "id", "ModalApp", "id", "WORKLOAD_PARENT"
    ) == {(fx.TEST_CLUSTER_ID, fx.TEST_APP_ID)}


def test_modal_task_ontology_status_is_running(neo4j_session):
    """Modal only ever returns live tasks, so a task in the graph is running by
    construction."""
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)

    # Act
    _sync_workloads(neo4j_session, apps)

    # Assert
    result = neo4j_session.run(
        "MATCH (t:ModalTask) RETURN t.id AS id, t._ont_status AS status, "
        "t._ont_name AS name, t._ont_namespace AS namespace"
    )
    rows = list(result)
    assert rows
    for row in rows:
        assert row["status"] == "running"
        assert row["name"] == row["id"]
        assert row["namespace"] == TEST_ENVIRONMENT_NAME


def test_removed_environment_cascades_compute_cleanup(neo4j_session):
    """The cascade registry must cover the compute nodes too, not just RBAC."""
    # Arrange: a fully populated environment.
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)
    _sync_images(neo4j_session)
    _sync_functions(neo4j_session, apps)
    _sync_sandboxes(neo4j_session)
    _sync_workloads(neo4j_session, apps)
    for label in (
        "ModalApp",
        "ModalFunction",
        "ModalClass",
        "ModalImage",
        "ModalImageTag",
        "ModalSandbox",
        "ModalSandboxTunnel",
        "ModalTask",
        "ModalCluster",
    ):
        assert check_nodes(neo4j_session, label, ["id"]), f"{label} not seeded"

    # Act: the environment disappears from Modal.
    cartography.intel.modal.environments.cleanup_removed_environments(
        neo4j_session,
        TEST_WORKSPACE_ID,
        live_environment_ids=set(),
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert: every environment-scoped compute node is gone, none left orphaned.
    for label in (
        "ModalApp",
        "ModalFunction",
        "ModalClass",
        "ModalImage",
        "ModalImageTag",
        "ModalSandbox",
        "ModalSandboxTunnel",
        "ModalTask",
        "ModalCluster",
    ):
        assert (
            check_nodes(neo4j_session, label, ["id"]) == set()
        ), f"{label} survived its deleted environment"


def _sync_sandboxes_with_v2(neo4j_session, apps, v2=None, update_tag=TEST_UPDATE_TAG):
    table = fx.MODAL_V2_SANDBOXES if v2 is None else v2

    async def fake_v2(_client, app_id):
        return list(table.get(app_id, [])), True

    with (
        patch.object(
            cartography.intel.modal.sandboxes,
            "list_sandboxes",
            return_value=(list(fx.MODAL_SANDBOXES), True),
        ),
        patch.object(
            cartography.intel.modal.sandboxes, "list_sandboxes_v2", side_effect=fake_v2
        ),
    ):
        return asyncio.run(
            cartography.intel.modal.sandboxes.sync(
                neo4j_session, MagicMock(), _params(update_tag), apps
            )
        )


def test_v2_sandboxes_are_ingested_too(neo4j_session):
    """Modal's ordinary listing omits v2 sandboxes, so they come from a second per-app RPC.

    Without it, a workspace using v2 sandboxes would have those workloads and their tunnels
    missing from the graph entirely.
    """
    # Arrange
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)

    # Act
    _sync_sandboxes_with_v2(neo4j_session, apps)

    # Assert: both generations present, each labelled with its own.
    assert check_nodes(neo4j_session, "ModalSandbox", ["id", "sandbox_version"]) == {
        (fx.TEST_SANDBOX_ID, "v1"),
        ("sb-JeuHHabrBlXBhVE3eHSTn5", "v1"),
        ("sb-3FinishedSandboxXXXXXX", "v1"),
        (fx.TEST_V2_SANDBOX_ID, "v2"),
    }
    # The v2 sandbox joins the workload chain like any other.
    assert (fx.TEST_V2_SANDBOX_ID, fx.TEST_APP_ID) in check_rels(
        neo4j_session, "ModalSandbox", "id", "ModalApp", "id", "WORKLOAD_PARENT"
    )


def test_missing_app_list_still_ingests_v1_sandboxes(neo4j_session):
    """v2 needs the app list, v1 does not. A failed app listing must not cost us the v1
    sandboxes, but it must skip cleanup since v2 could not be enumerated."""
    # Arrange: a full run first, so there is something a wrongly-run cleanup could delete.
    _seed_tenancy(neo4j_session)
    apps = _sync_apps(neo4j_session)
    _sync_sandboxes_with_v2(neo4j_session, apps)
    before = check_nodes(neo4j_session, "ModalSandbox", ["id"])
    assert len(before) == 4

    # Act: the app list is unavailable, so only the v1 listing can run.
    _sync_sandboxes(neo4j_session, apps=None, update_tag=TEST_UPDATE_TAG + 1)

    # Assert: v1 sandboxes refreshed, and the v2 one preserved rather than cleaned up.
    assert check_nodes(neo4j_session, "ModalSandbox", ["id"]) == before
