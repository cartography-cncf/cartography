from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayServerlessSQLDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the database.")
    name: PropertyRef = PropertyRef("name", description="Name of the database.")
    status: PropertyRef = PropertyRef("status", description="Status of the database.")
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="Connection endpoint URL."
    )
    # Serverless SQL is reached over a public connection endpoint; kept
    # consistent with the other data-service exposure flags.
    is_public: PropertyRef = PropertyRef(
        "is_public", description="True if reachable over a public endpoint."
    )
    cpu_min: PropertyRef = PropertyRef("cpu_min", description="Minimum vCPU.")
    cpu_max: PropertyRef = PropertyRef("cpu_max", description="Maximum vCPU.")
    cpu_current: PropertyRef = PropertyRef("cpu_current", description="Current vCPU.")
    started: PropertyRef = PropertyRef(
        "started", description="Whether the database is started."
    )
    engine_major_version: PropertyRef = PropertyRef(
        "engine_major_version", description="Major engine version."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the database lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayServerlessSQLDatabaseToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessSQLDatabase)
class ScalewayServerlessSQLDatabaseToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayServerlessSQLDatabase` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessSQLDatabaseToProjectRelProperties = (
        ScalewayServerlessSQLDatabaseToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessSQLDatabaseSchema(CartographyNodeSchema):
    """Represents a Serverless SQL Database (PostgreSQL) in Scaleway."""

    label: str = "ScalewayServerlessSQLDatabase"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayServerlessSQLDatabaseProperties = (
        ScalewayServerlessSQLDatabaseProperties()
    )
    sub_resource_relationship: ScalewayServerlessSQLDatabaseToProjectRel = (
        ScalewayServerlessSQLDatabaseToProjectRel()
    )
