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
class InfisicalProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Infisical project identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Infisical project was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Display name of the Infisical project.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL-safe slug of the Infisical project.",
    )
    organization_id: PropertyRef = PropertyRef(
        "INFISICAL_ORGANIZATION_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Infisical organization that owns this project.",
    )


@dataclass(frozen=True)
class InfisicalProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Infisical last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class InfisicalProjectToOrganizationRel(CartographyRelSchema):
    """Links an Infisical organization to one of its projects."""

    target_node_label: str = "InfisicalOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "INFISICAL_ORGANIZATION_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Infisical organization.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InfisicalProjectToOrganizationRelProperties = (
        InfisicalProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class InfisicalProjectSchema(CartographyNodeSchema):
    """A project managed by Infisical."""

    label: str = "InfisicalProject"
    properties: InfisicalProjectNodeProperties = InfisicalProjectNodeProperties()
    sub_resource_relationship: InfisicalProjectToOrganizationRel = (
        InfisicalProjectToOrganizationRel()
    )
