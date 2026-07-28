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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class SupabaseSecretNodeProperties(CartographyNodeProperties):
    # Synthesised as "<project ref>/<name>": secret names are only unique within
    # a project.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    updated_at: PropertyRef = PropertyRef("updated_at")
    # The `value` returned by GET /v1/projects/{ref}/secrets is deliberately
    # dropped in transform and never written to the graph.


@dataclass(frozen=True)
class SupabaseSecretToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseSecret)
class SupabaseSecretToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseSecretToProjectRelProperties = (
        SupabaseSecretToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseSecretSchema(CartographyNodeSchema):
    label: str = "SupabaseSecret"
    properties: SupabaseSecretNodeProperties = SupabaseSecretNodeProperties()
    sub_resource_relationship: SupabaseSecretToProjectRel = SupabaseSecretToProjectRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
