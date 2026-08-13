from unittest.mock import patch

import cartography.intel.snowflake.image_repositories
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.image_repositories import SNOWFLAKE_DONUT_IMAGE_DIGEST
from tests.data.snowflake.image_repositories import SNOWFLAKE_IMAGE_REPOSITORIES
from tests.data.snowflake.image_repositories import SNOWFLAKE_IMAGES_BY_REPOSITORY
from tests.data.snowflake.image_repositories import SNOWFLAKE_MONORAIL_IMAGE_DIGEST
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    KWIK_E_MART_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_IMAGES_ID = (
    "SPRINGFIELD.NUCLEAR/image_repository/SPRINGFIELD.NUCLEAR_PLANT.PLANT_IMAGES"
)
SQUISHEE_IMAGES_ID = (
    "SPRINGFIELD.NUCLEAR/image_repository/SPRINGFIELD.KWIK_E_MART.SQUISHEE_IMAGES"
)
MONORAIL_IMAGE_ID = (
    "SPRINGFIELD.NUCLEAR/image/SPRINGFIELD.NUCLEAR_PLANT.PLANT_IMAGES."
    f'"monorail-telemetry"@{SNOWFLAKE_MONORAIL_IMAGE_DIGEST}'
)
DONUT_IMAGE_ID = (
    "SPRINGFIELD.NUCLEAR/image/SPRINGFIELD.NUCLEAR_PLANT.PLANT_IMAGES."
    f'"donut-forecaster"@{SNOWFLAKE_DONUT_IMAGE_DIGEST}'
)
# The same image bytes promoted into a second repository: same digest, different node.
PROMOTED_MONORAIL_IMAGE_ID = (
    "SPRINGFIELD.NUCLEAR/image/SPRINGFIELD.KWIK_E_MART.SQUISHEE_IMAGES."
    f'"monorail-telemetry"@{SNOWFLAKE_MONORAIL_IMAGE_DIGEST}'
)

# The bundles the per-schema and per-repository listings produce together.
TEST_IMAGE_REPOSITORY_BUNDLES = [
    {
        "database_name": repository["database_name"],
        "schema_name": repository["schema_name"],
        "repository": repository,
        "images": SNOWFLAKE_IMAGES_BY_REPOSITORY[repository["name"]],
    }
    for repository in SNOWFLAKE_IMAGE_REPOSITORIES
]


def _ensure_local_neo4j_has_test_images(neo4j_session) -> None:
    """Seed the images a service container's HAS_IMAGE edge resolves against."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    repositories, images = cartography.intel.snowflake.image_repositories.transform(
        TEST_IMAGE_REPOSITORY_BUNDLES, SNOWFLAKE_ACCOUNT_ID
    )
    cartography.intel.snowflake.image_repositories.load_image_repositories(
        neo4j_session,
        repositories,
        images,
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.image_repositories,
    "get",
    return_value=(TEST_IMAGE_REPOSITORY_BUNDLES, True),
)
def test_sync_snowflake_image_repositories(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.image_repositories.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeImageRepository",
        ["id", "name", "repository_url"],
    ) == {
        (
            PLANT_IMAGES_ID,
            "PLANT_IMAGES",
            "springfield-nuclear.registry.snowflakecomputing.com"
            "/springfield/nuclear_plant/plant_images",
        ),
        (
            SQUISHEE_IMAGES_ID,
            "SQUISHEE_IMAGES",
            "springfield-nuclear.registry.snowflakecomputing.com"
            "/springfield/kwik_e_mart/squishee_images",
        ),
    }
    assert check_nodes(neo4j_session, "ContainerRegistry", ["id"]) >= {
        (PLANT_IMAGES_ID,),
        (SQUISHEE_IMAGES_ID,),
    }
    # The digest is part of the image key, so repushing a tag adds a node rather than
    # overwriting which content was deployed.
    assert check_nodes(
        neo4j_session,
        "SnowflakeImage",
        ["id", "name", "digest", "size"],
    ) == {
        (
            MONORAIL_IMAGE_ID,
            "monorail-telemetry",
            SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            148000000,
        ),
        (DONUT_IMAGE_ID, "donut-forecaster", SNOWFLAKE_DONUT_IMAGE_DIGEST, 92000000),
        (
            PROMOTED_MONORAIL_IMAGE_ID,
            "monorail-telemetry",
            SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            148000000,
        ),
    }
    # The untagged path is what disambiguates the two copies of the same digest, so a
    # container resolves to the repository it actually pulled from.
    assert check_nodes(
        neo4j_session, "SnowflakeImage", ["id", "untagged_image_path"]
    ) == {
        (
            MONORAIL_IMAGE_ID,
            "/springfield/nuclear_plant/plant_images/monorail-telemetry",
        ),
        (DONUT_IMAGE_ID, "/springfield/nuclear_plant/plant_images/donut-forecaster"),
        (
            PROMOTED_MONORAIL_IMAGE_ID,
            "/springfield/kwik_e_mart/squishee_images/monorail-telemetry",
        ),
    }
    assert check_nodes(neo4j_session, "Image", ["id"]) >= {
        (MONORAIL_IMAGE_ID,),
        (DONUT_IMAGE_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeImageRepository",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (PLANT_IMAGES_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SQUISHEE_IMAGES_ID, KWIK_E_MART_SCHEMA_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeImageRepository",
        "id",
        "SnowflakeImage",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (PLANT_IMAGES_ID, MONORAIL_IMAGE_ID),
        (PLANT_IMAGES_ID, DONUT_IMAGE_ID),
        (SQUISHEE_IMAGES_ID, PROMOTED_MONORAIL_IMAGE_ID),
    }
