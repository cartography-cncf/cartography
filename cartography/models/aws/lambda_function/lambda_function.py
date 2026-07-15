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
class AWSLambdaNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "FunctionArn", description="The arn of the lambda function"
    )
    arn: PropertyRef = PropertyRef(
        "FunctionArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the lambda function",
    )
    name: PropertyRef = PropertyRef(
        "FunctionName", description="The name of the lambda function"
    )
    modifieddate: PropertyRef = PropertyRef(
        "LastModified",
        description="Timestamp of the last time the function was last updated",
    )
    runtime: PropertyRef = PropertyRef(
        "Runtime", description="The runtime environment for the Lambda function"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the Lambda function"
    )
    timeout: PropertyRef = PropertyRef(
        "Timeout",
        description="The amount of time in seconds that Lambda allows a function to run before stopping it",
    )
    memory: PropertyRef = PropertyRef(
        "MemorySize", description="The memory that's allocated to the function"
    )
    codesize: PropertyRef = PropertyRef(
        "CodeSize",
        description="The size of the function's deployment package, in bytes.",
    )
    handler: PropertyRef = PropertyRef(
        "Handler",
        description="The function that Lambda calls to begin executing your function.",
    )
    version: PropertyRef = PropertyRef(
        "Version", description="The version of the Lambda function."
    )
    tracingconfigmode: PropertyRef = PropertyRef(
        "TracingConfigMode",
        description="The function's AWS X-Ray tracing configuration mode.",
    )
    revisionid: PropertyRef = PropertyRef(
        "RevisionId",
        description="The latest updated revision of the function or alias.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The current state of the function."
    )
    statereason: PropertyRef = PropertyRef(
        "StateReason", description="The reason for the function's current state."
    )
    statereasoncode: PropertyRef = PropertyRef(
        "StateReasonCode",
        description="The reason code for the function's current state.",
    )
    lastupdatestatus: PropertyRef = PropertyRef(
        "LastUpdateStatus",
        description="The status of the last update that was performed on the function.",
    )
    lastupdatestatusreason: PropertyRef = PropertyRef(
        "LastUpdateStatusReason",
        description="The reason for the last update that was performed on the function.",
    )
    lastupdatestatusreasoncode: PropertyRef = PropertyRef(
        "LastUpdateStatusReasonCode",
        description="The reason code for the last update that was performed on the function.",
    )
    packagetype: PropertyRef = PropertyRef(
        "PackageType",
        description="The type of deployment package (`Zip` for source code, `Image` for container).",
    )
    image_uri: PropertyRef = PropertyRef(
        "image_uri",
        description="Container image reference (e.g., `123.dkr.ecr.us-east-1.amazonaws.com/repo@sha256:...`). Populated when `packagetype=Image`.",
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        description="Content-addressable digest (`sha256:...`) extracted from `image_uri` when the reference is digest-pinned.",
    )
    signingprofileversionarn: PropertyRef = PropertyRef(
        "SigningProfileVersionArn",
        description="The ARN of the signing profile version.",
    )
    signingjobarn: PropertyRef = PropertyRef(
        "SigningJobArn", description="The ARN of the signing job."
    )
    codesha256: PropertyRef = PropertyRef(
        "CodeSha256",
        description="The SHA256 hash of the function's deployment package.",
    )
    architectures: PropertyRef = PropertyRef(
        "Architectures",
        description="The instruction set architecture that the function supports. Architecture is a string array with one of the valid values.",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Canonical architecture (`amd64`, `arm64`) derived from `architectures[0]`. Used by `RESOLVED_IMAGE` to pick the right child image when the Lambda runs a multi-architecture manifest list.",
    )
    masterarn: PropertyRef = PropertyRef(
        "MasterArn",
        description="For Lambda@Edge functions, the ARN of the main function.",
    )
    kmskeyarn: PropertyRef = PropertyRef(
        "KMSKeyArn",
        description="The KMS key that's used to encrypt the function's environment variables. This key is only returned if you've configured a customer managed key.",
    )
    anonymous_access: PropertyRef = PropertyRef(
        "AnonymousAccess",
        description="True if this function has a policy applied to it that allows anonymous access or if it is open to the internet.",
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "AnonymousActions",
        description="List of anonymous internet accessible actions that may be run on the function.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Lambda function is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSLambdaToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLambda`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaToAWSAccountRelProperties = (
        AWSLambdaToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaToPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToPrincipalRel(CartographyRelSchema):
    "Represents a `STS_ASSUMEROLE_ALLOW` relationship from `AWSLambda` to `AWSPrincipal`."

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STS_ASSUMEROLE_ALLOW"
    properties: AWSLambdaToPrincipalRelProperties = AWSLambdaToPrincipalRelProperties()


@dataclass(frozen=True)
class AWSLambdaToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:Function)-[:ASSUMES]->(:PermissionRole).
# The function runs with the permissions of its execution role. The existing
# STS_ASSUMEROLE_ALLOW edge (to the generic AWSPrincipal) is the IAM
# trust-policy view and is kept as a distinct semantic.
class AWSLambdaToRoleAssumesRel(CartographyRelSchema):
    "Represents a `ASSUMES` relationship from `AWSLambda` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: AWSLambdaToRoleAssumesRelProperties = (
        AWSLambdaToRoleAssumesRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToECRImageRel(CartographyRelSchema):
    "Represents a `HAS_IMAGE` relationship from `AWSLambda` to `AWSECRImage`."

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AWSLambdaToECRImageRelProperties = AWSLambdaToECRImageRelProperties()


@dataclass(frozen=True)
class AWSLambdaToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToGitLabContainerImageRel(CartographyRelSchema):
    "Represents a `HAS_IMAGE` relationship from `AWSLambda` to `GitLabContainerImage`."

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AWSLambdaToGitLabContainerImageRelProperties = (
        AWSLambdaToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaToGCPArtifactRegistryImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToGCPArtifactRegistryImageRel(CartographyRelSchema):
    "Represents a `HAS_IMAGE` relationship from `AWSLambda` to `GCPArtifactRegistryImage`."

    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AWSLambdaToGCPArtifactRegistryImageRelProperties = (
        AWSLambdaToGCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaToGitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToGitHubContainerImageRel(CartographyRelSchema):
    "Represents a `HAS_IMAGE` relationship from `AWSLambda` to `GitHubContainerImage`."

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AWSLambdaToGitHubContainerImageRelProperties = (
        AWSLambdaToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaSchema(CartographyNodeSchema):
    "Represents an `AWSLambda` node in the AWS graph."

    label: str = "AWSLambda"
    properties: AWSLambdaNodeProperties = AWSLambdaNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    sub_resource_relationship: AWSLambdaToAWSAccountRel = AWSLambdaToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToPrincipalRel(),
            AWSLambdaToRoleAssumesRel(),
            AWSLambdaToECRImageRel(),
            AWSLambdaToGitLabContainerImageRel(),
            AWSLambdaToGCPArtifactRegistryImageRel(),
            AWSLambdaToGitHubContainerImageRel(),
        ],
    )
