from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class DatabricksWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    host: PropertyRef = PropertyRef("host", extra_index=True)
    tokens_enabled: PropertyRef = PropertyRef("tokens_enabled")
    max_token_lifetime_days: PropertyRef = PropertyRef("max_token_lifetime_days")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksWorkspaceSchema(CartographyNodeSchema):
    label: str = "DatabricksWorkspace"
    properties: DatabricksWorkspaceNodeProperties = DatabricksWorkspaceNodeProperties()
    # `Tenant` is the ontology label for the top-level resource container.
    # ponytail: scoped under the workspace; account-level (`DatabricksAccount`) lands
    # in a follow-up PR alongside the Accounts API client.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
