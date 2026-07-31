from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class SupabaseSecurityAdvisorFindingNodeProperties(CartographyNodeProperties):
    """
    A single lint result from Supabase's own security advisor, e.g. a public table
    with row level security disabled, or a security-definer view.
    """

    # Synthesised as "<project ref>/<cache_key>": cache_key identifies the lint
    # plus the specific entity it fired on.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    level: PropertyRef = PropertyRef("level")
    # "EXTERNAL" means the affected object is reachable from outside the project.
    facing: PropertyRef = PropertyRef("facing")
    categories: PropertyRef = PropertyRef("categories")
    description: PropertyRef = PropertyRef("description")
    detail: PropertyRef = PropertyRef("detail")
    remediation: PropertyRef = PropertyRef("remediation")
    entity: PropertyRef = PropertyRef("entity")
    entity_schema: PropertyRef = PropertyRef("entity_schema")
    entity_name: PropertyRef = PropertyRef("entity_name")
    entity_type: PropertyRef = PropertyRef("entity_type")


@dataclass(frozen=True)
class SupabaseSecurityAdvisorFindingToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseSecurityAdvisorFinding)
class SupabaseSecurityAdvisorFindingToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseSecurityAdvisorFindingToProjectRelProperties = (
        SupabaseSecurityAdvisorFindingToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseSecurityAdvisorFindingToDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseSecurityAdvisorFinding)-[:AFFECTS]->(:SupabaseDatabase)
class SupabaseSecurityAdvisorFindingToDatabaseRel(CartographyRelSchema):
    target_node_label: str = "SupabaseDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SupabaseSecurityAdvisorFindingToDatabaseRelProperties = (
        SupabaseSecurityAdvisorFindingToDatabaseRelProperties()
    )


@dataclass(frozen=True)
class SupabaseSecurityAdvisorFindingSchema(CartographyNodeSchema):
    label: str = "SupabaseSecurityAdvisorFinding"
    properties: SupabaseSecurityAdvisorFindingNodeProperties = (
        SupabaseSecurityAdvisorFindingNodeProperties()
    )
    sub_resource_relationship: SupabaseSecurityAdvisorFindingToProjectRel = (
        SupabaseSecurityAdvisorFindingToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SupabaseSecurityAdvisorFindingToDatabaseRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
