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
class EBSSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SnapshotId")
    snapshotid: PropertyRef = PropertyRef("SnapshotId", extra_index=True)
    description: PropertyRef = PropertyRef("Description")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    progress: PropertyRef = PropertyRef("Progress")
    starttime: PropertyRef = PropertyRef("StartTime")
    state: PropertyRef = PropertyRef("State")
    statemessage: PropertyRef = PropertyRef("StateMessage")
    volumeid: PropertyRef = PropertyRef("VolumeId")
    volumesize: PropertyRef = PropertyRef("VolumeSize")
    outpostarn: PropertyRef = PropertyRef("OutpostArn")
    dataencryptionkeyid: PropertyRef = PropertyRef("DataEncryptionKeyId")
    kmskeyid: PropertyRef = PropertyRef("KmsKeyId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSSnapshotToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSSnapshotToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EBSSnapshotToAWSAccountRelProperties = (
        EBSSnapshotToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EBSSnapshotSchema(CartographyNodeSchema):
    label: str = "EBSSnapshot"
    properties: EBSSnapshotNodeProperties = EBSSnapshotNodeProperties()
    sub_resource_relationship: EBSSnapshotToAWSAccountRel = EBSSnapshotToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([])
