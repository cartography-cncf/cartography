from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CodeBuildProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    created: PropertyRef = PropertyRef("created")
    environment_variables: PropertyRef = PropertyRef("environmentVariables")
    source_type: PropertyRef = PropertyRef("sourceType")
    source_location: PropertyRef = PropertyRef("sourceLocation")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CodeBuildProjectToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CodeBuildProjectToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CodeBuildProjectToAwsAccountRelProperties = (
        CodeBuildProjectToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CodeBuildProjectSchema(CartographyNodeSchema):
    label: str = "CodeBuildProject"
    properties: CodeBuildProjectNodeProperties = CodeBuildProjectNodeProperties()
    sub_resource_relationship: CodeBuildProjectToAWSAccountRel = (
        CodeBuildProjectToAWSAccountRel()
    )
