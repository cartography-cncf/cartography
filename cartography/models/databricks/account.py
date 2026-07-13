from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class DatabricksAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    account_id: PropertyRef = PropertyRef("account_id", extra_index=True)
    host: PropertyRef = PropertyRef("host")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountSchema(CartographyNodeSchema):
    label: str = "DatabricksAccount"
    properties: DatabricksAccountNodeProperties = DatabricksAccountNodeProperties()
    # `Tenant` is the ontology label for the top-level resource container; the
    # account is the parent of every workspace it owns. Top-level node with no
    # sub-resource, like AWSAccount / GCPProject.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
