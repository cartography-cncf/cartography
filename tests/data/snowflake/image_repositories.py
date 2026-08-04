"""Raw Snowflake image repository and image payloads.

``SNOWFLAKE_IMAGE_REPOSITORIES`` is shaped as the per-schema listing returns it and
``SNOWFLAKE_IMAGES_BY_REPOSITORY`` as the per-repository image listing returns it.
"""

from typing import Any

# The digest a running service container reports, which is what ties the container to
# the concrete image it is executing.
SNOWFLAKE_MONORAIL_IMAGE_DIGEST = (
    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
)
SNOWFLAKE_DONUT_IMAGE_DIGEST = (
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
)

SNOWFLAKE_IMAGE_REPOSITORIES: list[dict[str, Any]] = [
    {
        "name": "PLANT_IMAGES",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "repository_url": (
            "springfield-nuclear.registry.snowflakecomputing.com"
            "/springfield/nuclear_plant/plant_images"
        ),
        "privatelink_repository_url": "",
        "owner": "SYSADMIN",
        "comment": "Container images for the plant services",
        "created_on": "2026-08-03T17:40:00.000+00:00",
    },
    {
        "name": "SQUISHEE_IMAGES",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "repository_url": (
            "springfield-nuclear.registry.snowflakecomputing.com"
            "/springfield/kwik_e_mart/squishee_images"
        ),
        "privatelink_repository_url": (
            "springfield-nuclear.registry.privatelink.snowflakecomputing.com"
            "/springfield/kwik_e_mart/squishee_images"
        ),
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T17:41:00.000+00:00",
    },
]

SNOWFLAKE_IMAGES_BY_REPOSITORY: dict[str, Any] = {
    "PLANT_IMAGES": [
        {
            "image_name": "monorail-telemetry",
            "tags": ["latest", "v3"],
            "digest": SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            "image_path": (
                "/springfield/nuclear_plant/plant_images/monorail-telemetry:latest"
            ),
            "size": 148000000,
            "uploaded_on": "2026-08-03T17:45:00.000+00:00",
        },
        {
            "image_name": "donut-forecaster",
            "tags": ["v1"],
            "digest": SNOWFLAKE_DONUT_IMAGE_DIGEST,
            "image_path": (
                "/springfield/nuclear_plant/plant_images/donut-forecaster:v1"
            ),
            "size": 92000000,
            "uploaded_on": "2026-08-03T17:46:00.000+00:00",
        },
    ],
    # The same image bytes promoted into a second repository, so the digest is shared
    # with PLANT_IMAGES. A container pulling from plant_images must attach only to the
    # plant_images copy, which is why HAS_IMAGE matches on the untagged path too.
    "SQUISHEE_IMAGES": [
        {
            "image_name": "monorail-telemetry",
            "tags": ["v3"],
            "digest": SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            "image_path": (
                "/springfield/kwik_e_mart/squishee_images/monorail-telemetry:v3"
            ),
            "size": 148000000,
            "uploaded_on": "2026-08-03T17:47:00.000+00:00",
        },
    ],
}
