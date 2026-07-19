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
class ScalewayMailboxProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    project_id: PropertyRef = PropertyRef("project_id")
    domain_id: PropertyRef = PropertyRef("domain_id")
    email: PropertyRef = PropertyRef("email")
    status: PropertyRef = PropertyRef("status")
    subscription_period: PropertyRef = PropertyRef("subscription_period")
    subscription_period_started_at: PropertyRef = PropertyRef(
        "subscription_period_started_at"
    )
    next_subscription_period: PropertyRef = PropertyRef("next_subscription_period")
    next_subscription_period_starts_at: PropertyRef = PropertyRef(
        "next_subscription_period_starts_at"
    )
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    deletion_scheduled_at: PropertyRef = PropertyRef("deletion_scheduled_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMailboxToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMailbox)
class ScalewayMailboxToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMailboxToProjectRelProperties = (
        ScalewayMailboxToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMailboxToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayMailboxDomain)-[:RESOURCE]->(:ScalewayMailbox)
class ScalewayMailboxToDomainRel(CartographyRelSchema):
    target_node_label: str = "ScalewayMailboxDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMailboxToDomainRelProperties = (
        ScalewayMailboxToDomainRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMailboxSchema(CartographyNodeSchema):
    label: str = "ScalewayMailbox"
    properties: ScalewayMailboxProperties = ScalewayMailboxProperties()
    sub_resource_relationship: ScalewayMailboxToProjectRel = (
        ScalewayMailboxToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[ScalewayMailboxToDomainRel()],
    )
