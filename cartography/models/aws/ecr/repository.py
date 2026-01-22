from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ECRRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("repositoryArn")
    arn: PropertyRef = PropertyRef("repositoryArn", extra_index=True)
    name: PropertyRef = PropertyRef("repositoryName", extra_index=True)
    uri: PropertyRef = PropertyRef("repositoryUri", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "ECRRepositoryImage"
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
    label: str = "ECRRepository"
    properties: ECRRepositoryNodeProperties = ECRRepositoryNodeProperties()
    sub_resource_relationship: ECRRepositoryToAWSAccountRel = (
        ECRRepositoryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRRepositoryToRepositoryImageRel(),
        ]
    )
