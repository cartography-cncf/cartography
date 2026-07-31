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
from cartography.models.ontology.labels import DNS_RECORD


@dataclass(frozen=True)
class SupabaseCustomHostnameNodeProperties(CartographyNodeProperties):
    # Synthesised as "<project ref>/<hostname>".
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    # A custom hostname always fronts the project's own *.supabase.co endpoint, so
    # the record type is always CNAME.
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    ssl_status: PropertyRef = PropertyRef("ssl_status")
    verification_errors: PropertyRef = PropertyRef("verification_errors")
    custom_origin_server: PropertyRef = PropertyRef("custom_origin_server")


@dataclass(frozen=True)
class SupabaseCustomHostnameToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseCustomHostname)
class SupabaseCustomHostnameToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseCustomHostnameToProjectRelProperties = (
        SupabaseCustomHostnameToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseCustomHostnamePointsToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseCustomHostname)-[:POINTS_TO]->(:SupabaseProject)
class SupabaseCustomHostnamePointsToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO"
    properties: SupabaseCustomHostnamePointsToProjectRelProperties = (
        SupabaseCustomHostnamePointsToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseCustomHostnameSchema(CartographyNodeSchema):
    label: str = "SupabaseCustomHostname"
    properties: SupabaseCustomHostnameNodeProperties = (
        SupabaseCustomHostnameNodeProperties()
    )
    sub_resource_relationship: SupabaseCustomHostnameToProjectRel = (
        SupabaseCustomHostnameToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SupabaseCustomHostnamePointsToProjectRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DNS_RECORD])
