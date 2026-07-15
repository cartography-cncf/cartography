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
class ECRRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("repositoryArn", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "repositoryArn", extra_index=True, description="The ARN of the repository"
    )
    name: PropertyRef = PropertyRef(
        "repositoryName", extra_index=True, description="The name of the repository"
    )
    uri: PropertyRef = PropertyRef(
        "repositoryUri", extra_index=True, description="The URI of the repository"
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Date and time when the repository was created"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the repository"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECRRepositoryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECRRepository`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRRepositoryToAWSAccountRelProperties = (
        ECRRepositoryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECRRepositoryToRepositoryImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryToRepositoryImageRel(CartographyRelSchema):
    "Represents a `REPO_IMAGE` relationship from `AWSECRRepository` to `AWSECRRepositoryImage`."

    target_node_label: str = "AWSECRRepositoryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPO_IMAGE"
    properties: ECRRepositoryToRepositoryImageRelProperties = (
        ECRRepositoryToRepositoryImageRelProperties()
    )


@dataclass(frozen=True)
class ECRRepositorySchema(CartographyNodeSchema):
    "Represents an `AWSECRRepository` node in the AWS graph."

    label: str = "AWSECRRepository"
    # DEPRECATED: legacy ECRRepository node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ECRRepository", "ContainerRegistry"]
    )
    properties: ECRRepositoryNodeProperties = ECRRepositoryNodeProperties()
    sub_resource_relationship: ECRRepositoryToAWSAccountRel = (
        ECRRepositoryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRRepositoryToRepositoryImageRel(),
        ]
    )
