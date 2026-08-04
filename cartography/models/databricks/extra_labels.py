from cartography.models.core.nodes import ExtraNodeLabel

DATABRICKS_ACL_OBJECT = ExtraNodeLabel(
    label="DatabricksAclObject",
    description="An object that can receive Databricks workspace permissions.",
)


DATABRICKS_SECURABLE = ExtraNodeLabel(
    label="DatabricksSecurable",
    description="A Unity Catalog object that can receive Databricks privileges.",
)
