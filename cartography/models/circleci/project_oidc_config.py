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
class CircleCIProjectOidcConfigNodeProperties(CartographyNodeProperties):
    # One project-level custom-claims config per project; id is the project id.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    scope: PropertyRef = PropertyRef("scope")
    audience: PropertyRef = PropertyRef("audience")
    audience_updated_at: PropertyRef = PropertyRef("audience_updated_at")
    ttl: PropertyRef = PropertyRef("ttl")
    ttl_updated_at: PropertyRef = PropertyRef("ttl_updated_at")
    org_id: PropertyRef = PropertyRef("org_id")
    project_id: PropertyRef = PropertyRef("project_id")


@dataclass(frozen=True)
class CircleCIProjectOidcConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIProjectOidcConfig)
class CircleCIProjectOidcConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIProjectOidcConfigToProjectRelProperties = (
        CircleCIProjectOidcConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIProjectOidcConfigSchema(CartographyNodeSchema):
    label: str = "CircleCIProjectOidcConfig"
    properties: CircleCIProjectOidcConfigNodeProperties = (
        CircleCIProjectOidcConfigNodeProperties()
    )
    sub_resource_relationship: CircleCIProjectOidcConfigToProjectRel = (
        CircleCIProjectOidcConfigToProjectRel()
    )
