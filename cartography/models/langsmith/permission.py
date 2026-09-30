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
class LangSmithPermissionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Permission string, for example organization:manage or deployments:read.",
    )
    name: PropertyRef = PropertyRef("name", description="Permission string.")
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of what the permission allows.",
    )
    access_scope: PropertyRef = PropertyRef(
        "access_scope",
        description="Whether the permission applies at organization or workspace scope.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithPermissionToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithPermission)
class LangSmithPermissionToOrganizationRel(CartographyRelSchema):
    """Links an organization to a permission available within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithPermissionToOrganizationRelProperties = (
        LangSmithPermissionToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithPermissionSchema(CartographyNodeSchema):
    """A single LangSmith permission string that roles may grant."""

    label: str = "LangSmithPermission"
    properties: LangSmithPermissionNodeProperties = LangSmithPermissionNodeProperties()
    sub_resource_relationship: LangSmithPermissionToOrganizationRel = (
        LangSmithPermissionToOrganizationRel()
    )
