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
from cartography.models.ontology.labels import TENANT
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Snowflake organization name.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The Snowflake organization name."
    )


@dataclass(frozen=True)
class SnowflakeOrganizationSchema(CartographyNodeSchema):
    """Represents a Snowflake organization: the container that owns a set of accounts."""

    label: str = "SnowflakeOrganization"
    properties: SnowflakeOrganizationNodeProperties = (
        SnowflakeOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    # The organization is the root of the Snowflake hierarchy, so it deliberately
    # has no sub_resource_relationship and is never cleaned up by a scoped job.
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class SnowflakeAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The account identifier, as ORGANIZATION.ACCOUNT.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The account name within the organization.",
    )
    organization_name: PropertyRef = PropertyRef(
        "organization_name",
        extra_index=True,
        description="The organization that owns the account.",
    )
    edition: PropertyRef = PropertyRef(
        "edition",
        description=(
            "The Snowflake edition, which gates features such as masking policies "
            "and failover groups."
        ),
    )
    region: PropertyRef = PropertyRef(
        "region", description="The cloud region hosting the account."
    )
    region_group: PropertyRef = PropertyRef(
        "region_group", description="The region group the account's region belongs to."
    )
    account_url: PropertyRef = PropertyRef(
        "account_url", description="The account's preferred URL."
    )
    account_locator: PropertyRef = PropertyRef(
        "account_locator",
        extra_index=True,
        description="The account's legacy locator identifier.",
    )
    is_org_admin: PropertyRef = PropertyRef(
        "is_org_admin",
        description="Whether the ORGADMIN role is enabled in this account.",
    )
    retention_time: PropertyRef = PropertyRef(
        "retention_time",
        description="Days the account remains restorable after being dropped.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Account comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the account was created."
    )
    dropped_on: PropertyRef = PropertyRef(
        "dropped_on",
        description="When the account was dropped, if it has been.",
    )
    scheduled_deletion_time: PropertyRef = PropertyRef(
        "scheduled_deletion_time",
        description="When a dropped account is scheduled for permanent deletion.",
    )
    is_current: PropertyRef = PropertyRef(
        "is_current",
        description=(
            "Whether this is the account Cartography authenticated against. Only the "
            "current account has its objects synced; sibling accounts in the "
            "organization are recorded as nodes without resources."
        ),
    )


@dataclass(frozen=True)
class SnowflakeAccountToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeOrganization)-[:RESOURCE]->(:SnowflakeAccount)
class SnowflakeAccountToOrganizationRel(CartographyRelSchema):
    """A Snowflake organization contains the account."""

    target_node_label: str = "SnowflakeOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_name")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeAccountToOrganizationRelProperties = (
        SnowflakeAccountToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccountSchema(CartographyNodeSchema):
    """Represents a Snowflake account: the tenant that owns every other Snowflake object."""

    label: str = "SnowflakeAccount"
    properties: SnowflakeAccountNodeProperties = SnowflakeAccountNodeProperties()
    # The account carries SnowflakeSecurable because account-level privileges
    # (CREATE USER, MANAGE GRANTS, ...) are granted on the account itself, so it
    # has to be a valid HAS_PRIVILEGE target.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT, SNOWFLAKE_SECURABLE])
    # The account is the tenant every other node hangs off, so it has no
    # sub_resource_relationship of its own and is never scope-cleaned. The
    # organization edge is an ordinary relationship because listing the
    # organization requires ORGADMIN, which most collectors do not hold.
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeAccountToOrganizationRel()],
    )
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class SnowflakeManagedAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the managed account."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The managed account name."
    )
    account_type: PropertyRef = PropertyRef(
        "account_type",
        description="The managed account type; READER for a reader account.",
    )
    is_reader: PropertyRef = PropertyRef(
        "is_reader",
        description=(
            "Whether this is a reader account, which consumes shared data without "
            "a Snowflake contract of its own."
        ),
    )
    locator: PropertyRef = PropertyRef(
        "locator", extra_index=True, description="The managed account's locator."
    )
    url: PropertyRef = PropertyRef(
        "url", description="The managed account's login URL."
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="The cloud hosting the managed account."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region hosting the managed account."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Managed account comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the managed account was created."
    )


@dataclass(frozen=True)
class SnowflakeManagedAccountToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeManagedAccount)
class SnowflakeManagedAccountToAccountRel(CartographyRelSchema):
    """A Snowflake account owns the managed account it created."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeManagedAccountToAccountRelProperties = (
        SnowflakeManagedAccountToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeManagedAccountSchema(CartographyNodeSchema):
    """Represents a Snowflake managed account, such as a reader account created to consume a share."""

    label: str = "SnowflakeManagedAccount"
    properties: SnowflakeManagedAccountNodeProperties = (
        SnowflakeManagedAccountNodeProperties()
    )
    # A managed account is a tenant in its own right, but Cartography cannot
    # authenticate into it, so it is recorded as a child of the account that
    # created it rather than as a sync root.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: SnowflakeManagedAccountToAccountRel = (
        SnowflakeManagedAccountToAccountRel()
    )
