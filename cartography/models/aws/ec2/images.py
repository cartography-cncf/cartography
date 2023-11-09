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
class EC2ImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('ID')
    imageid: PropertyRef = PropertyRef('ImageId', extra_index=True)
    name: PropertyRef = PropertyRef('Name', extra_index=True)
    creationdate: PropertyRef = PropertyRef('CreationDate')
    architecture: PropertyRef = PropertyRef('Architecture')
    location: PropertyRef = PropertyRef('ImageLocation')
    type: PropertyRef = PropertyRef('ImageType')
    ispublic: PropertyRef = PropertyRef('Public')
    platform: PropertyRef = PropertyRef('Platform')
    platform_details: PropertyRef = PropertyRef('PlatformDetails')
    usageoperation: PropertyRef = PropertyRef('UsageOperation')
    state: PropertyRef = PropertyRef('State')
    description: PropertyRef = PropertyRef('Description')
    enasupport: PropertyRef = PropertyRef('EnaSupport')
    hypervisor: PropertyRef = PropertyRef('Hypervisor')
    rootdevicename: PropertyRef = PropertyRef('RootDeviceName')
    rootdevicetype: PropertyRef = PropertyRef('RootDeviceType')
    virtualizationtype: PropertyRef = PropertyRef('VirtualizationType')
    sriov_net_support: PropertyRef = PropertyRef('SriovNetSupport')
    bootmode: PropertyRef = PropertyRef('BootMode')
    owner: PropertyRef = PropertyRef('OwnerId')
    image_owner_alias: PropertyRef = PropertyRef('ImageOwnerAlias')
    kernel_id: PropertyRef = PropertyRef('KernelId')
    ramdisk_id: PropertyRef = PropertyRef('RamdiskId')
    region: PropertyRef = PropertyRef('Region')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ImageToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ImageToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2ImageToAwsAccountRelProperties = EC2ImageToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2ImageSchema(CartographyNodeSchema):
    label: str = 'EC2Image'
    properties: EC2ImageNodeProperties = EC2ImageNodeProperties()
    sub_resource_relationship: EC2ImageToAWSAccount = EC2ImageToAWSAccount()
