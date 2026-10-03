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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class ScalewayCockpitProperties(CartographyNodeProperties):
    # Cockpit has no provider-side ID of its own - it's a singleton per project - so
    # the project's own id is reused as this node's id.
    id: PropertyRef = PropertyRef(
        "id", description="ID of the owning project (used as this node's id)."
    )
    plan_name: PropertyRef = PropertyRef(
        "plan_name", description="Cockpit plan for this project (e.g. `free`)."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayCockpitToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayCockpit)
class ScalewayCockpitToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayCockpit` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayCockpitToProjectRelProperties = (
        ScalewayCockpitToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayCockpitSchema(CartographyNodeSchema):
    """Represents a project's Scaleway Cockpit (observability) configuration."""

    label: str = "ScalewayCockpit"
    properties: ScalewayCockpitProperties = ScalewayCockpitProperties()
    sub_resource_relationship: ScalewayCockpitToProjectRel = (
        ScalewayCockpitToProjectRel()
    )


@dataclass(frozen=True)
class ScalewayCockpitDataSourceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Data source unique ID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Data source name."
    )
    url: PropertyRef = PropertyRef("url", description="Data source query URL.")
    type: PropertyRef = PropertyRef(
        "type_", description="Data source type (`metrics`, `logs`, `traces`)."
    )
    origin: PropertyRef = PropertyRef(
        "origin",
        description="Where the data source's data comes from (`scaleway`, `external`, `custom`).",
    )
    synchronized_with_grafana: PropertyRef = PropertyRef(
        "synchronized_with_grafana",
        description="Whether this data source is synchronized as a Grafana data source.",
    )
    retention_days: PropertyRef = PropertyRef(
        "retention_days", description="Number of days data is retained."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the data source lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Data source creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Data source last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayCockpitDataSourceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayCockpitDataSource)
class ScalewayCockpitDataSourceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayCockpitDataSource` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayCockpitDataSourceToProjectRelProperties = (
        ScalewayCockpitDataSourceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayCockpitDataSourceToCockpitRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayCockpit)-[:HAS]->(:ScalewayCockpitDataSource)
class ScalewayCockpitDataSourceToCockpitRel(CartographyRelSchema):
    """Connects `ScalewayCockpit` to `ScalewayCockpitDataSource` through `HAS`."""

    target_node_label: str = "ScalewayCockpit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayCockpitDataSourceToCockpitRelProperties = (
        ScalewayCockpitDataSourceToCockpitRelProperties()
    )


@dataclass(frozen=True)
class ScalewayCockpitDataSourceSchema(CartographyNodeSchema):
    """A Grafana/Cockpit data source (metrics, logs, or traces) within a project."""

    label: str = "ScalewayCockpitDataSource"
    properties: ScalewayCockpitDataSourceProperties = (
        ScalewayCockpitDataSourceProperties()
    )
    sub_resource_relationship: ScalewayCockpitDataSourceToProjectRel = (
        ScalewayCockpitDataSourceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ScalewayCockpitDataSourceToCockpitRel()],
    )


@dataclass(frozen=True)
class ScalewayCockpitTokenProperties(CartographyNodeProperties):
    # The token's secret_key (its actual bearer credential) is intentionally never
    # read into this node - see cartography/intel/scaleway/cockpit/cockpit.py.
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Token unique ID."
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Token name.")
    scopes: PropertyRef = PropertyRef(
        "scopes", description="Permission scopes granted to this token."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the token lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Token creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Token last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayCockpitTokenToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayCockpitToken)
class ScalewayCockpitTokenToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayCockpitToken` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayCockpitTokenToProjectRelProperties = (
        ScalewayCockpitTokenToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayCockpitTokenToCockpitRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayCockpit)-[:HAS]->(:ScalewayCockpitToken)
class ScalewayCockpitTokenToCockpitRel(CartographyRelSchema):
    """Connects `ScalewayCockpit` to `ScalewayCockpitToken` through `HAS`."""

    target_node_label: str = "ScalewayCockpit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayCockpitTokenToCockpitRelProperties = (
        ScalewayCockpitTokenToCockpitRelProperties()
    )


@dataclass(frozen=True)
class ScalewayCockpitTokenSchema(CartographyNodeSchema):
    """
    A Cockpit API token: a bearer credential that can read/write observability data.

    Scaleway's list API returns each token's full secret_key alongside its metadata.
    Cartography deliberately ingests only the metadata - see
    cartography/intel/scaleway/cockpit/cockpit.py for where that secret_key is dropped.
    """

    label: str = "ScalewayCockpitToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    properties: ScalewayCockpitTokenProperties = ScalewayCockpitTokenProperties()
    sub_resource_relationship: ScalewayCockpitTokenToProjectRel = (
        ScalewayCockpitTokenToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ScalewayCockpitTokenToCockpitRel()],
    )
