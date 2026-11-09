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
class CloudflareAccessApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-qualified application ID: <account_id>/<application_id>.",
    )
    application_id: PropertyRef = PropertyRef(
        "application_id", description="Application ID returned by the Cloudflare API."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Human-readable application name."
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        description="Configured application domain, which may include a wildcard or path.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Application type, such as self_hosted, saas, bookmark, or infrastructure.",
    )
    session_duration: PropertyRef = PropertyRef(
        "session_duration", description="Duration of an application session."
    )
    aud: PropertyRef = PropertyRef("aud", description="Application audience tag.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the application was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the application was last modified."
    )
    public_domains: PropertyRef = PropertyRef(
        "public_domains",
        description="Public self-hosted Access destinations, including configured paths.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessApplicationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessApplicationToAccountRel(CartographyRelSchema):
    """The account owns the Access resource."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareAccessApplicationToAccountRelProperties = (
        CloudflareAccessApplicationToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareAccessApplicationToDNSRecordRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessApplicationToDNSRecordRel(CartographyRelSchema):
    """The public application hostname matches a concrete proxied DNS record.

    Read public_domains for path restrictions and HAS_POLICY for decisions.
    This edge does not evaluate bypass policies or overlapping applications.
    """

    target_node_label: str = "CloudflareDNSRecord"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("dns_record_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MATCHES_HOSTNAME"
    properties: CloudflareAccessApplicationToDNSRecordRelProperties = (
        CloudflareAccessApplicationToDNSRecordRelProperties()
    )


@dataclass(frozen=True)
class CloudflareAccessApplicationToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessApplicationToZoneRel(CartographyRelSchema):
    """A known zone in the same account hosts a configured public application domain."""

    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("zone_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APPLICATION"
    properties: CloudflareAccessApplicationToZoneRelProperties = (
        CloudflareAccessApplicationToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareAccessApplicationSchema(CartographyNodeSchema):
    """
    An Access application in a Cloudflare account. Its presence alone does not
    establish that a hostname is protected: policy decisions and application
    domain/path matching must also be considered. MATCHES_HOSTNAME records configured
    hostname matches only; no effective-access inference is performed.
    """

    label: str = "CloudflareAccessApplication"
    properties: CloudflareAccessApplicationNodeProperties = (
        CloudflareAccessApplicationNodeProperties()
    )
    sub_resource_relationship: CloudflareAccessApplicationToAccountRel = (
        CloudflareAccessApplicationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareAccessApplicationToDNSRecordRel(),
            CloudflareAccessApplicationToZoneRel(),
        ]
    )
