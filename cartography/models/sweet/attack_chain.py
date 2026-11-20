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
class SweetAttackChainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sweet attack chain ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sweet attack chain was last synced.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        description="Attack chain title.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Attack chain description.",
    )
    story: PropertyRef = PropertyRef(
        "story",
        description="Markdown narrative of the attack chain, one numbered line per step.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Attack chain severity: `critical`, `high`, `medium`, or `low`.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Sweet status: `Open` or `In Progress`.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        extra_index=True,
        description="How far Sweet validated the chain, such as `fully-validated`. Null when unknown.",
    )
    impact: PropertyRef = PropertyRef(
        "impact",
        description="Impact tags for the attack chain.",
    )
    owasp: PropertyRef = PropertyRef(
        "owasp",
        description="OWASP categories that the attack chain falls under.",
    )
    cwe: PropertyRef = PropertyRef(
        "cwe",
        description="CWE identifiers for the attack chain.",
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        extra_index=True,
        description="Host of the affected endpoints, lowercased and without a trailing dot.",
    )
    endpoints: PropertyRef = PropertyRef(
        "endpoints",
        description="Affected endpoints as `METHOD path` strings.",
    )
    first_detected_at: PropertyRef = PropertyRef(
        "first_detected_at",
        description="When Sweet first detected the attack chain.",
    )
    last_detected_at: PropertyRef = PropertyRef(
        "last_detected_at",
        description="When Sweet last detected the attack chain.",
    )
    execution_name: PropertyRef = PropertyRef(
        "execution_name",
        description="Name of the Sweet execution the chain was seen in.",
    )
    campaign_name: PropertyRef = PropertyRef(
        "campaign_name",
        description="Name of the Sweet campaign that produced the chain.",
    )
    asset_id: PropertyRef = PropertyRef(
        "asset_id",
        extra_index=True,
        description="Sweet ID of the asset the chain is linked to. Null when the chain has no linked asset.",
    )


@dataclass(frozen=True)
class SweetAttackChainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SweetAttackChainToTenantRel(CartographyRelSchema):
    """Links a Sweet tenant to one of its attack chains."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetAttackChainRelProperties = SweetAttackChainRelProperties()


@dataclass(frozen=True)
class SweetAttackChainToDNSRecordRel(CartographyRelSchema):
    """Links a Sweet attack chain to every synced DNS record whose name is the chain's endpoint host."""

    target_node_label: str = "DNSRecord"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_name": PropertyRef("domain")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SweetAttackChainRelProperties = SweetAttackChainRelProperties()


@dataclass(frozen=True)
class SweetAttackChainSchema(CartographyNodeSchema):
    """An attack chain that Sweet validated against an application's endpoints, excluding resolved and closed chains."""

    label: str = "SweetAttackChain"
    properties: SweetAttackChainNodeProperties = SweetAttackChainNodeProperties()
    sub_resource_relationship: SweetAttackChainToTenantRel = (
        SweetAttackChainToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SweetAttackChainToDNSRecordRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
