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
class CircleCIContextEnvVarNodeProperties(CartographyNodeProperties):
    # Synthesized stable id: "{context_id}:{variable}" (API returns no id here).
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    variable: PropertyRef = PropertyRef("variable", extra_index=True)
    context_id: PropertyRef = PropertyRef("context_id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class CircleCIContextEnvVarToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIContextEnvVar)
class CircleCIContextEnvVarToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIContextEnvVarToOrganizationRelProperties = (
        CircleCIContextEnvVarToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIContextEnvVarToContextRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIContext)-[:HAS_ENV_VAR]->(:CircleCIContextEnvVar)
class CircleCIContextEnvVarToContextRel(CartographyRelSchema):
    target_node_label: str = "CircleCIContext"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("context_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENV_VAR"
    properties: CircleCIContextEnvVarToContextRelProperties = (
        CircleCIContextEnvVarToContextRelProperties()
    )


@dataclass(frozen=True)
class CircleCIContextEnvVarSchema(CartographyNodeSchema):
    label: str = "CircleCIContextEnvVar"
    properties: CircleCIContextEnvVarNodeProperties = (
        CircleCIContextEnvVarNodeProperties()
    )
    sub_resource_relationship: CircleCIContextEnvVarToOrganizationRel = (
        CircleCIContextEnvVarToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCIContextEnvVarToContextRel()],
    )
