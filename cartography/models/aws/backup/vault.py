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
class AWSBackupBackupVaultNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "BackupVaultArn",
        description="The Amazon Resource Name (ARN) of the backup vault",
    )
    arn: PropertyRef = PropertyRef(
        "BackupVaultArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the backup vault",
    )
    name: PropertyRef = PropertyRef(
        "BackupVaultName", description="The name of the backup vault"
    )
    encryption_key_arn: PropertyRef = PropertyRef(
        "EncryptionKeyArn",
        description="The ARN of the KMS key that encrypts the backup vault",
    )
    creation_date: PropertyRef = PropertyRef(
        "CreationDate", description="The time the backup vault was created"
    )
    number_of_recovery_points: PropertyRef = PropertyRef(
        "NumberOfRecoveryPoints",
        description="The number of recovery points stored in the backup vault",
    )
    locked: PropertyRef = PropertyRef(
        "Locked", description="Whether AWS Backup Vault Lock is enabled on the vault"
    )
    min_retention_days: PropertyRef = PropertyRef(
        "MinRetentionDays",
        description="The vault lock minimum retention period, in days",
    )
    max_retention_days: PropertyRef = PropertyRef(
        "MaxRetentionDays",
        description="The vault lock maximum retention period, in days",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region of the backup vault",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupBackupVaultToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupBackupVaultToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBackupBackupVaultToAWSAccountRelProperties = (
        AWSBackupBackupVaultToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBackupBackupVaultToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupBackupVaultToKMSKeyRel(CartographyRelSchema):
    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("EncryptionKeyArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: AWSBackupBackupVaultToKMSKeyRelProperties = (
        AWSBackupBackupVaultToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class AWSBackupBackupVaultSchema(CartographyNodeSchema):
    """Representation of an AWS [Backup vault](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_BackupVaultListMember.html)."""

    label: str = "AWSBackupBackupVault"
    properties: AWSBackupBackupVaultNodeProperties = (
        AWSBackupBackupVaultNodeProperties()
    )
    sub_resource_relationship: AWSBackupBackupVaultToAWSAccountRel = (
        AWSBackupBackupVaultToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBackupBackupVaultToKMSKeyRel(),
        ],
    )
