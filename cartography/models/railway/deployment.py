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
from cartography.models.ontology.labels import CONTAINER


@dataclass(frozen=True)
class RailwayDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway deployment.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    status: PropertyRef = PropertyRef(
        "status", extra_index=True, description="Current deployment status."
    )
    # "current" for the revision the service instance is serving, "historical" for a
    # superseded one. Drives the conditional Container label below.
    lifecycle: PropertyRef = PropertyRef(
        "lifecycle",
        extra_index=True,
        description="Whether this deployment is the current or a historical revision.",
    )
    status_updated_at: PropertyRef = PropertyRef(
        "statusUpdatedAt", description="Time when the deployment status last changed."
    )
    project_id: PropertyRef = PropertyRef(
        "projectId", description="ID of the owning project."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the deployment environment.",
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId", extra_index=True, description="ID of the deployed service."
    )
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="URL associated with the deployment."
    )
    static_url: PropertyRef = PropertyRef(
        "staticUrl", description="Stable URL associated with the deployment."
    )
    can_redeploy: PropertyRef = PropertyRef(
        "canRedeploy", description="Whether the deployment can be redeployed."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the deployment was created."
    )
    # Copied from the parent RailwayServiceInstance.source_image onto the current revision so
    # the image ontology can reach it. Railway only exposes an image reference for the current
    # deployment, so historical revisions leave these null.
    image_uri: PropertyRef = PropertyRef(
        "image_uri",
        extra_index=True,
        description="Container image reference this deployment runs, when deployed from a registry.",
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        description="Digest (e.g. `sha256:...`) when `image_uri` is pinned by digest; `None` for tag-based references.",
    )


@dataclass(frozen=True)
class RailwayDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayDeployment)
class RailwayDeploymentToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a deployment that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayDeploymentToProjectRelProperties = (
        RailwayDeploymentToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeployment)-[:WORKLOAD_PARENT]->(:RailwayServiceInstance)
# Required by ONTOLOGY_REL_CONSTRAINTS: Container -> ComputeService must be WORKLOAD_PARENT.
class RailwayDeploymentToServiceInstanceRel(CartographyRelSchema):
    """Identifies the service instance represented by a Railway deployment revision."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("serviceId"),
            "environment_id": PropertyRef("environmentId"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: RailwayDeploymentToServiceInstanceRelProperties = (
        RailwayDeploymentToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeployment)-[:HAS_IMAGE]->(:AWSECRImage), joined on digest.
class RailwayDeploymentToECRImageRel(CartographyRelSchema):
    """Links a deployment to the image it runs, hosted in Amazon ECR."""

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: RailwayDeploymentToECRImageRelProperties = (
        RailwayDeploymentToECRImageRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeployment)-[:HAS_IMAGE]->(:GitLabContainerImage), joined on digest.
class RailwayDeploymentToGitLabContainerImageRel(CartographyRelSchema):
    """Links a deployment to the image it runs, hosted in the GitLab registry."""

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: RailwayDeploymentToGitLabContainerImageRelProperties = (
        RailwayDeploymentToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentToGCPArtifactRegistryImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeployment)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage), joined on digest.
class RailwayDeploymentToGCPArtifactRegistryImageRel(CartographyRelSchema):
    """Links a deployment to the image it runs, hosted in Artifact Registry."""

    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: RailwayDeploymentToGCPArtifactRegistryImageRelProperties = (
        RailwayDeploymentToGCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class RailwayDeploymentToGitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayDeployment)-[:HAS_IMAGE]->(:GitHubContainerImage), joined on digest.
class RailwayDeploymentToGitHubContainerImageRel(CartographyRelSchema):
    """Links a deployment to the image it runs, hosted in GitHub Container Registry."""

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: RailwayDeploymentToGitHubContainerImageRelProperties = (
        RailwayDeploymentToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
# A deployment is one concrete revision of a service instance, so the revision that is
# actually running plays the Container role to the instance's ComputeService - the same split
# GCP Cloud Run uses for Service and ServiceContainer.
#
# Only the current revision gets the label. Railway keeps a deployment row for every past
# attempt, including FAILED and CRASHED ones, and labelling those Container would fill the
# cross-provider container ontology with things that are not running. Superseded revisions
# stay in the graph as plain RailwayDeployment nodes for deploy history.
class RailwayDeploymentSchema(CartographyNodeSchema):
    """A concrete deployment revision of a Railway service instance."""

    label: str = "RailwayDeployment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [CONTAINER.when(lifecycle="current")],
    )
    properties: RailwayDeploymentNodeProperties = RailwayDeploymentNodeProperties()
    sub_resource_relationship: RailwayDeploymentToProjectRel = (
        RailwayDeploymentToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayDeploymentToServiceInstanceRel(),
            RailwayDeploymentToECRImageRel(),
            RailwayDeploymentToGitLabContainerImageRel(),
            RailwayDeploymentToGCPArtifactRegistryImageRel(),
            RailwayDeploymentToGitHubContainerImageRel(),
        ],
    )
