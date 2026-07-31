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
from cartography.models.ontology.labels import FUNCTION


@dataclass(frozen=True)
class SupabaseEdgeFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    version: PropertyRef = PropertyRef("version")
    # False means the function is publicly invokable without a valid project JWT.
    verify_jwt: PropertyRef = PropertyRef("verify_jwt")
    import_map: PropertyRef = PropertyRef("import_map")
    entrypoint_path: PropertyRef = PropertyRef("entrypoint_path")
    import_map_path: PropertyRef = PropertyRef("import_map_path")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class SupabaseEdgeFunctionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseEdgeFunction)
class SupabaseEdgeFunctionToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseEdgeFunctionToProjectRelProperties = (
        SupabaseEdgeFunctionToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseEdgeFunctionSchema(CartographyNodeSchema):
    label: str = "SupabaseEdgeFunction"
    properties: SupabaseEdgeFunctionNodeProperties = (
        SupabaseEdgeFunctionNodeProperties()
    )
    sub_resource_relationship: SupabaseEdgeFunctionToProjectRel = (
        SupabaseEdgeFunctionToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FUNCTION])
