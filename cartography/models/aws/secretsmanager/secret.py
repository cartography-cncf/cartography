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
class SecretsManagerSecretNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Secrets Manager Secret
    """

    id: PropertyRef = PropertyRef("ARN", description="The arn of the secret.")
    arn: PropertyRef = PropertyRef(
        "ARN",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSSecretsManagerSecret` node.",
    )
    name: PropertyRef = PropertyRef(
        "Name",
        extra_index=True,
        description="The friendly name of the secret. You can use forward slashes in the name to represent a path hierarchy. For example, /prod/databases/dbserver1 could represent the secret for a server named dbserver1 in the folder databases in the folder prod.",
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The user-provided description of the secret."
    )

    # Rotation properties
    rotation_enabled: PropertyRef = PropertyRef(
        "RotationEnabled",
        description="Indicates whether automatic, scheduled rotation is enabled for this secret.",
    )
    rotation_lambda_arn: PropertyRef = PropertyRef(
        "RotationLambdaARN",
        description="The ARN of an AWS Lambda function invoked by Secrets Manager to rotate and expire the secret either automatically per the schedule or manually by a call to RotateSecret.",
    )
    rotation_rules_automatically_after_days: PropertyRef = PropertyRef(
        "RotationRulesAutomaticallyAfterDays",
        description="Specifies the number of days between automatic scheduled rotations of the secret.",
    )

    # Date properties (will be converted to epoch timestamps)
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="The date and time when a secret was created."
    )
    last_rotated_date: PropertyRef = PropertyRef(
        "LastRotatedDate",
        description="The most recent date and time that the Secrets Manager rotation process was successfully completed. This value is null if the secret hasn't ever rotated.",
    )
    last_changed_date: PropertyRef = PropertyRef(
        "LastChangedDate",
        description="The last date and time that this secret was modified in any way.",
    )
    last_accessed_date: PropertyRef = PropertyRef(
        "LastAccessedDate",
        description="The last date that this secret was accessed. This value is truncated to midnight of the date and therefore shows only the date, not the time.",
    )
    deleted_date: PropertyRef = PropertyRef(
        "DeletedDate",
        description="The date and time the deletion of the secret occurred. Not present on active secrets. The secret can be recovered until the number of days in the recovery window has passed, as specified in the RecoveryWindowInDays parameter of the DeleteSecret operation.",
    )

    # Other properties
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="The ARN or alias of the AWS KMS customer master key (CMK) used to encrypt the SecretString and SecretBinary fields in each version of the secret. If you don't provide a key, then Secrets Manager defaults to encrypting the secret fields with the default KMS CMK, the key named awssecretsmanager, for this account.",
    )
    owning_service: PropertyRef = PropertyRef(
        "OwningService",
        description="Returns the name of the service that created the secret.",
    )
    primary_region: PropertyRef = PropertyRef(
        "PrimaryRegion",
        description="The Region where Secrets Manager originated the secret.",
    )

    # Standard cartography properties
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSSecretsManagerSecret` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


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
    Only created when kms_key_id is present
    """

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("KmsKeyId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SecretsManagerSecretRelProperties = SecretsManagerSecretRelProperties()


@dataclass(frozen=True)
class SecretsManagerSecretSchema(CartographyNodeSchema):
    """
    Schema for AWS Secrets Manager Secret
    """

    label: str = "AWSSecretsManagerSecret"
    # DEPRECATED: legacy SecretsManagerSecret node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "SecretsManagerSecret",
            "Secret",
        ]
    )  # Secret label is used for ontology mapping
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
