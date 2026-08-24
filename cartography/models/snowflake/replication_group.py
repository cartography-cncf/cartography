"""Snowflake replication and failover group nodes.

A replication group copies a named set of objects to other Snowflake accounts on a
schedule. A failover group does the same and additionally lets a secondary account
be promoted to primary. Both are account-to-account data movement: whatever an
account can read in the target account, it can read of the replicated data, so a
group's ``allowed_accounts`` list is an authoritative data egress boundary.

Failover groups are a Business Critical feature and replication groups need
Enterprise, so a Standard-edition account has neither.

The two are separate labels because promotion is a materially different capability
from one-way replication, and they share one property set because ``SHOW
REPLICATION GROUPS`` and ``SHOW FAILOVER GROUPS`` return the same columns.

``allowed_accounts`` values are organization-qualified account identifiers, which
are exactly the identifiers Cartography keys account nodes on, so the cross-account
edge resolves whenever the other account is also in the graph.
"""

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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeReplicationGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the group."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The group name."
    )
    group_type: PropertyRef = PropertyRef(
        "group_type",
        description="The group type Snowflake reports, distinguishing replication from failover.",
    )
    is_primary: PropertyRef = PropertyRef(
        "is_primary",
        description=(
            "Whether this account holds the primary copy. Only the primary is "
            "writable; a secondary is a read-only replica."
        ),
    )
    primary: PropertyRef = PropertyRef(
        "primary",
        description="Fully qualified name of the primary group, including its account.",
    )
    object_types: PropertyRef = PropertyRef(
        "object_types",
        description=(
            "Kinds of object the group replicates, such as DATABASES, SHARES, USERS "
            "or ROLES. Replicating USERS and ROLES copies the account's identities "
            "into the target account."
        ),
    )
    allowed_integration_types: PropertyRef = PropertyRef(
        "allowed_integration_types",
        description="Integration types the group is permitted to replicate.",
    )
    allowed_accounts: PropertyRef = PropertyRef(
        "allowed_accounts",
        description=(
            "Accounts permitted to hold a replica, as organization-qualified "
            "identifiers. Kept verbatim because an account outside this organization "
            "has no node in the graph."
        ),
    )
    allowed_databases: PropertyRef = PropertyRef(
        "allowed_databases", description="Databases the group replicates."
    )
    allowed_shares: PropertyRef = PropertyRef(
        "allowed_shares", description="Shares the group replicates."
    )
    replication_schedule: PropertyRef = PropertyRef(
        "replication_schedule",
        description=(
            "How often the replica is refreshed. Null means refreshes are triggered "
            "manually rather than on a schedule."
        ),
    )
    secondary_state: PropertyRef = PropertyRef(
        "secondary_state",
        description="Whether the secondary replica is started or suspended.",
    )
    next_scheduled_refresh: PropertyRef = PropertyRef(
        "next_scheduled_refresh", description="When the next refresh is due."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the group."
    )
    comment: PropertyRef = PropertyRef("comment", description="Group comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the group was created."
    )


@dataclass(frozen=True)
class SnowflakeReplicationGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeReplicationGroup)
class SnowflakeReplicationGroupToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the replication or failover group as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeReplicationGroupToAccountRelProperties = (
        SnowflakeReplicationGroupToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeReplicationGroupToTargetAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeReplicationGroup)-[:REPLICATES_TO]->(:SnowflakeAccount)
class SnowflakeReplicationGroupToTargetAccountRel(CartographyRelSchema):
    """The group is permitted to place a replica of its objects in this Snowflake account."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES_TO"
    properties: SnowflakeReplicationGroupToTargetAccountRelProperties = (
        SnowflakeReplicationGroupToTargetAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeReplicationGroupToDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeReplicationGroup)-[:REPLICATES]->(:SnowflakeDatabase)
class SnowflakeReplicationGroupToDatabaseRel(CartographyRelSchema):
    """The group copies this database's contents to every account allowed to hold a replica."""

    target_node_label: str = "SnowflakeDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("allowed_database_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES"
    properties: SnowflakeReplicationGroupToDatabaseRelProperties = (
        SnowflakeReplicationGroupToDatabaseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeReplicationGroupSchema(CartographyNodeSchema):
    """Represents a Snowflake replication group: a set of objects copied to other accounts on a schedule."""

    label: str = "SnowflakeReplicationGroup"
    properties: SnowflakeReplicationGroupNodeProperties = (
        SnowflakeReplicationGroupNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeReplicationGroupToAccountRel = (
        SnowflakeReplicationGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeReplicationGroupToTargetAccountRel(),
            SnowflakeReplicationGroupToDatabaseRel(),
        ],
    )


@dataclass(frozen=True)
class SnowflakeFailoverGroupSchema(CartographyNodeSchema):
    """Represents a Snowflake failover group: a replication group whose secondary can be promoted to primary."""

    label: str = "SnowflakeFailoverGroup"
    properties: SnowflakeReplicationGroupNodeProperties = (
        SnowflakeReplicationGroupNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeReplicationGroupToAccountRel = (
        SnowflakeReplicationGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeReplicationGroupToTargetAccountRel(),
            SnowflakeReplicationGroupToDatabaseRel(),
        ],
    )
