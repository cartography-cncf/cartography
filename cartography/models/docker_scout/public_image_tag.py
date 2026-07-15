from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DockerScoutPublicImageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique identifier for the public image tag in `name:tag` format.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the public image.")
    tag: PropertyRef = PropertyRef("tag", description="Tag of the public image.")
    alternative_tags: PropertyRef = PropertyRef(
        "alternative_tags",
        description="Alternative tags suggested by Docker Scout.",
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Size of the public image.",
    )
    flavor: PropertyRef = PropertyRef(
        "flavor",
        description="Flavor of the public image.",
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Operating system family inferred from the report.",
    )
    runtime: PropertyRef = PropertyRef(
        "runtime",
        description="Runtime version reported by Docker Scout.",
    )
    is_slim: PropertyRef = PropertyRef(
        "is_slim",
        description="Whether the public image tag is a slim variant.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class DockerScoutPublicImageTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageBuiltFromPublicImageTagRel(CartographyRelSchema):
    """Links a Docker Scout public image to its current public image tag."""

    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("built_from_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_FROM"
    properties: DockerScoutPublicImageTagRelProperties = (
        DockerScoutPublicImageTagRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties(
    CartographyRelProperties,
):
    benefits: PropertyRef = PropertyRef(
        "benefits",
        description="Recommendation benefits reported as a bullet list.",
    )
    fix_critical: PropertyRef = PropertyRef(
        "fix_critical",
        description="Number of critical vulnerabilities fixed by the update.",
    )
    fix_high: PropertyRef = PropertyRef(
        "fix_high",
        description="Number of high-severity vulnerabilities fixed by the update.",
    )
    fix_medium: PropertyRef = PropertyRef(
        "fix_medium",
        description="Number of medium-severity vulnerabilities fixed by the update.",
    )
    fix_low: PropertyRef = PropertyRef(
        "fix_low",
        description="Number of low-severity vulnerabilities fixed by the update.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageUpdateToPublicImageTagRel(CartographyRelSchema):
    """Recommends a public image tag as an update for a Docker Scout image."""

    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("recommended_for_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties = (
        DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageTagSchema(CartographyNodeSchema):
    """A current or recommended base image tag from Docker Scout."""

    label: str = "DockerScoutPublicImageTag"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageTagNodeProperties = (
        DockerScoutPublicImageTagNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutPublicImageBuiltFromPublicImageTagRel(),
            DockerScoutPublicImageUpdateToPublicImageTagRel(),
        ],
    )
