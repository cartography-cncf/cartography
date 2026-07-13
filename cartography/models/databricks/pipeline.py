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


@dataclass(frozen=True)
class DatabricksPipelineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    pipeline_id: PropertyRef = PropertyRef("pipeline_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    creator_user_name: PropertyRef = PropertyRef("creator_user_name", extra_index=True)
    run_as_user_name: PropertyRef = PropertyRef("run_as_user_name", extra_index=True)
    catalog: PropertyRef = PropertyRef("catalog", extra_index=True)
    target_schema: PropertyRef = PropertyRef("target_schema")
    storage: PropertyRef = PropertyRef("storage")
    continuous: PropertyRef = PropertyRef("continuous")
    development: PropertyRef = PropertyRef("development")
    serverless: PropertyRef = PropertyRef("serverless")
    photon: PropertyRef = PropertyRef("photon")
    edition: PropertyRef = PropertyRef("edition")
    channel: PropertyRef = PropertyRef("channel")
    pipeline_type: PropertyRef = PropertyRef("pipeline_type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksPipelineToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksPipeline)
class DatabricksPipelineToWorkspaceRel(CartographyRelSchema):
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksAclObject"])
