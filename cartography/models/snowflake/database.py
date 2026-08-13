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
from cartography.models.ontology.labels import DATABASE
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeDatabaseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the database."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The database name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The database name as it appears in a fully-qualified object name.",
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description=(
            "The database kind reported by Snowflake, for example STANDARD or "
            "IMPORTED DATABASE."
        ),
    )
    origin: PropertyRef = PropertyRef(
        "origin",
        extra_index=True,
        description=(
            "The share this database was created from, as PROVIDER_ACCOUNT.SHARE. "
            "Empty for a database created locally."
        ),
    )
    is_from_share: PropertyRef = PropertyRef(
        "is_from_share",
        description=(
            "Whether the database is a read-only mount of an inbound share rather "
            "than data this account owns."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the database."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Database comment.")
    options: PropertyRef = PropertyRef(
        "options",
        description="Database options such as TRANSIENT, as reported by Snowflake.",
    )
    retention_time: PropertyRef = PropertyRef(
        "retention_time",
        description="Days a dropped database stays recoverable through UNDROP.",
    )
    data_retention_time_in_days: PropertyRef = PropertyRef(
        "data_retention_time_in_days",
        description=(
            "Time Travel window in days. A value of 0 disables Time Travel, which "
            "removes the ability to recover data after an accidental or malicious "
            "change."
        ),
    )
    budget: PropertyRef = PropertyRef(
        "budget", description="Name of the budget the database is attached to."
    )
    is_current: PropertyRef = PropertyRef(
        "is_current",
        description="Whether this is the current database for the collecting session.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description="Whether this is the default database for the collecting user.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the database was created."
    )
    dropped_on: PropertyRef = PropertyRef(
        "dropped_on",
        description="When the database was dropped, if it is pending purge.",
    )


@dataclass(frozen=True)
class SnowflakeDatabaseToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeDatabase)
class SnowflakeDatabaseToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the database as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeDatabaseToAccountRelProperties = (
        SnowflakeDatabaseToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDatabaseToShareRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeDatabase)-[:CREATED_FROM_SHARE]->(:SnowflakeShare)
class SnowflakeDatabaseToShareRel(CartographyRelSchema):
    """The database is a read-only mount of data another Snowflake account shared in.

    Data reachable through this database belongs to the provider account, so a
    privilege granted here exposes someone else's data rather than this account's.
    """

    target_node_label: str = "SnowflakeShare"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("share_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_FROM_SHARE"
    properties: SnowflakeDatabaseToShareRelProperties = (
        SnowflakeDatabaseToShareRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDatabaseSchema(CartographyNodeSchema):
    """Represents a Snowflake database, the top container of the data hierarchy."""

    label: str = "SnowflakeDatabase"
    properties: SnowflakeDatabaseNodeProperties = SnowflakeDatabaseNodeProperties()
    # Database: ontology label for cross-provider data store queries.
    # SnowflakeSecurable: shared target label for the account's grant graph.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [DATABASE, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeDatabaseToAccountRel = (
        SnowflakeDatabaseToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeDatabaseToShareRel()],
    )
