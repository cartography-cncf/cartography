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
class CloudflareAccessPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Policy attachment ID: <account_id>/<application_id>/<policy_id>.",
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id",
        description="Original Cloudflare policy ID; reusable policies may appear on multiple applications.",
    )
    application_id: PropertyRef = PropertyRef(
        "application_id",
        description="Account-qualified application ID for this policy attachment.",
    )
    name: PropertyRef = PropertyRef("name", description="Human-readable policy name.")
    decision: PropertyRef = PropertyRef(
        "decision",
        description="Configured decision: allow, deny, non_identity, or bypass; not an effective-access verdict.",
    )
    precedence: PropertyRef = PropertyRef(
        "precedence", description="Policy evaluation order within this application."
    )
    include: PropertyRef = PropertyRef(
        "include",
        description="JSON-encoded Include rule blocks, evaluated with OR semantics; null when omitted.",
    )
    require: PropertyRef = PropertyRef(
        "require",
        description="JSON-encoded Require rule blocks, evaluated with AND semantics; null when omitted.",
    )
    exclude: PropertyRef = PropertyRef(
        "exclude",
        description="JSON-encoded Exclude rule blocks, evaluated with NOT semantics; null when omitted.",
    )
    session_duration: PropertyRef = PropertyRef(
        "session_duration", description="Session duration configured on the policy."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the policy was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the policy was last modified."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessPolicyToAccountRel(CartographyRelSchema):
    """The account owns the Access resource."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareAccessPolicyToAccountRelProperties = (
        CloudflareAccessPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareAccessPolicyToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccessPolicyToApplicationRel(CartographyRelSchema):
    """The application uses this policy attachment."""

    target_node_label: str = "CloudflareAccessApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_POLICY"
    properties: CloudflareAccessPolicyToApplicationRelProperties = (
        CloudflareAccessPolicyToApplicationRelProperties()
    )


@dataclass(frozen=True)
class CloudflareAccessPolicySchema(CartographyNodeSchema):
    """
    A policy as attached to one Access application. Reusable policies retain their
    Cloudflare policy_id but have separate attachment nodes so application-specific
    precedence and cleanup never overwrite another application's policy data.
    Rule blocks are preserved as JSON strings because Neo4j node properties cannot
    store nested maps. These nodes inventory configuration, not effective access.
    """

    label: str = "CloudflareAccessPolicy"
    properties: CloudflareAccessPolicyNodeProperties = (
        CloudflareAccessPolicyNodeProperties()
    )
    sub_resource_relationship: CloudflareAccessPolicyToAccountRel = (
        CloudflareAccessPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareAccessPolicyToApplicationRel(),
        ]
    )
