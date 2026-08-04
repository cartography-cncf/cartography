"""Snowflake share nodes.

A share is how data leaves a Snowflake account. An outbound share names a set of
objects and a set of consumer accounts, and those consumers then read the live
data with no copy and no further approval, so an outbound share is a standing data
egress path. An inbound share is the mirror image: data this account consumes from
someone else.

Shares have no REST endpoint. The listing comes from ``SHOW SHARES``, the objects
it exposes from ``SHOW GRANTS TO SHARE``, and the consumer accounts from
``SHOW GRANTS OF SHARE``.

A share is both a grantee (objects are granted *to* a share) and a grantable object
(privileges can be granted on a share), so it carries both shared grant labels.
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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_PRINCIPAL
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeShareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the share."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The share name."
    )
    owner_account: PropertyRef = PropertyRef(
        "owner_account",
        extra_index=True,
        description=(
            "Account that owns the share. For an INBOUND share this is the provider "
            "the data arrives from, which is what distinguishes two shares that "
            "happen to carry the same name."
        ),
    )
    share_kind: PropertyRef = PropertyRef(
        "share_kind",
        description=(
            "OUTBOUND when this account publishes the share, INBOUND when it consumes "
            "one. An OUTBOUND share is a data egress path out of the account."
        ),
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        description="Database the share exposes, or the local database created from an inbound share.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the share."
    )
    comment: PropertyRef = PropertyRef("comment", description="Share comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the share was created."
    )
    listing_global_name: PropertyRef = PropertyRef(
        "listing_global_name",
        description=(
            "Global name of the Marketplace or Data Exchange listing that publishes "
            "this share, if any."
        ),
    )
    shared_with_accounts: PropertyRef = PropertyRef(
        "shared_with_accounts",
        description=(
            "Every account the share is shared with, as Snowflake reports them. Kept "
            "verbatim because a consumer outside this organization has no node in the "
            "graph and would otherwise be invisible."
        ),
    )
    shared_with_account_count: PropertyRef = PropertyRef(
        "shared_with_account_count",
        description="Number of accounts the share is shared with.",
    )


@dataclass(frozen=True)
class SnowflakeShareToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeShare)
class SnowflakeShareToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the share as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeShareToAccountRelProperties = (
        SnowflakeShareToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeShareToSecurableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeShare)-[:SHARES]->(:SnowflakeSecurable)
class SnowflakeShareToSecurableRel(CartographyRelSchema):
    """A Snowflake share exposes this object to every account the share is shared with."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("shared_object_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARES"
    properties: SnowflakeShareToSecurableRelProperties = (
        SnowflakeShareToSecurableRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeShareToManagedAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeShare)-[:SHARED_WITH]->(:SnowflakeManagedAccount)
class SnowflakeShareToManagedAccountRel(CartographyRelSchema):
    """A Snowflake share is readable by this managed consumer account."""

    target_node_label: str = "SnowflakeManagedAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("shared_with_account_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARED_WITH"
    properties: SnowflakeShareToManagedAccountRelProperties = (
        SnowflakeShareToManagedAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeShareSchema(CartographyNodeSchema):
    """Represents a Snowflake share: a live, copy-free data feed between accounts."""

    label: str = "SnowflakeShare"
    properties: SnowflakeShareNodeProperties = SnowflakeShareNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SNOWFLAKE_PRINCIPAL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeShareToAccountRel = SnowflakeShareToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeShareToSecurableRel(),
            SnowflakeShareToManagedAccountRel(),
        ],
    )
