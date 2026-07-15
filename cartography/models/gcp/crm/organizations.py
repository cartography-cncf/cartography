from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GCPOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description='The name of the GCP Organization, e.g. "organizations/1234".'
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    orgname: PropertyRef = PropertyRef(
        "name", description="Name assigned to this resource."
    )
    displayname: PropertyRef = PropertyRef(
        "displayName", description='The "friendly name", e.g. "My Company".'
    )
    lifecyclestate: PropertyRef = PropertyRef(
        "lifecycleState",
        description="The organization's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/organizations#LifecycleState).",
    )


@dataclass(frozen=True)
class GCPOrganizationSchema(CartographyNodeSchema):
    """Representation of a GCP [Organization](https://cloud.google.com/resource-manager/reference/rest/v1/organizations) object."""

    label: str = "GCPOrganization"
    properties: GCPOrganizationNodeProperties = GCPOrganizationNodeProperties()
    # sub_resource_relationship is None by default - Organizations are top-level resources
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
