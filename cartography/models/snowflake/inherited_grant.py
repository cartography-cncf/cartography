from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SnowflakeInheritedGrantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    privilege: PropertyRef = PropertyRef(
        "privilege",
        description="Privilege on matching objects inside the container, not on the container itself.",
    )
    object_type: PropertyRef = PropertyRef(
        "object_type",
        description="Snowflake object type covered by this grant, such as TABLE or VIEW.",
    )
    container_type: PropertyRef = PropertyRef(
        "container_type", description="ACCOUNT, DATABASE, or SCHEMA scope."
    )
    database_name: PropertyRef = PropertyRef("database_name")
    schema_name: PropertyRef = PropertyRef("schema_name")
    grantee_name: PropertyRef = PropertyRef("grantee_name")
    grantee_type: PropertyRef = PropertyRef(
        "grantee_type",
        description="Provider grantee kind; unsupported principal kinds retain their identity here.",
    )
    grant_option: PropertyRef = PropertyRef("grant_option")
    granted_by: PropertyRef = PropertyRef("granted_by")
    created_on: PropertyRef = PropertyRef("created_on")


@dataclass(frozen=True)
class SnowflakeInheritedGrantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnowflakeInheritedGrantToAccount(CartographyRelSchema):
    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeInheritedGrantRelProperties = (
        SnowflakeInheritedGrantRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeInheritedGrantToPrincipal(CartographyRelSchema):
    """A principal holds a grant applying to matching current and future objects."""

    target_node_label: str = "SnowflakePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INHERITED_GRANT"
    properties: SnowflakeInheritedGrantRelProperties = (
        SnowflakeInheritedGrantRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeInheritedGrantToContainer(CartographyRelSchema):
    """The inherited grant applies inside this account, database, or schema."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("container_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_IN"
    properties: SnowflakeInheritedGrantRelProperties = (
        SnowflakeInheritedGrantRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeInheritedGrantSchema(CartographyNodeSchema):
    """An object-type-specific privilege on current and future objects within a container. Required container privileges and policy restrictions still apply; this is not an expanded effective-access edge."""

    label: str = "SnowflakeInheritedGrant"
    properties: SnowflakeInheritedGrantProperties = SnowflakeInheritedGrantProperties()
    sub_resource_relationship: SnowflakeInheritedGrantToAccount = (
        SnowflakeInheritedGrantToAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeInheritedGrantToPrincipal(), SnowflakeInheritedGrantToContainer()]
    )
