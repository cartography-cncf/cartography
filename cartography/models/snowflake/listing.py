"""Snowflake listing nodes.

A listing publishes a share through the Snowflake Marketplace or a Data Exchange.
The share decides *what* is exposed; the listing decides *who can find it*. A
listing whose ``state`` is published and whose ``distribution`` is EXTERNAL is
offered on the public Snowflake Marketplace, which makes the underlying share's
data reachable by parties nobody in the account explicitly approved. That is the
single most consequential fact on this node.

Listings have no REST endpoint, so they come from ``SHOW LISTINGS``.
"""

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
class SnowflakeListingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the listing."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The listing name within the account."
    )
    global_name: PropertyRef = PropertyRef(
        "global_name",
        extra_index=True,
        description="Snowflake's globally unique name for the listing.",
    )
    title: PropertyRef = PropertyRef(
        "title", description="The title consumers see for the listing."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description=(
            "Lifecycle state of the listing. Only a published listing is discoverable "
            "by consumers."
        ),
    )
    review_state: PropertyRef = PropertyRef(
        "review_state",
        description="Where the listing stands in Snowflake's publishing review.",
    )
    distribution: PropertyRef = PropertyRef(
        "distribution",
        description=(
            "EXTERNAL for the public Snowflake Marketplace, INTERNAL for the "
            "organization's own Data Exchange. EXTERNAL plus a published state means "
            "the share behind it is publicly offered."
        ),
    )
    is_monetized: PropertyRef = PropertyRef(
        "is_monetized", description="Whether the listing is offered for a price."
    )
    is_application: PropertyRef = PropertyRef(
        "is_application",
        description="Whether the listing publishes a Native App rather than data alone.",
    )
    is_targeted: PropertyRef = PropertyRef(
        "is_targeted",
        description=(
            "Whether the listing is offered only to named consumer accounts rather "
            "than to everyone who can see it."
        ),
    )
    is_limited_trial: PropertyRef = PropertyRef(
        "is_limited_trial",
        description="Whether the listing offers a limited trial of the data.",
    )
    share_name: PropertyRef = PropertyRef(
        "share_name", description="Name of the share the listing publishes."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the listing."
    )
    comment: PropertyRef = PropertyRef("comment", description="Listing comment.")
    published_on: PropertyRef = PropertyRef(
        "published_on",
        description="When the listing was published. Null while it is unpublished.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the listing was created."
    )


@dataclass(frozen=True)
class SnowflakeListingToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeListing)
class SnowflakeListingToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the listing as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeListingToAccountRelProperties = (
        SnowflakeListingToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeListingToShareRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeListing)-[:PUBLISHES]->(:SnowflakeShare)
class SnowflakeListingToShareRel(CartographyRelSchema):
    """A Snowflake listing offers this share to consumers."""

    target_node_label: str = "SnowflakeShare"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("share_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PUBLISHES"
    properties: SnowflakeListingToShareRelProperties = (
        SnowflakeListingToShareRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeListingSchema(CartographyNodeSchema):
    """Represents a Snowflake listing: the Marketplace or Data Exchange offer that publishes a share."""

    label: str = "SnowflakeListing"
    properties: SnowflakeListingNodeProperties = SnowflakeListingNodeProperties()
    sub_resource_relationship: SnowflakeListingToAccountRel = (
        SnowflakeListingToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeListingToShareRel()],
    )
