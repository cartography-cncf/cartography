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
class RDSSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DBSnapshotArn", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "DBSnapshotArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the DB snapshot.",
    )
    db_snapshot_identifier: PropertyRef = PropertyRef(
        "DBSnapshotIdentifier",
        extra_index=True,
        description="Specifies the identifier for the DB snapshot.",
    )
    ispublic: PropertyRef = PropertyRef(
        "Public",
        description="Whether this `AWSRDSSnapshot` node is publicly accessible.",
    )
    db_instance_identifier: PropertyRef = PropertyRef(
        "DBInstanceIdentifier",
        description="Specifies the DB instance identifier of the DB instance this DB snapshot was created from.",
    )
    snapshot_create_time: PropertyRef = PropertyRef(
        "SnapshotCreateTime",
        description="Specifies when the snapshot was taken in Coordinated Universal Time (UTC). Changes for the copy when the snapshot is copied.",
    )
    engine: PropertyRef = PropertyRef(
        "Engine", description="Specifies the name of the database engine."
    )
    engine_version: PropertyRef = PropertyRef(
        "EngineVersion", description="Specifies the version of the database engine."
    )
    allocated_storage: PropertyRef = PropertyRef(
        "AllocatedStorage",
        description="Specifies the allocated storage size in gibibytes (GiB).",
    )
    status: PropertyRef = PropertyRef(
        "Status", description="Specifies the status of this DB snapshot."
    )
    port: PropertyRef = PropertyRef(
        "Port",
        description="Specifies the port that the database engine was listening on at the time of the snapshot.",
    )
    availability_zone: PropertyRef = PropertyRef(
        "AvailabilityZone",
        description="Specifies the name of the Availability Zone the DB instance was located in at the time of the DB snapshot.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId", description="Provides the VPC ID associated with the DB snapshot."
    )
    instance_create_time: PropertyRef = PropertyRef(
        "InstanceCreateTime",
        description="Specifies the time in Coordinated Universal Time (UTC) when the DB instance, from which the snapshot was taken, was created.",
    )
    master_username: PropertyRef = PropertyRef(
        "MasterUsername",
        description="Provides the master username for the DB snapshot.",
    )
    license_model: PropertyRef = PropertyRef(
        "LicenseModel",
        description="License model information for the restored DB instance.",
    )
    snapshot_type: PropertyRef = PropertyRef(
        "SnapshotType", description="Provides the type of the DB snapshot."
    )
    iops: PropertyRef = PropertyRef(
        "Iops",
        description="Specifies the Provisioned IOPS (I/O operations per second) value of the DB instance at the time of the snapshot.",
    )
    option_group_name: PropertyRef = PropertyRef(
        "OptionGroupName",
        description="Provides the option group name for the DB snapshot.",
    )
    percent_progress: PropertyRef = PropertyRef(
        "PercentProgress",
        description="The percentage of the estimated data that has been transferred.",
    )
    source_region: PropertyRef = PropertyRef(
        "SourceRegion",
        description="The AWS Region that the DB snapshot was created in or copied from.",
    )
    source_db_snapshot_identifier: PropertyRef = PropertyRef(
        "SourceDBSnapshotIdentifier",
        description="The DB snapshot Amazon Resource Name (ARN) that the DB snapshot was copied from. It only has a value in the case of a cross-account or cross-Region copy.",
    )
    storage_type: PropertyRef = PropertyRef(
        "StorageType",
        description="Specifies the storage type associated with DB snapshot.",
    )
    tde_credential_arn: PropertyRef = PropertyRef(
        "TdeCredentialArn",
        description="The ARN from the key store with which to associate the instance for TDE encryption.",
    )
    encrypted: PropertyRef = PropertyRef(
        "Encrypted", description="Specifies whether the DB snapshot is encrypted."
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="If Encrypted is true, the AWS KMS key identifier for the encrypted DB snapshot. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the KMS key.",
    )
    timezone: PropertyRef = PropertyRef(
        "Timezone",
        description="The time zone of the DB snapshot. In most cases, the Timezone element is empty. Timezone content appears only for snapshots taken from Microsoft SQL Server DB instances that were created with a time zone specified.",
    )
    iam_database_authentication_enabled: PropertyRef = PropertyRef(
        "IAMDatabaseAuthenticationEnabled",
        description="True if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled, and otherwise false.",
    )
    processor_features: PropertyRef = PropertyRef(
        "ProcessorFeatures",
        description="The number of CPU cores and the number of threads per core for the DB instance class of the DB instance when the DB snapshot was created.",
    )
    dbi_resource_id: PropertyRef = PropertyRef(
        "DbiResourceId",
        description="The identifier for the source DB instance, which can't be changed and which is unique to an AWS Region.",
    )
    original_snapshot_create_time: PropertyRef = PropertyRef(
        "OriginalSnapshotCreateTime",
        description="Specifies the time of the CreateDBSnapshot operation in Coordinated Universal Time (UTC). Doesn't change when the snapshot is copied.",
    )
    snapshot_database_time: PropertyRef = PropertyRef(
        "SnapshotDatabaseTime",
        description="The timestamp of the most recent transaction applied to the database that you're backing up. Thus, if you restore a snapshot, SnapshotDatabaseTime is the most recent transaction in the restored DB instance. In contrast, originalSnapshotCreateTime specifies the system time that the snapshot completed. If you back up a read replica, you can determine the replica lag by comparing SnapshotDatabaseTime with originalSnapshotCreateTime. For example, if originalSnapshotCreateTime is two hours later than SnapshotDatabaseTime, then the replica lag is two hours.",
    )
    snapshot_target: PropertyRef = PropertyRef(
        "SnapshotTarget",
        description="Specifies where manual snapshots are stored: AWS Outposts or the AWS Region.",
    )
    storage_throughput: PropertyRef = PropertyRef(
        "StorageThroughput",
        description="The storage throughput of the DB snapshot, in mebibytes per second (MiBps).",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region of the snapshot"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class RDSSnapshotToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSSnapshotToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRDSSnapshot`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RDSSnapshotToAWSAccountRelProperties = (
        RDSSnapshotToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RDSSnapshotToRDSInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSSnapshotToRDSInstanceRel(CartographyRelSchema):
    "Represents a `IS_SNAPSHOT_SOURCE` relationship from `AWSRDSSnapshot` to `AWSRDSInstance`."

    target_node_label: str = "AWSRDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_instance_identifier": PropertyRef("DBInstanceIdentifier"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_SNAPSHOT_SOURCE"
    properties: RDSSnapshotToRDSInstanceRelProperties = (
        RDSSnapshotToRDSInstanceRelProperties()
    )


@dataclass(frozen=True)
class RDSSnapshotSchema(CartographyNodeSchema):
    "Represents an `AWSRDSSnapshot` node in the AWS graph."

    label: str = "AWSRDSSnapshot"
    properties: RDSSnapshotNodeProperties = RDSSnapshotNodeProperties()
    # DEPRECATED: legacy RDSSnapshot node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["RDSSnapshot", "Snapshot"])
    sub_resource_relationship: RDSSnapshotToAWSAccountRel = RDSSnapshotToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RDSSnapshotToRDSInstanceRel(),
        ]
    )
