from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import IMAGE


@dataclass(frozen=True)
class FlyImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Same as digest.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    digest: PropertyRef = PropertyRef(
        "digest", extra_index=True, description="SHA256 digest of the image."
    )
    registry: PropertyRef = PropertyRef(
        "registry", description="Registry the image was pulled from."
    )
    repository: PropertyRef = PropertyRef(
        "repository", description="Repository within the registry."
    )
    tag: PropertyRef = PropertyRef("tag", description="Tag deployed for this image.")
    uri: PropertyRef = PropertyRef(
        "uri", description="Full pull reference: `<registry>/<repository>:<tag>`."
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyImageToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyImage)
class FlyImageToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyImage` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyImageToAppRelProperties = FlyImageToAppRelProperties()


@dataclass(frozen=True)
class FlyImageSchema(CartographyNodeSchema):
    """Represents a container image deployed by one or more Fly Machines,
    identified by its digest. Deduplicated across Machines that share a deploy."""

    label: str = "FlyImage"
    properties: FlyImageNodeProperties = FlyImageNodeProperties()
    sub_resource_relationship: FlyImageToAppRel = FlyImageToAppRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IMAGE])
