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
class DatabricksBudgetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks budget configuration ID.",
    )
    budget_configuration_id: PropertyRef = PropertyRef(
        "budget_configuration_id",
        extra_index=True,
        description="Databricks budget configuration ID.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description="Budget display name.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksBudgetToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksBudget)
class DatabricksBudgetToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksBudgetToAccountRelProperties = (
        DatabricksBudgetToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksBudgetSchema(CartographyNodeSchema):
    """A Databricks account budget configuration."""

    label: str = "DatabricksBudget"
    properties: DatabricksBudgetNodeProperties = DatabricksBudgetNodeProperties()
    sub_resource_relationship: DatabricksBudgetToAccountRel = (
        DatabricksBudgetToAccountRel()
    )
