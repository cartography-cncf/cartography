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
class KMSKeyNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS KMS Key
    """

    id: PropertyRef = PropertyRef("KeyId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    key_id: PropertyRef = PropertyRef("KeyId", extra_index=True)
    description: PropertyRef = PropertyRef("Description")

    # Key configuration properties
    enabled: PropertyRef = PropertyRef("Enabled")
    key_state: PropertyRef = PropertyRef("KeyState")
    key_usage: PropertyRef = PropertyRef("KeyUsage")
    key_manager: PropertyRef = PropertyRef("KeyManager")
    origin: PropertyRef = PropertyRef("Origin")

    # Date properties (will be converted to epoch timestamps)
    creation_date: PropertyRef = PropertyRef("CreationDate")
    deletion_date: PropertyRef = PropertyRef("DeletionDate")
    valid_to: PropertyRef = PropertyRef("ValidTo")

    # Key store properties
    custom_key_store_id: PropertyRef = PropertyRef("CustomKeyStoreId")
    cloud_hsm_cluster_id: PropertyRef = PropertyRef("CloudHsmClusterId")
    expiration_model: PropertyRef = PropertyRef("ExpirationModel")

    # Key spec and algorithms
    customer_master_key_spec: PropertyRef = PropertyRef("CustomerMasterKeySpec")
    encryption_algorithms: PropertyRef = PropertyRef("EncryptionAlgorithms")
    signing_algorithms: PropertyRef = PropertyRef("SigningAlgorithms")

    # Policy analysis properties
    anonymous_access: PropertyRef = PropertyRef("anonymous_access")
    anonymous_actions: PropertyRef = PropertyRef("anonymous_actions")

    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSKeyRelProperties(CartographyRelProperties):
    """
    Properties for relationships between KMSKey and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSKeyToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between KMSKey and AWS Account
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KMSKeyRelProperties = KMSKeyRelProperties()


@dataclass(frozen=True)
class KMSKeySchema(CartographyNodeSchema):
    """
    Schema for AWS KMS Key
    """

    label: str = "KMSKey"
    properties: KMSKeyNodeProperties = KMSKeyNodeProperties()
    sub_resource_relationship: KMSKeyToAWSAccountRel = KMSKeyToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([])
