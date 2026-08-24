from cartography.models.core.nodes import ExtraNodeLabel

# Snowflake's RBAC model grants privileges from any grantee kind to almost any
# object kind. Declaring one shared source label and one shared target label lets
# the whole grant graph ride on a single HAS_PRIVILEGE relationship instead of a
# relationship per (grantee label, object label) pair, the same way
# DatabricksSecurable collapses Unity Catalog grants. Neither label is a
# standalone node type.

SNOWFLAKE_PRINCIPAL = ExtraNodeLabel(
    label="SnowflakePrincipal",
    description="A Snowflake grantee that can hold privileges.",
)


SNOWFLAKE_SECURABLE = ExtraNodeLabel(
    label="SnowflakeSecurable",
    description="A Snowflake object that can receive privileges through GRANT.",
)
