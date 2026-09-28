"""Snowflake account parameter nodes.

Snowflake exposes several hundred account parameters, most of which are performance
or ergonomics knobs. Cartography records only the ones that decide a security
outcome: whether a network policy is in force, whether unloading data to arbitrary
URLs is permitted, whether stages must go through a storage integration, whether
MFA and ID tokens can be cached, and how long historical data stays recoverable.
Loading all of them would bury those few facts in noise.

The values come from ``SHOW PARAMETERS IN ACCOUNT``, which has no REST equivalent.
An empty value string means the parameter is unset and is recorded as null.
"""

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
class SnowflakeAccountParameterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the parameter."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The parameter name."
    )
    value: PropertyRef = PropertyRef(
        "value",
        description=(
            "The parameter's effective value at the account level. Null when the "
            "parameter is unset."
        ),
    )
    default_value: PropertyRef = PropertyRef(
        "default_value",
        description="The value Snowflake applies when the parameter is not set.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description=(
            "Whether the effective value still equals Snowflake's default, meaning "
            "nobody has deliberately set it."
        ),
    )
    level: PropertyRef = PropertyRef(
        "level",
        description=(
            "The object level the value was set at. An empty level means the value "
            "was never set anywhere and the default applies."
        ),
    )
    parameter_type: PropertyRef = PropertyRef(
        "parameter_type",
        description="The parameter's data type, such as BOOLEAN, NUMBER or STRING.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Snowflake's own description of the parameter."
    )


@dataclass(frozen=True)
class SnowflakeAccountParameterToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeAccountParameter)
class SnowflakeAccountParameterToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the parameter as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeAccountParameterToAccountRelProperties = (
        SnowflakeAccountParameterToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccountParameterSchema(CartographyNodeSchema):
    """Represents a security-relevant Snowflake account parameter and its effective value."""

    label: str = "SnowflakeAccountParameter"
    properties: SnowflakeAccountParameterNodeProperties = (
        SnowflakeAccountParameterNodeProperties()
    )
    sub_resource_relationship: SnowflakeAccountParameterToAccountRel = (
        SnowflakeAccountParameterToAccountRel()
    )
