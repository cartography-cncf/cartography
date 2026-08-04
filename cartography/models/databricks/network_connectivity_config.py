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
class DatabricksNetworkConnectivityConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped identifier for the network connectivity configuration.",
    )
    network_connectivity_config_id: PropertyRef = PropertyRef(
        "network_connectivity_config_id",
        extra_index=True,
        description="Databricks network connectivity configuration identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the network connectivity configuration.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="Cloud region of the network connectivity configuration.",
    )
    # Egress default rule summary: whether Databricks-managed serverless egress
    # is enabled and the target CIDR/region list, flattened to a signal.
    default_rules_target_regions: PropertyRef = PropertyRef(
        "default_rules_target_regions",
        description="Target regions allowed by the default egress rules.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksNetworkConnectivityConfigToAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksNetworkConnectivityConfig)
class DatabricksNetworkConnectivityConfigToAccountRel(CartographyRelSchema):
    """A Databricks account contains this network connectivity configuration."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksNetworkConnectivityConfigToAccountRelProperties = (
        DatabricksNetworkConnectivityConfigToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNetworkConnectivityConfigSchema(CartographyNodeSchema):
    """A Databricks account network connectivity configuration."""

    label: str = "DatabricksNetworkConnectivityConfig"
    properties: DatabricksNetworkConnectivityConfigNodeProperties = (
        DatabricksNetworkConnectivityConfigNodeProperties()
    )
    sub_resource_relationship: DatabricksNetworkConnectivityConfigToAccountRel = (
        DatabricksNetworkConnectivityConfigToAccountRel()
    )
