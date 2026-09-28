from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.snowflake.extra_labels import SNOWFLAKE_PRINCIPAL
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the role."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The role name."
    )
    role_type: PropertyRef = PropertyRef(
        "role_type",
        description=(
            "BUILTIN for a Snowflake system role such as ACCOUNTADMIN or "
            "SECURITYADMIN, CUSTOM otherwise."
        ),
    )
    comment: PropertyRef = PropertyRef("comment", description="Role comment.")
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns this role."
    )
    assigned_to_users: PropertyRef = PropertyRef(
        "assigned_to_users", description="Number of users this role is granted to."
    )
    granted_to_roles: PropertyRef = PropertyRef(
        "granted_to_roles", description="Number of roles this role is granted to."
    )
    granted_roles: PropertyRef = PropertyRef(
        "granted_roles", description="Number of roles granted to this role."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the role was created."
    )


@dataclass(frozen=True)
class SnowflakeRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeRole)
class SnowflakeRoleToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the role as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeRoleToAccountRelProperties = (
        SnowflakeRoleToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeRoleSchema(CartographyNodeSchema):
    """Represents a Snowflake account-level role, the unit privileges are granted to."""

    label: str = "SnowflakeRole"
    properties: SnowflakeRoleNodeProperties = SnowflakeRoleNodeProperties()
    # A role both holds privileges and can have privileges granted on it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [PERMISSION_ROLE, SNOWFLAKE_PRINCIPAL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeRoleToAccountRel = SnowflakeRoleToAccountRel()


@dataclass(frozen=True)
class SnowflakeDatabaseRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the database role."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The database role name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The database-qualified role name, as DATABASE.ROLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="The database that owns the role."
    )
    comment: PropertyRef = PropertyRef("comment", description="Database role comment.")
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns this database role."
    )
    granted_to_roles: PropertyRef = PropertyRef(
        "granted_to_roles",
        description="Number of account roles this database role is granted to.",
    )
    granted_to_database_roles: PropertyRef = PropertyRef(
        "granted_to_database_roles",
        description="Number of database roles this database role is granted to.",
    )
    granted_database_roles: PropertyRef = PropertyRef(
        "granted_database_roles",
        description="Number of database roles granted to this database role.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the database role was created."
    )


@dataclass(frozen=True)
class SnowflakeDatabaseRoleToDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeDatabase)-[:CONTAINS]->(:SnowflakeDatabaseRole)
class SnowflakeDatabaseRoleToDatabaseRel(CartographyRelSchema):
    """A Snowflake database contains the database role."""

    target_node_label: str = "SnowflakeDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeDatabaseRoleToDatabaseRelProperties = (
        SnowflakeDatabaseRoleToDatabaseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDatabaseRoleSchema(CartographyNodeSchema):
    """Represents a Snowflake database role, whose privileges are confined to one database."""

    label: str = "SnowflakeDatabaseRole"
    properties: SnowflakeDatabaseRoleNodeProperties = (
        SnowflakeDatabaseRoleNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [PERMISSION_ROLE, SNOWFLAKE_PRINCIPAL, SNOWFLAKE_SECURABLE],
    )
    # Scoped to the account, not the database: cleanup has to be able to delete a
    # database role whose database was dropped between syncs.
    sub_resource_relationship: SnowflakeRoleToAccountRel = SnowflakeRoleToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeDatabaseRoleToDatabaseRel()],
    )
