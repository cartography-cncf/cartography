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
class ScalewayMailboxDomainProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    mailbox_total_count: PropertyRef = PropertyRef("mailbox_total_count")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    webmail_url: PropertyRef = PropertyRef("webmail_url")
    imap_url: PropertyRef = PropertyRef("imap_url")
    pop3_url: PropertyRef = PropertyRef("pop3_url")
    smtp_url: PropertyRef = PropertyRef("smtp_url")
    jmap_url: PropertyRef = PropertyRef("jmap_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMailboxDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMailboxDomain)
class ScalewayMailboxDomainToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMailboxDomainToProjectRelProperties = (
        ScalewayMailboxDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMailboxDomainSchema(CartographyNodeSchema):
    label: str = "ScalewayMailboxDomain"
    properties: ScalewayMailboxDomainProperties = ScalewayMailboxDomainProperties()
    sub_resource_relationship: ScalewayMailboxDomainToProjectRel = (
        ScalewayMailboxDomainToProjectRel()
    )
