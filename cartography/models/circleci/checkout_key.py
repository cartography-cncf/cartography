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
class CircleCICheckoutKeyNodeProperties(CartographyNodeProperties):
    # Synthesized stable id: "{project_slug}:{fingerprint}".
    id: PropertyRef = PropertyRef(
        "id", description="Synthesized CircleCI checkout key ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint", extra_index=True, description="Checkout key fingerprint."
    )
    type: PropertyRef = PropertyRef("type", description="Checkout key type.")
    preferred: PropertyRef = PropertyRef(
        "preferred", description="Whether this is the preferred checkout key."
    )
    public_key: PropertyRef = PropertyRef("public_key", description="SSH public key.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Checkout key creation timestamp."
    )
    project_slug: PropertyRef = PropertyRef(
        "project_slug", description="Slug of the owning CircleCI project."
    )


@dataclass(frozen=True)
class CircleCICheckoutKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCICheckoutKey)
class CircleCICheckoutKeyToProjectRel(CartographyRelSchema):
    """The CircleCI project contains the checkout key."""

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCICheckoutKeyToProjectRelProperties = (
        CircleCICheckoutKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCICheckoutKeySchema(CartographyNodeSchema):
    """A public checkout or deploy key for a CircleCI project."""

    label: str = "CircleCICheckoutKey"
    properties: CircleCICheckoutKeyNodeProperties = CircleCICheckoutKeyNodeProperties()
    sub_resource_relationship: CircleCICheckoutKeyToProjectRel = (
        CircleCICheckoutKeyToProjectRel()
    )
