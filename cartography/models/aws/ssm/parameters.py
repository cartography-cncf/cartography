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
class SSMParameterNodeProperties(CartographyNodeProperties):

    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    id: PropertyRef = PropertyRef("ARN")
    name: PropertyRef = PropertyRef("Name")
    description: PropertyRef = PropertyRef("Description")
    type: PropertyRef = PropertyRef("Type")
    keyid: PropertyRef = PropertyRef("KeyId")
    version: PropertyRef = PropertyRef("Version")
    lastmodifieddate: PropertyRef = PropertyRef("LastModifiedDate")
    tier: PropertyRef = PropertyRef("Tier")
    lastmodifieduser: PropertyRef = PropertyRef("LastModifiedUser")
    datatype: PropertyRef = PropertyRef("DataType")
    allowedpattern: PropertyRef = PropertyRef("AllowedPattern") 
    policies_json: PropertyRef = PropertyRef("PoliciesJson")  
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMParameterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)



@dataclass(frozen=True)
class SSMParameterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMParameterToAWSAccountRelRelProperties = (
        SSMParameterToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class SSMParameterToKMSKeyRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class SSMParameterToKMSKeyRel(CartographyRelSchema):
    target_node_label: str = 'AWSKmsKey'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('KeyId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SSMParameterToKMSKeyRelRelProperties = SSMParameterToKMSKeyRelRelProperties()


@dataclass(frozen=True)
class SSMParameterSchema(CartographyNodeSchema):

    label: str = "SSMParameter"
    properties: SSMParameterNodeProperties = SSMParameterNodeProperties()
    sub_resource_relationship: SSMParameterToAWSAccountRel = (
        SSMParameterToAWSAccountRel()
    )

    other_relationships: OtherRelationships = OtherRelationships( 
        [ 
            SSMParameterToKMSKeyRel(),
        ],
    )
