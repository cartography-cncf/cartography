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
    id: PropertyRef = PropertyRef("FunctionArn")
    arn: PropertyRef = PropertyRef("FunctionArn", extra_index=True)
    name: PropertyRef = PropertyRef("FunctionName")
    modifieddate: PropertyRef = PropertyRef("LastModified")
    runtime: PropertyRef = PropertyRef("Runtime")
    description: PropertyRef = PropertyRef("Description")
    timeout: PropertyRef = PropertyRef("Timeout")
    memory: PropertyRef = PropertyRef("MemorySize")
    codesize: PropertyRef = PropertyRef("CodeSize")
    handler: PropertyRef = PropertyRef("Handler")
    version: PropertyRef = PropertyRef("Version")
    tracingconfigmode: PropertyRef = PropertyRef("TracingConfigMode")
    revisionid: PropertyRef = PropertyRef("RevisionId")
    state: PropertyRef = PropertyRef("State")
    statereason: PropertyRef = PropertyRef("StateReason")
    statereasoncode: PropertyRef = PropertyRef("StateReasonCode")
    lastupdatestatus: PropertyRef = PropertyRef("LastUpdateStatus")
    lastupdatestatusreason: PropertyRef = PropertyRef("LastUpdateStatusReason")
    lastupdatestatusreasoncode: PropertyRef = PropertyRef("LastUpdateStatusReasonCode")
    packagetype: PropertyRef = PropertyRef("PackageType")
    image_uri: PropertyRef = PropertyRef("image_uri")
    image_digest: PropertyRef = PropertyRef("image_digest")
    signingprofileversionarn: PropertyRef = PropertyRef("SigningProfileVersionArn")
    signingjobarn: PropertyRef = PropertyRef("SigningJobArn")
    codesha256: PropertyRef = PropertyRef("CodeSha256")
    architectures: PropertyRef = PropertyRef("Architectures")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    masterarn: PropertyRef = PropertyRef("MasterArn")
    kmskeyarn: PropertyRef = PropertyRef("KMSKeyArn")
    anonymous_access: PropertyRef = PropertyRef("AnonymousAccess")
    anonymous_actions: PropertyRef = PropertyRef("AnonymousActions")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STS_ASSUMEROLE_ALLOW"
    properties: AWSLambdaToPrincipalRelProperties = AWSLambdaToPrincipalRelProperties()


@dataclass(frozen=True)
class AWSLambdaToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
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
class AWSLambdaToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToGCPArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AWSLambdaToGCPArtifactRegistryContainerImageRelProperties = (
        AWSLambdaToGCPArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaSchema(CartographyNodeSchema):
    label: str = "AWSLambda"
    properties: AWSLambdaNodeProperties = AWSLambdaNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    sub_resource_relationship: AWSLambdaToAWSAccountRel = AWSLambdaToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToPrincipalRel(),
            AWSLambdaToECRImageRel(),
            AWSLambdaToGitLabContainerImageRel(),
            AWSLambdaToGCPArtifactRegistryContainerImageRel(),
        ],
    )
