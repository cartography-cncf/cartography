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
class SpaceliftStackNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Stack node.
    """

    id: PropertyRef = PropertyRef("id", description="Spacelift stack ID.")
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Stack name.")
    description: PropertyRef = PropertyRef(
        "description", description="Stack description."
    )
    state: PropertyRef = PropertyRef("state", description="Current stack state.")
    administrative: PropertyRef = PropertyRef(
        "administrative", description="Whether this is an administrative stack."
    )
    repository: PropertyRef = PropertyRef(
        "repository", description="VCS repository used by the stack."
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Git branch monitored by the stack."
    )
    project_root: PropertyRef = PropertyRef(
        "project_root", description="Repository directory containing project code."
    )
    space_id: PropertyRef = PropertyRef(
        "space_id", description="ID of the space containing the stack."
    )
    spacelift_account_id: PropertyRef = PropertyRef(
        "spacelift_account_id", description="ID of the containing Spacelift account."
    )
    aws_role_arn: PropertyRef = PropertyRef(
        "aws_role_arn", description="ARN of the AWS IAM role assumed at runtime."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SpaceliftStackToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Stack and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToAccountRel(CartographyRelSchema):
    """A Spacelift account contains a stack."""

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftStackToAccountRelProperties = (
        SpaceliftStackToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftStackToSpaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToSpaceRel(CartographyRelSchema):
    """A Spacelift space contains a stack."""

    target_node_label: str = "SpaceliftSpace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("space_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SpaceliftStackToSpaceRelProperties = (
        SpaceliftStackToSpaceRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftStackToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToAWSRoleRel(CartographyRelSchema):
    """A Spacelift stack assumes an AWS IAM role at runtime."""

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: SpaceliftStackToAWSRoleRelProperties = (
        SpaceliftStackToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftStackSchema(CartographyNodeSchema):
    """An infrastructure management stack with the CICDPipeline label."""

    label: str = "SpaceliftStack"
    properties: SpaceliftStackNodeProperties = SpaceliftStackNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CICDPipeline"])
    sub_resource_relationship: SpaceliftStackToAccountRel = SpaceliftStackToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftStackToSpaceRel(),
            SpaceliftStackToAWSRoleRel(),
        ],
    )
