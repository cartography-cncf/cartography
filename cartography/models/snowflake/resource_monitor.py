from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeResourceMonitorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the resource monitor."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The resource monitor name."
    )
    credit_quota: PropertyRef = PropertyRef(
        "credit_quota",
        description="Credits the monitored objects may consume per interval before actions fire.",
    )
    used_credits: PropertyRef = PropertyRef(
        "used_credits", description="Credits consumed so far in the current interval."
    )
    remaining_credits: PropertyRef = PropertyRef(
        "remaining_credits",
        description="Credits left in the current interval before the quota is reached.",
    )
    level: PropertyRef = PropertyRef(
        "level",
        description=(
            "Scope the monitor applies to: ACCOUNT for an account-wide cap, WAREHOUSE "
            "when it is assigned to specific warehouses."
        ),
    )
    frequency: PropertyRef = PropertyRef(
        "frequency",
        description="How often the credit usage resets: MONTHLY, DAILY, WEEKLY, YEARLY or NEVER.",
    )
    notify_at: PropertyRef = PropertyRef(
        "notify_at",
        description="Quota percentages at which the monitor only notifies, without suspending.",
    )
    suspend_at: PropertyRef = PropertyRef(
        "suspend_at",
        description=(
            "Quota percentage at which running statements finish but no new ones start. "
            "Null means the monitor never suspends."
        ),
    )
    suspend_immediate_at: PropertyRef = PropertyRef(
        "suspend_immediate_at",
        description="Quota percentage at which running statements are aborted immediately.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the resource monitor."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Resource monitor comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the resource monitor was created."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time", description="When the current monitoring interval started."
    )
    end_time: PropertyRef = PropertyRef(
        "end_time",
        description="When monitoring ends. Null means the monitor runs indefinitely.",
    )


@dataclass(frozen=True)
class SnowflakeResourceMonitorToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeResourceMonitor)
class SnowflakeResourceMonitorToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the resource monitor as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeResourceMonitorToAccountRelProperties = (
        SnowflakeResourceMonitorToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeResourceMonitorSchema(CartographyNodeSchema):
    """Represents a Snowflake resource monitor: the credit quota that suspends warehouses when exceeded."""

    label: str = "SnowflakeResourceMonitor"
    properties: SnowflakeResourceMonitorNodeProperties = (
        SnowflakeResourceMonitorNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeResourceMonitorToAccountRel = (
        SnowflakeResourceMonitorToAccountRel()
    )
