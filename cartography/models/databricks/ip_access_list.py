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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class DatabricksIpAccessListNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the IP access list."
    )
    list_id: PropertyRef = PropertyRef(
        "list_id",
        extra_index=True,
        description="Databricks IP access list identifier.",
    )
    label: PropertyRef = PropertyRef(
        "label", extra_index=True, description="Display label of the IP access list."
    )
    list_type: PropertyRef = PropertyRef(
        "list_type",
        description="Access list type, such as allowlist or blocklist.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the IP access list is enforced."
    )
    address_count: PropertyRef = PropertyRef(
        "address_count",
        description="Number of IP addresses and CIDR ranges in the list.",
    )
    ip_addresses: PropertyRef = PropertyRef(
        "ip_addresses", description="IP addresses and CIDR ranges in the list."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the IP access list was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the IP access list was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksIpAccessListToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksIpAccessList)
class DatabricksIpAccessListToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the IP access list as a resource."""

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
    """A Databricks workspace control that allows or blocks network addresses."""

    label: str = "DatabricksIpAccessList"
    properties: DatabricksIpAccessListNodeProperties = (
        DatabricksIpAccessListNodeProperties()
    )
    # NetworkAccessControl: ontology label for cross-provider network access
    # control queries (mapping in models/ontology/mapping/data/firewalls.py).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    sub_resource_relationship: DatabricksIpAccessListToWorkspaceRel = (
        DatabricksIpAccessListToWorkspaceRel()
    )
