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
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<project ref>/<cache key>`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The lint identifier (e.g. `rls_disabled_in_public`)",
    )
    title: PropertyRef = PropertyRef(
        "title", description="Human-readable title of the finding"
    )
    level: PropertyRef = PropertyRef(
        "level", description="Advisor severity (`ERROR`, `WARN`, `INFO`)"
    )
    # "EXTERNAL" means the affected object is reachable from outside the project.
    facing: PropertyRef = PropertyRef(
        "facing",
        description="Exposure of the affected object. `EXTERNAL` means it is reachable from outside the project",
    )
    categories: PropertyRef = PropertyRef(
        "categories", description="Advisor categories the lint belongs to"
    )
    description: PropertyRef = PropertyRef(
        "description", description="What the lint checks"
    )
    detail: PropertyRef = PropertyRef(
        "detail", description="Details of this particular occurrence"
    )
    remediation: PropertyRef = PropertyRef(
        "remediation", description="Link to remediation guidance"
    )
    entity: PropertyRef = PropertyRef(
        "entity", description="Fully-qualified name of the affected database object"
    )
    entity_schema: PropertyRef = PropertyRef(
        "entity_schema", description="Schema of the affected object"
    )
    entity_name: PropertyRef = PropertyRef(
        "entity_name", description="Name of the affected object"
    )
    entity_type: PropertyRef = PropertyRef(
        "entity_type",
        description="Type of the affected object (table, view, function, ...)",
    )


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
    """Represents a finding from Supabase's own security advisor, for example a public table with row level security disabled, or a security-definer view."""

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
