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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    endpoint: PropertyRef = PropertyRef("endpoint")
    # Serverless SQL is reached over a public connection endpoint; kept
    # consistent with the other data-service exposure flags.
    is_public: PropertyRef = PropertyRef("is_public")
    cpu_min: PropertyRef = PropertyRef("cpu_min")
    cpu_max: PropertyRef = PropertyRef("cpu_max")
    cpu_current: PropertyRef = PropertyRef("cpu_current")
    started: PropertyRef = PropertyRef("started")
    engine_major_version: PropertyRef = PropertyRef("engine_major_version")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayServerlessSQLDatabaseToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessSQLDatabase)
class ScalewayServerlessSQLDatabaseToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayServerlessSQLDatabase"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayServerlessSQLDatabaseProperties = (
        ScalewayServerlessSQLDatabaseProperties()
    )
    sub_resource_relationship: ScalewayServerlessSQLDatabaseToProjectRel = (
        ScalewayServerlessSQLDatabaseToProjectRel()
    )
