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
class DynamoDBSSEDescriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sse_status: PropertyRef = PropertyRef("SSEStatus", extra_index=True)
    sse_type: PropertyRef = PropertyRef("SSEType")
    kms_master_key_arn: PropertyRef = PropertyRef("KMSMasterKeyArn")


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBSSEDescriptionToAWSAccountRelProperties = (
        DynamoDBSSEDescriptionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToTableRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SSE"
    properties: DynamoDBSSEDescriptionToTableRelProperties = (
        DynamoDBSSEDescriptionToTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBSSEDescriptionToKMSKeyRel(CartographyRelSchema):
    """
    Relationship to KMSKey. Only created when SSEType is "KMS" and KMSMasterKeyArn exists.
    """

    target_node_label: str = "KMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("KMSMasterKeyArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_KMS_KEY"
    properties: DynamoDBSSEDescriptionToKMSKeyRelProperties = (
        DynamoDBSSEDescriptionToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBSSEDescriptionSchema(CartographyNodeSchema):
    label: str = "DynamoDBSSEDescription"
    properties: DynamoDBSSEDescriptionNodeProperties = (
        DynamoDBSSEDescriptionNodeProperties()
    )
    sub_resource_relationship: DynamoDBSSEDescriptionToAWSAccountRel = (
        DynamoDBSSEDescriptionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBSSEDescriptionToTableRel(),
            DynamoDBSSEDescriptionToKMSKeyRel(),
        ]
    )
