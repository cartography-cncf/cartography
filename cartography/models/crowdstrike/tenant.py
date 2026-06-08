from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class CrowdstrikeTenantNodeProperties(CartographyNodeProperties):
    """
    Represents a CrowdStrike customer tenant identified by its CID. Hosts and
    Spotlight vulnerabilities reported by the API carry a `cid` field that
    points to this tenant; CrowdstrikeTenant is the cleanup scope for those
    nodes.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CrowdstrikeTenantSchema(CartographyNodeSchema):
    label: str = "CrowdstrikeTenant"
    # Mirrors the ontology pattern used by other tenant roots (KandjiTenant,
    # GoogleWorkspaceTenant, etc.): expose the shared `Tenant` label so
    # cross-module queries that match (:Tenant) discover this organizational
    # boundary.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    properties: CrowdstrikeTenantNodeProperties = CrowdstrikeTenantNodeProperties()
