from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class DatabricksAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Databricks account ID.")
    account_id: PropertyRef = PropertyRef(
        "account_id",
        extra_index=True,
        description="Databricks account ID.",
    )
    host: PropertyRef = PropertyRef(
        "host",
        description="Host URL for the Databricks account API.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountSchema(CartographyNodeSchema):
    """A Databricks account that owns workspaces and account-level resources."""

    label: str = "DatabricksAccount"
    properties: DatabricksAccountNodeProperties = DatabricksAccountNodeProperties()
    # `Tenant` is the ontology label for the top-level resource container; the
    # account is the parent of every workspace it owns. Top-level node with no
    # sub-resource, like AWSAccount / GCPProject.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
