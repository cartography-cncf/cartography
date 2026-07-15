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
class CircleCIPipelineNodeProperties(CartographyNodeProperties):
    # A pipeline definition (the config/source binding). Pipeline runs are not
    # ingested - they are high-volume ephemeral telemetry, not inventory.
    id: PropertyRef = PropertyRef("id", description="CircleCI pipeline ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Pipeline name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Pipeline description."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Pipeline creation timestamp."
    )
    config_source_provider: PropertyRef = PropertyRef(
        "config_source_provider", description="Pipeline configuration provider."
    )
    config_source_repo_full_name: PropertyRef = PropertyRef(
        "config_source_repo_full_name",
        description="Full name of the configuration repository.",
    )
    config_source_repo_external_id: PropertyRef = PropertyRef(
        "config_source_repo_external_id",
        description="External ID of the configuration repository.",
    )
    config_source_file_path: PropertyRef = PropertyRef(
        "config_source_file_path",
        description="Path to the pipeline configuration file.",
    )
    checkout_source_provider: PropertyRef = PropertyRef(
        "checkout_source_provider", description="Pipeline checkout provider."
    )
    checkout_source_repo_full_name: PropertyRef = PropertyRef(
        "checkout_source_repo_full_name",
        description="Full name of the checkout repository.",
    )
    checkout_source_repo_external_id: PropertyRef = PropertyRef(
        "checkout_source_repo_external_id",
        description="External ID of the checkout repository.",
    )


@dataclass(frozen=True)
class CircleCIPipelineToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIPipeline)
class CircleCIPipelineToProjectRel(CartographyRelSchema):
    """The CircleCI project contains the pipeline definition."""

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIPipelineToProjectRelProperties = (
        CircleCIPipelineToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIPipelineSchema(CartographyNodeSchema):
    """A CircleCI pipeline definition with the canonical CICDPipeline label."""

    label: str = "CircleCIPipeline"
    properties: CircleCIPipelineNodeProperties = CircleCIPipelineNodeProperties()
    # CICDPipeline label maps this node into the ontology alongside other CI/CD
    # pipelines (GitHubWorkflow, GitLab CI, AWS CodeBuild, Spacelift stacks).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CICDPipeline"])
    sub_resource_relationship: CircleCIPipelineToProjectRel = (
        CircleCIPipelineToProjectRel()
    )
