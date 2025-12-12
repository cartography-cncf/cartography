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
    signingprofileversionarn: PropertyRef = PropertyRef("SigningProfileVersionArn")
    signingjobarn: PropertyRef = PropertyRef("SigningJobArn")
    codesha256: PropertyRef = PropertyRef("CodeSha256")
    architectures: PropertyRef = PropertyRef("Architectures")
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
class AWSLambdaSchema(CartographyNodeSchema):
    label: str = "AWSLambda"
    properties: AWSLambdaNodeProperties = AWSLambdaNodeProperties()
    sub_resource_relationship: AWSLambdaToAWSAccountRel = AWSLambdaToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToPrincipalRel(),
        ],
    )
