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
class KMSAliasNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS KMS Alias
    """

    id: PropertyRef = PropertyRef("AliasArn")
    arn: PropertyRef = PropertyRef("AliasArn", extra_index=True)
    alias_name: PropertyRef = PropertyRef("AliasName", extra_index=True)
    target_key_id: PropertyRef = PropertyRef("TargetKeyId")

    # Date properties (will be converted to epoch timestamps)
    creation_date: PropertyRef = PropertyRef("CreationDate")
    last_updated_date: PropertyRef = PropertyRef("LastUpdatedDate")

    # Standard cartography properties
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSAliasRelProperties(CartographyRelProperties):
    """
    Properties for relationships between KMS Alias and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSAliasToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between KMS Alias and AWS Account
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KMSAliasRelProperties = KMSAliasRelProperties()


@dataclass(frozen=True)
class KMSAliasToKMSKeyRel(CartographyRelSchema):
    """
    Relationship between KMS Alias and its associated KMS Key
    """

    target_node_label: str = "KMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TargetKeyId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "KNOWN_AS"
    properties: KMSAliasRelProperties = KMSAliasRelProperties()


@dataclass(frozen=True)
class KMSAliasSchema(CartographyNodeSchema):
    """
    Schema for AWS KMS Alias
    """

    label: str = "KMSAlias"
    properties: KMSAliasNodeProperties = KMSAliasNodeProperties()
    sub_resource_relationship: KMSAliasToAWSAccountRel = KMSAliasToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KMSAliasToKMSKeyRel(),
        ],
    )
