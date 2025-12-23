from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSBackupVaultNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("BackupVaultArn")
    name: PropertyRef = PropertyRef("BackupVaultName")
    arn: PropertyRef = PropertyRef("BackupVaultArn")
    creation_date: PropertyRef = PropertyRef("CreationDate")
    encryption_key_arn: PropertyRef = PropertyRef("EncryptionKeyArn")
    creator_request_id: PropertyRef = PropertyRef("CreatorRequestId")
    number_of_recovery_points: PropertyRef = PropertyRef("NumberOfRecoveryPoints")
    locked: PropertyRef = PropertyRef("Locked")
    min_retention_days: PropertyRef = PropertyRef("MinRetentionDays")
    max_retention_days: PropertyRef = PropertyRef("MaxRetentionDays")
    lock_date: PropertyRef = PropertyRef("LockDate")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupVaultToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupVaultToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBackupVaultToAWSAccountRelProperties = (
        AWSBackupVaultToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBackupVaultSchema(CartographyNodeSchema):
    label: str = "AWSBackupVault"
    properties: AWSBackupVaultNodeProperties = AWSBackupVaultNodeProperties()
    sub_resource_relationship: AWSBackupVaultToAWSAccountRel = (
        AWSBackupVaultToAWSAccountRel()
    )
