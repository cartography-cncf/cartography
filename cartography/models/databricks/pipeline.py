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
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksPipelineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Databricks pipeline."
    )
    pipeline_id: PropertyRef = PropertyRef(
        "pipeline_id", extra_index=True, description="Databricks pipeline identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the pipeline."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the pipeline."
    )
    creator_user_name: PropertyRef = PropertyRef(
        "creator_user_name",
        extra_index=True,
        description="User name of the pipeline creator.",
    )
    run_as_user_name: PropertyRef = PropertyRef(
        "run_as_user_name",
        extra_index=True,
        description="Name of the principal that runs the pipeline.",
    )
    catalog: PropertyRef = PropertyRef(
        "catalog", extra_index=True, description="Target Unity Catalog catalog."
    )
    target_schema: PropertyRef = PropertyRef(
        "target_schema", description="Target schema for published pipeline data."
    )
    storage: PropertyRef = PropertyRef(
        "storage", description="Storage location used by the pipeline."
    )
    continuous: PropertyRef = PropertyRef(
        "continuous", description="Whether the pipeline runs continuously."
    )
    development: PropertyRef = PropertyRef(
        "development", description="Whether the pipeline uses development mode."
    )
    serverless: PropertyRef = PropertyRef(
        "serverless", description="Whether the pipeline uses serverless compute."
    )
    photon: PropertyRef = PropertyRef(
        "photon", description="Whether the pipeline uses the Photon engine."
    )
    edition: PropertyRef = PropertyRef(
        "edition", description="Product edition configured for the pipeline."
    )
    channel: PropertyRef = PropertyRef(
        "channel", description="Runtime release channel used by the pipeline."
    )
    pipeline_type: PropertyRef = PropertyRef(
        "pipeline_type", description="Type of the pipeline."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksPipelineToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksPipeline)
class DatabricksPipelineToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this pipeline resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksPipelineToWorkspaceRelProperties = (
        DatabricksPipelineToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksPipelineToCatalogRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksPipeline)-[:PUBLISHES_TO]->(:DatabricksCatalog)
class DatabricksPipelineToCatalogRel(CartographyRelSchema):
    """A Databricks pipeline publishes data to a Unity Catalog catalog."""

    target_node_label: str = "DatabricksCatalog"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("catalog_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PUBLISHES_TO"
    properties: DatabricksPipelineToCatalogRelProperties = (
        DatabricksPipelineToCatalogRelProperties()
    )


# See job.py for why RUN_AS matches on the workspace-scoped principal id.


@dataclass(frozen=True)
class DatabricksPipelineToRunAsUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksPipeline)-[:RUN_AS]->(:DatabricksUser)
class DatabricksPipelineToRunAsUserRel(CartographyRelSchema):
    """A Databricks pipeline runs as a Databricks user."""

    target_node_label: str = "DatabricksUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("run_as_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUN_AS"
    properties: DatabricksPipelineToRunAsUserRelProperties = (
        DatabricksPipelineToRunAsUserRelProperties()
    )


@dataclass(frozen=True)
class DatabricksPipelineToRunAsSPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksPipeline)-[:RUN_AS]->(:DatabricksServicePrincipal)
class DatabricksPipelineToRunAsSPRel(CartographyRelSchema):
    """A Databricks pipeline runs as a Databricks service principal."""

    target_node_label: str = "DatabricksServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("run_as_sp_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUN_AS"
    properties: DatabricksPipelineToRunAsSPRelProperties = (
        DatabricksPipelineToRunAsSPRelProperties()
    )


@dataclass(frozen=True)
class DatabricksPipelineSchema(CartographyNodeSchema):
    """A Databricks data pipeline in a workspace."""

    label: str = "DatabricksPipeline"
    properties: DatabricksPipelineNodeProperties = DatabricksPipelineNodeProperties()
    sub_resource_relationship: DatabricksPipelineToWorkspaceRel = (
        DatabricksPipelineToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksPipelineToCatalogRel(),
            DatabricksPipelineToRunAsUserRel(),
            DatabricksPipelineToRunAsSPRel(),
        ],
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
