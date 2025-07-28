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
class RDSSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DBSnapshotArn")
    arn: PropertyRef = PropertyRef("DBSnapshotArn", extra_index=True)
    db_snapshot_identifier: PropertyRef = PropertyRef(
        "DBSnapshotIdentifier", extra_index=True
    )
    db_instance_identifier: PropertyRef = PropertyRef("DBInstanceIdentifier")
    snapshot_create_time: PropertyRef = PropertyRef("SnapshotCreateTime")
    engine: PropertyRef = PropertyRef("Engine")
    engine_version: PropertyRef = PropertyRef("EngineVersion")
    allocated_storage: PropertyRef = PropertyRef("AllocatedStorage")
    status: PropertyRef = PropertyRef("Status")
    port: PropertyRef = PropertyRef("Port")
    availability_zone: PropertyRef = PropertyRef("AvailabilityZone")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    instance_create_time: PropertyRef = PropertyRef("InstanceCreateTime")
    master_username: PropertyRef = PropertyRef("MasterUsername")
    license_model: PropertyRef = PropertyRef("LicenseModel")
    snapshot_type: PropertyRef = PropertyRef("SnapshotType")
    iops: PropertyRef = PropertyRef("Iops")
    option_group_name: PropertyRef = PropertyRef("OptionGroupName")
    percent_progress: PropertyRef = PropertyRef("PercentProgress")
    source_region: PropertyRef = PropertyRef("SourceRegion")
    source_db_snapshot_identifier: PropertyRef = PropertyRef(
        "SourceDBSnapshotIdentifier"
    )
    storage_type: PropertyRef = PropertyRef("StorageType")
    tde_credential_arn: PropertyRef = PropertyRef("TdeCredentialArn")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    timezone: PropertyRef = PropertyRef("Timezone")
    iam_database_authentication_enabled: PropertyRef = PropertyRef(
        "IAMDatabaseAuthenticationEnabled"
    )
    processor_features: PropertyRef = PropertyRef("ProcessorFeatures")
    dbi_resource_id: PropertyRef = PropertyRef("DbiResourceId")
    original_snapshot_create_time: PropertyRef = PropertyRef(
        "OriginalSnapshotCreateTime"
    )
    snapshot_database_time: PropertyRef = PropertyRef("SnapshotDatabaseTime")
    snapshot_target: PropertyRef = PropertyRef("SnapshotTarget")
    storage_throughput: PropertyRef = PropertyRef("StorageThroughput")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSSnapshotToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSSnapshotToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "RDSInstance"
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
    label: str = "RDSSnapshot"
    properties: RDSSnapshotNodeProperties = RDSSnapshotNodeProperties()
    sub_resource_relationship: RDSSnapshotToAWSAccountRel = RDSSnapshotToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RDSSnapshotToRDSInstanceRel(),
        ]
    )
