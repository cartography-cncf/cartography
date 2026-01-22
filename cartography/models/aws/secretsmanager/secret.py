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
class SecretsManagerSecretNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Secrets Manager Secret
    """

    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    description: PropertyRef = PropertyRef("Description")

    # Rotation properties
    rotation_enabled: PropertyRef = PropertyRef("RotationEnabled")
    rotation_lambda_arn: PropertyRef = PropertyRef("RotationLambdaARN")
    rotation_rules_automatically_after_days: PropertyRef = PropertyRef(
        "RotationRulesAutomaticallyAfterDays"
    )

    # Date properties (will be converted to epoch timestamps)
    created_date: PropertyRef = PropertyRef("CreatedDate")
    last_rotated_date: PropertyRef = PropertyRef("LastRotatedDate")
    last_changed_date: PropertyRef = PropertyRef("LastChangedDate")
    last_accessed_date: PropertyRef = PropertyRef("LastAccessedDate")
    deleted_date: PropertyRef = PropertyRef("DeletedDate")

    # Other properties
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    owning_service: PropertyRef = PropertyRef("OwningService")
    primary_region: PropertyRef = PropertyRef("PrimaryRegion")

    # Standard cartography properties
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecretsManagerSecretRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecretsManagerSecretToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between Secret and AWS Account
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SecretsManagerSecretRelProperties = SecretsManagerSecretRelProperties()


@dataclass(frozen=True)
class SecretsManagerSecretToKMSKeyRel(CartographyRelSchema):
    """
    Relationship between Secret and its KMS key
    Only created when KmsKeyId is present
    """

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("KmsKeyId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SecretsManagerSecretRelProperties = SecretsManagerSecretRelProperties()


@dataclass(frozen=True)
class SecretsManagerSecretSchema(CartographyNodeSchema):
    """
    Schema for AWS Secrets Manager Secret
    """

    label: str = "SecretsManagerSecret"
    properties: SecretsManagerSecretNodeProperties = (
        SecretsManagerSecretNodeProperties()
    )
    sub_resource_relationship: SecretsManagerSecretToAWSAccountRel = (
        SecretsManagerSecretToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SecretsManagerSecretToKMSKeyRel(),
        ],
    )
