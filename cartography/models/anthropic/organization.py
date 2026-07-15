from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AnthropicOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class AnthropicOrganizationSchema(CartographyNodeSchema):
    """An Anthropic organization containing users, workspaces, and API keys."""

    label: str = "AnthropicOrganization"
    properties: AnthropicOrganizationNodeProperties = (
        AnthropicOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
