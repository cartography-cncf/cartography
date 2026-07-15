from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class DatabricksAclObjectLabel(ExtraNodeLabel):
    """An object that can receive Databricks workspace permissions."""

    label: str = "DatabricksAclObject"


@dataclass(frozen=True)
class DatabricksSecurableLabel(ExtraNodeLabel):
    """A Unity Catalog object that can receive Databricks privileges."""

    label: str = "DatabricksSecurable"
