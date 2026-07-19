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
    id: PropertyRef = PropertyRef("id", description="ID of the Mailbox domain.")
    name: PropertyRef = PropertyRef("name", description="Domain name.")
    status: PropertyRef = PropertyRef(
        "status", description="Status of the Mailbox domain."
    )
    mailbox_total_count: PropertyRef = PropertyRef(
        "mailbox_total_count", description="Number of mailboxes for the domain."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    webmail_url: PropertyRef = PropertyRef(
        "webmail_url", description="Webmail URL for the domain."
    )
    imap_url: PropertyRef = PropertyRef(
        "imap_url", description="IMAP server URL for the domain."
    )
    pop3_url: PropertyRef = PropertyRef(
        "pop3_url", description="POP3 server URL for the domain."
    )
    smtp_url: PropertyRef = PropertyRef(
        "smtp_url", description="SMTP server URL for the domain."
    )
    jmap_url: PropertyRef = PropertyRef(
        "jmap_url", description="JMAP server URL for the domain."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMailboxDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMailboxDomain)
class ScalewayMailboxDomainToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayMailboxDomain` through `RESOURCE`."""

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
    """Represents a Mailbox domain in Scaleway."""

    label: str = "ScalewayMailboxDomain"
    properties: ScalewayMailboxDomainProperties = ScalewayMailboxDomainProperties()
    sub_resource_relationship: ScalewayMailboxDomainToProjectRel = (
        ScalewayMailboxDomainToProjectRel()
    )
