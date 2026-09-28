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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeNetworkPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the network policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The network policy name."
    )
    allowed_ip_list: PropertyRef = PropertyRef(
        "allowed_ip_list",
        description=(
            "CIDR ranges permitted to connect. A list containing 0.0.0.0/0 permits "
            "the entire internet and satisfies Snowflake's policy requirement "
            "without restricting anything."
        ),
    )
    blocked_ip_list: PropertyRef = PropertyRef(
        "blocked_ip_list",
        description="CIDR ranges denied even when they appear in the allowed list.",
    )
    allows_all_ipv4: PropertyRef = PropertyRef(
        "allows_all_ipv4",
        description=(
            "Whether the allowed list contains 0.0.0.0/0, meaning the policy places "
            "no effective network restriction on IPv4 traffic."
        ),
    )
    allowed_ip_count: PropertyRef = PropertyRef(
        "allowed_ip_count", description="Number of entries in the allowed IP list."
    )
    blocked_ip_count: PropertyRef = PropertyRef(
        "blocked_ip_count", description="Number of entries in the blocked IP list."
    )
    comment: PropertyRef = PropertyRef("comment", description="Network policy comment.")
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the network policy."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the network policy was created."
    )
    attached_to_account: PropertyRef = PropertyRef(
        "attached_to_account",
        description=(
            "Whether this policy is set as the account-level network policy, which "
            "applies it to every user without their own policy."
        ),
    )


@dataclass(frozen=True)
class SnowflakeNetworkPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeNetworkPolicy)
class SnowflakeNetworkPolicyToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the network policy as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeNetworkPolicyToAccountRelProperties = (
        SnowflakeNetworkPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccountToNetworkPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:GOVERNED_BY]->(:SnowflakeNetworkPolicy)
class SnowflakeAccountToNetworkPolicyRel(CartographyRelSchema):
    """Every connection to the Snowflake account is restricted by this network policy.

    Distinct from the RESOURCE edge, which merely records that the policy is
    defined in the account. This edge means the policy is actually in force
    account-wide, which is read from the account's NETWORK_POLICY parameter.
    """

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GOVERNED_BY"
    properties: SnowflakeAccountToNetworkPolicyRelProperties = (
        SnowflakeAccountToNetworkPolicyRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNetworkPolicyToAllowedRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNetworkPolicy)-[:ALLOWS]->(:SnowflakeNetworkRule)
class SnowflakeNetworkPolicyToAllowedRuleRel(CartographyRelSchema):
    """A Snowflake network policy permits the traffic described by this network rule."""

    target_node_label: str = "SnowflakeNetworkRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_network_rule_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWS"
    properties: SnowflakeNetworkPolicyToAllowedRuleRelProperties = (
        SnowflakeNetworkPolicyToAllowedRuleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNetworkPolicyToBlockedRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNetworkPolicy)-[:BLOCKS]->(:SnowflakeNetworkRule)
class SnowflakeNetworkPolicyToBlockedRuleRel(CartographyRelSchema):
    """A Snowflake network policy denies the traffic described by this network rule."""

    target_node_label: str = "SnowflakeNetworkRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("blocked_network_rule_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BLOCKS"
    properties: SnowflakeNetworkPolicyToBlockedRuleRelProperties = (
        SnowflakeNetworkPolicyToBlockedRuleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNetworkPolicySchema(CartographyNodeSchema):
    """Represents a Snowflake network policy: the IP and network-rule allow/deny list gating connections."""

    label: str = "SnowflakeNetworkPolicy"
    properties: SnowflakeNetworkPolicyNodeProperties = (
        SnowflakeNetworkPolicyNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_ACCESS_CONTROL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeNetworkPolicyToAccountRel = (
        SnowflakeNetworkPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeAccountToNetworkPolicyRel(),
            SnowflakeNetworkPolicyToAllowedRuleRel(),
            SnowflakeNetworkPolicyToBlockedRuleRel(),
        ],
    )
