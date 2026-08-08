from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class FlyReleaseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly release ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    version: PropertyRef = PropertyRef(
        "version", extra_index=True, description="Release version."
    )
    stable: PropertyRef = PropertyRef(
        "stable", description="Whether the release is stable."
    )
    in_progress: PropertyRef = PropertyRef(
        "in_progress", description="Whether the release is in progress."
    )
    reason: PropertyRef = PropertyRef(
        "reason", description="Release reason, such as deploy or secrets."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Release description."
    )
    status: PropertyRef = PropertyRef("status", description="Release status.")
    deployment_strategy: PropertyRef = PropertyRef(
        "deployment_strategy", description="Deployment strategy used for the release."
    )
    evaluation_id: PropertyRef = PropertyRef(
        "evaluation_id", description="Fly evaluation ID, if returned."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    image_ref: PropertyRef = PropertyRef(
        "image_ref", description="Docker image reference deployed by the release."
    )
    user_id: PropertyRef = PropertyRef(
        "user_id", description="ID of the user who triggered the release, if returned."
    )
    user_name: PropertyRef = PropertyRef(
        "user_name",
        description="Name of the user who triggered the release, if returned.",
    )
    user_email: PropertyRef = PropertyRef(
        "user_email",
        description="Email of the user who triggered the release, if returned.",
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyReleaseToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyRelease)
class FlyReleaseToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyRelease` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyReleaseToAppRelProperties = FlyReleaseToAppRelProperties()


@dataclass(frozen=True)
class FlyReleaseSchema(CartographyNodeSchema):
    """Represents a Fly app release."""

    label: str = "FlyRelease"
    properties: FlyReleaseNodeProperties = FlyReleaseNodeProperties()
    sub_resource_relationship: FlyReleaseToAppRel = FlyReleaseToAppRel()
