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
class DatabricksIpAccessListNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    list_id: PropertyRef = PropertyRef("list_id", extra_index=True)
    label: PropertyRef = PropertyRef("label", extra_index=True)
    list_type: PropertyRef = PropertyRef("list_type")
    enabled: PropertyRef = PropertyRef("enabled")
    address_count: PropertyRef = PropertyRef("address_count")
    ip_addresses: PropertyRef = PropertyRef("ip_addresses")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksIpAccessListToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksIpAccessList)
class DatabricksIpAccessListToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksIpAccessListToWorkspaceRelProperties = (
        DatabricksIpAccessListToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksIpAccessListSchema(CartographyNodeSchema):
    label: str = "DatabricksIpAccessList"
    properties: DatabricksIpAccessListNodeProperties = (
        DatabricksIpAccessListNodeProperties()
    )
    # ponytail: NetworkAccessControl ontology label + mapping land in PR 9
    # alongside the rest of the Databricks ontology wiring; surfacing the
    # label here without the mapping would expose a NAC node with no `name`
    # field to cross-cloud queries.
    sub_resource_relationship: DatabricksIpAccessListToWorkspaceRel = (
        DatabricksIpAccessListToWorkspaceRel()
    )
