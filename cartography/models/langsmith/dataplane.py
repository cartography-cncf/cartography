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
class LangSmithDataPlaneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Data plane UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Data plane name."
    )
    status: PropertyRef = PropertyRef("status", description="Data plane status.")
    url: PropertyRef = PropertyRef("url", description="URL of the data plane.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the data plane was registered."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithDataPlaneToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithDataPlane)
class LangSmithDataPlaneToOrganizationRel(CartographyRelSchema):
    """Links an organization to a data plane registered to it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithDataPlaneToOrganizationRelProperties = (
        LangSmithDataPlaneToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithDataPlaneSchema(CartographyNodeSchema):
    """A self-hosted or bring-your-own-cloud data plane serving LangSmith workspaces."""

    label: str = "LangSmithDataPlane"
    properties: LangSmithDataPlaneNodeProperties = LangSmithDataPlaneNodeProperties()
    sub_resource_relationship: LangSmithDataPlaneToOrganizationRel = (
        LangSmithDataPlaneToOrganizationRel()
    )
