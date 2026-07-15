from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SpaceliftAccountNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Account node.
    """

    id: PropertyRef = PropertyRef("id", description="Spacelift account ID.")
    spacelift_account_id: PropertyRef = PropertyRef(
        "spacelift_account_id",
        extra_index=True,
        description="Spacelift account identifier.",
    )
    name: PropertyRef = PropertyRef("name", description="Account display name.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SpaceliftAccountSchema(CartographyNodeSchema):
    """A Spacelift account that contains the organization's resources."""

    label: str = "SpaceliftAccount"
    properties: SpaceliftAccountNodeProperties = SpaceliftAccountNodeProperties()
    sub_resource_relationship = None
    other_relationships = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
