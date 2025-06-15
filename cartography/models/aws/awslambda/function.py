from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    OtherRelationships,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class LambdaFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("FunctionArn", extra_index=True)
    arn: PropertyRef = PropertyRef("FunctionArn")
    name: PropertyRef = PropertyRef("FunctionName")
    modifieddate: PropertyRef = PropertyRef("LastModified")
    runtime: PropertyRef = PropertyRef("Runtime")
    description: PropertyRef = PropertyRef("Description")
    timeout: PropertyRef = PropertyRef("Timeout")
    memory: PropertyRef = PropertyRef("MemorySize")
    codesize: PropertyRef = PropertyRef("CodeSize")
    handler: PropertyRef = PropertyRef("Handler")
    version: PropertyRef = PropertyRef("Version")
    tracingconfigmode: PropertyRef = PropertyRef("TracingConfig.Mode")
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
    role: PropertyRef = PropertyRef("Role")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaFunctionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaFunctionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("AWS_ID", set_in_kwargs=True)})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LambdaFunctionToAWSAccountRelProperties = LambdaFunctionToAWSAccountRelProperties()


@dataclass(frozen=True)
class LambdaFunctionToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaFunctionToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"arn": PropertyRef("Role")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STS_ASSUME_ROLE_ALLOW"
    properties: LambdaFunctionToAWSPrincipalRelProperties = LambdaFunctionToAWSPrincipalRelProperties()


@dataclass(frozen=True)
class LambdaFunctionSchema(CartographyNodeSchema):
    label: str = "AWSLambda"
    properties: LambdaFunctionNodeProperties = LambdaFunctionNodeProperties()
    sub_resource_relationship: LambdaFunctionToAWSAccountRel = LambdaFunctionToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([LambdaFunctionToAWSPrincipalRel()])
