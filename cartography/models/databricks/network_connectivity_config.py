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
    id: PropertyRef = PropertyRef("id")
    network_connectivity_config_id: PropertyRef = PropertyRef(
        "network_connectivity_config_id", extra_index=True
    )
    name: PropertyRef = PropertyRef("name", extra_index=True)
    region: PropertyRef = PropertyRef("region")
    # Egress default rule summary: whether Databricks-managed serverless egress
    # is enabled and the target CIDR/region list, flattened to a signal.
    default_rules_target_regions: PropertyRef = PropertyRef(
        "default_rules_target_regions"
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
    label: str = "DatabricksNetworkConnectivityConfig"
    properties: DatabricksNetworkConnectivityConfigNodeProperties = (
        DatabricksNetworkConnectivityConfigNodeProperties()
    )
    sub_resource_relationship: DatabricksNetworkConnectivityConfigToAccountRel = (
        DatabricksNetworkConnectivityConfigToAccountRel()
    )
