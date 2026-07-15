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
class CodeBuildProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn", description="The ARN of the CodeBuild Project")
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the CodeBuild Project",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The CodeBuild Project name"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the codebuild project"
    )
    created: PropertyRef = PropertyRef(
        "created", description="The creation time of the CodeBuild Project"
    )
    environment_variables: PropertyRef = PropertyRef(
        "environmentVariables",
        description="A list of environment variables used in the build environment. Each variable is represented as a string in the format `<NAME>=<VALUE>`. Variables of type `PLAINTEXT` retain their values (e.g., `ENV=prod`), while variables of type `PARAMETER_STORE`, `SECRETS_MANAGER`, etc., have values redacted as `<REDACTED>` (e.g., `SECRET_TOKEN=<REDACTED>`)",
    )
    source_type: PropertyRef = PropertyRef(
        "sourceType",
        description="The type of repository that contains the source code to be built",
    )
    source_location: PropertyRef = PropertyRef(
        "sourceLocation",
        description="Information about the location of the source code to be built",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CodeBuildProjectToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CodeBuildProjectToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCodeBuildProject`."

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
    "Represents an `AWSCodeBuildProject` node in the AWS graph."

    label: str = "AWSCodeBuildProject"
    properties: CodeBuildProjectNodeProperties = CodeBuildProjectNodeProperties()
    # DEPRECATED: legacy CodeBuildProject node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["CodeBuildProject", "CICDPipeline"]
    )
    sub_resource_relationship: CodeBuildProjectToAWSAccountRel = (
        CodeBuildProjectToAWSAccountRel()
    )
