import cartography.intel.railway.storage.volumes
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    _sync_compute_tier,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import BUNDLES
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    POSTGRES_INSTANCE_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    WEB_INSTANCE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

WEB_VOLUME_ID = "f1111111-1111-1111-1111-111111111111"
POSTGRES_VOLUME_ID = "f2222222-2222-2222-2222-222222222222"
WEB_VOLUME_INSTANCE_ID = "f3333333-3333-3333-3333-333333333333"
POSTGRES_VOLUME_INSTANCE_ID = "f4444444-4444-4444-4444-444444444444"


def _sync_volumes(neo4j_session):
    _sync_compute_tier(neo4j_session)
    cartography.intel.railway.storage.volumes.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )


def test_load_railway_volumes(neo4j_session):
    # Act
    _sync_volumes(neo4j_session)

    # Assert the project-scoped volume definitions
    assert check_nodes(neo4j_session, "RailwayVolume", ["id", "name"]) == {
        (WEB_VOLUME_ID, "web-volume"),
        (POSTGRES_VOLUME_ID, "postgres-volume"),
    }
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayVolume",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, WEB_VOLUME_ID),
        (TEST_PROJECT_ID, POSTGRES_VOLUME_ID),
    }


def test_load_railway_volume_instances(neo4j_session):
    # Act
    _sync_volumes(neo4j_session)

    # Assert the per-environment disks, including the derived size_gb the ontology needs
    assert check_nodes(
        neo4j_session,
        "RailwayVolumeInstance",
        ["id", "mount_path", "region", "size_mb", "size_gb", "state"],
    ) == {
        (
            WEB_VOLUME_INSTANCE_ID,
            "/data",
            "us-west2",
            500,
            500 / 1024,
            "READY",
        ),
        (
            POSTGRES_VOLUME_INSTANCE_ID,
            "/var/lib/postgresql/data",
            "us-west2",
            500,
            500 / 1024,
            "READY",
        ),
    }

    # Assert the volume -> instance containment
    assert check_rels(
        neo4j_session,
        "RailwayVolume",
        "id",
        "RailwayVolumeInstance",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (WEB_VOLUME_ID, WEB_VOLUME_INSTANCE_ID),
        (POSTGRES_VOLUME_ID, POSTGRES_VOLUME_INSTANCE_ID),
    }

    # Assert the MOUNTS edge from the workload that mounts the disk
    assert check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "RailwayVolumeInstance",
        "id",
        "MOUNTS",
        rel_direction_right=True,
    ) == {
        (WEB_INSTANCE_ID, WEB_VOLUME_INSTANCE_ID),
        (POSTGRES_INSTANCE_ID, POSTGRES_VOLUME_INSTANCE_ID),
    }

    # Assert the BlockStorage ontology label
    assert check_nodes(neo4j_session, "BlockStorage", ["id"]) == {
        (WEB_VOLUME_INSTANCE_ID,),
        (POSTGRES_VOLUME_INSTANCE_ID,),
    }


def test_volume_instance_size_gb_is_none_when_size_missing():
    bundle = {
        "volumes": {"edges": []},
        "environments": {
            "edges": [
                {
                    "node": {
                        "volumeInstances": {
                            "edges": [{"node": {"id": "vi-1", "sizeMB": None}}],
                        },
                    },
                },
            ],
        },
    }

    _, instances = cartography.intel.railway.storage.volumes.transform(
        {"project-1": bundle},
    )

    assert instances["project-1"][0]["size_gb"] is None
