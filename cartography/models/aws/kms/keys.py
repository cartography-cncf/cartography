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
class KMSKeyNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS KMS Key
    """

    id: PropertyRef = PropertyRef("KeyId", description="The KeyId of the key")
    arn: PropertyRef = PropertyRef(
        "Arn", extra_index=True, description="The ARN of the key"
    )
    key_id: PropertyRef = PropertyRef(
        "KeyId", extra_index=True, description="The KeyId of the key"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the key"
    )

    # Key configuration properties
    enabled: PropertyRef = PropertyRef(
        "Enabled", description="Whether the key is enabled"
    )
    key_state: PropertyRef = PropertyRef(
        "KeyState",
        description="The current state of the key (e.g., Enabled, Disabled, PendingDeletion)",
    )
    key_usage: PropertyRef = PropertyRef(
        "KeyUsage",
        description="The permitted use of the key (e.g., ENCRYPT_DECRYPT, SIGN_VERIFY)",
    )
    key_manager: PropertyRef = PropertyRef(
        "KeyManager", description="The manager of the key (AWS or CUSTOMER)"
    )
    origin: PropertyRef = PropertyRef(
        "Origin",
        description="The source of the key material (AWS_KMS, EXTERNAL, AWS_CLOUDHSM)",
    )

    # Date properties (will be converted to epoch timestamps)
    creation_date: PropertyRef = PropertyRef(
        "CreationDate", description="The date the key was created"
    )
    deletion_date: PropertyRef = PropertyRef(
        "DeletionDate", description="The date the key is scheduled for deletion"
    )
    valid_to: PropertyRef = PropertyRef(
        "ValidTo", description="The expiration date for the key material"
    )

    # Key store properties
    custom_key_store_id: PropertyRef = PropertyRef(
        "CustomKeyStoreId",
        description="The ID of the custom key store that contains the key",
    )
    cloud_hsm_cluster_id: PropertyRef = PropertyRef(
        "CloudHsmClusterId",
        description="The cluster ID of the AWS CloudHSM cluster that contains the key material",
    )
    expiration_model: PropertyRef = PropertyRef(
        "ExpirationModel", description="Specifies whether key material expires"
    )

    # Key spec and algorithms
    customer_master_key_spec: PropertyRef = PropertyRef(
        "CustomerMasterKeySpec", description="The type of key material in the CMK"
    )
    encryption_algorithms: PropertyRef = PropertyRef(
        "EncryptionAlgorithms",
        description="The encryption algorithms that AWS KMS supports for this key",
    )
    signing_algorithms: PropertyRef = PropertyRef(
        "SigningAlgorithms",
        description="The signing algorithms that AWS KMS supports for this key",
    )

    # Policy analysis properties
    anonymous_access: PropertyRef = PropertyRef(
        "anonymous_access",
        description="True if this key has a policy applied to it that allows anonymous access or if it is open to the internet.",
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "anonymous_actions",
        description="List of anonymous internet accessible actions that may be run on the key.",
    )

    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region where key is created"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated by Cartography",
    )


@dataclass(frozen=True)
class KMSKeyRelProperties(CartographyRelProperties):
    """
    Properties for relationships between AWSKMSKey and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSKeyToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between AWSKMSKey and AWS Account
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

    label: str = "AWSKMSKey"
    # DEPRECATED: legacy KMSKey node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["KMSKey", "EncryptionKey"])
    properties: KMSKeyNodeProperties = KMSKeyNodeProperties()
    sub_resource_relationship: KMSKeyToAWSAccountRel = KMSKeyToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([])
