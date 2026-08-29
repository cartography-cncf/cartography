from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import CONTAINER_REGISTRY
from cartography.models.ontology.labels import IMAGE
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeImageRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the image repository."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The image repository name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified DATABASE.SCHEMA.NAME of the image repository.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        description="Name of the database containing the image repository.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Name of the schema containing the image repository."
    )
    repository_url: PropertyRef = PropertyRef(
        "repository_url",
        extra_index=True,
        description="Registry URL images are pushed to and pulled from.",
    )
    privatelink_repository_url: PropertyRef = PropertyRef(
        "privatelink_repository_url",
        description="Private-endpoint registry URL, when private connectivity is configured.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the image repository."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Image repository comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the image repository was created."
    )


@dataclass(frozen=True)
class SnowflakeImageRepositoryToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeImageRepository)
class SnowflakeImageRepositoryToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the image repository as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeImageRepositoryToAccountRelProperties = (
        SnowflakeImageRepositoryToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeImageRepositoryToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeImageRepository)
class SnowflakeImageRepositoryToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the image repository."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeImageRepositoryToSchemaRelProperties = (
        SnowflakeImageRepositoryToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeImageRepositorySchema(CartographyNodeSchema):
    """Represents a Snowflake image repository: the account-hosted OCI registry that Snowpark Container Services pulls from."""

    label: str = "SnowflakeImageRepository"
    properties: SnowflakeImageRepositoryNodeProperties = (
        SnowflakeImageRepositoryNodeProperties()
    )
    # ContainerRegistry: ontology label; an image repository stores container images.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [CONTAINER_REGISTRY, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeImageRepositoryToAccountRel = (
        SnowflakeImageRepositoryToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeImageRepositoryToSchemaRel()],
    )


@dataclass(frozen=True)
class SnowflakeImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the image."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Image name within its repository."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Content digest of the image manifest, which uniquely pins its contents.",
    )
    image_path: PropertyRef = PropertyRef(
        "image_path",
        extra_index=True,
        description="Full registry path a container specification references the image by.",
    )
    untagged_image_path: PropertyRef = PropertyRef(
        "untagged_image_path",
        extra_index=True,
        description=(
            "Registry path with the tag removed. A running container is resolved to "
            "this plus the digest, so the same image bytes pushed to two repositories "
            "stay two distinct images."
        ),
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags currently pointing at this image."
    )
    size: PropertyRef = PropertyRef("size", description="Size of the image in bytes.")
    repository_name: PropertyRef = PropertyRef(
        "repository_name",
        description="Fully qualified name of the image repository holding the image.",
    )
    uploaded_on: PropertyRef = PropertyRef(
        "uploaded_on", description="When the image was pushed to the repository."
    )


@dataclass(frozen=True)
class SnowflakeImageToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeImage)
class SnowflakeImageToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the image as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeImageToAccountRelProperties = (
        SnowflakeImageToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeImageToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeImageRepository)-[:CONTAINS]->(:SnowflakeImage)
class SnowflakeImageToRepositoryRel(CartographyRelSchema):
    """A Snowflake image repository holds this image."""

    target_node_label: str = "SnowflakeImageRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_repository_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeImageToRepositoryRelProperties = (
        SnowflakeImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeImageSchema(CartographyNodeSchema):
    """Represents a container image stored in a Snowflake image repository."""

    label: str = "SnowflakeImage"
    properties: SnowflakeImageNodeProperties = SnowflakeImageNodeProperties()
    # Image: ontology label; this is a concrete container image.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IMAGE])
    sub_resource_relationship: SnowflakeImageToAccountRel = SnowflakeImageToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeImageToRepositoryRel()],
    )
