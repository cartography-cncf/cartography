from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2ImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ID", description="The ID of the AMI.")
    imageid: PropertyRef = PropertyRef(
        "ImageId",
        extra_index=True,
        description="Identifier of the imageid linked to this `AWSEC2Image` node.",
    )
    name: PropertyRef = PropertyRef(
        "Name",
        extra_index=True,
        description="The name of the AMI that was provided during image creation.",
    )
    creationdate: PropertyRef = PropertyRef(
        "CreationDate", description="The date and time the image was created."
    )
    architecture: PropertyRef = PropertyRef(
        "Architecture", description="The architecture of the image."
    )
    location: PropertyRef = PropertyRef(
        "ImageLocation", description="The location of the AMI."
    )
    type: PropertyRef = PropertyRef("ImageType", description="The type of image.")
    ispublic: PropertyRef = PropertyRef(
        "Public",
        description="Indicates whether the image has public launch permissions.",
    )
    platform: PropertyRef = PropertyRef(
        "Platform",
        description="This value is set to `windows` for Windows AMIs; otherwise, it is blank.",
    )
    platform_details: PropertyRef = PropertyRef(
        "PlatformDetails",
        description="Operating-system platform details for the machine image.",
    )
    usageoperation: PropertyRef = PropertyRef(
        "UsageOperation",
        description="The operation of the Amazon EC2 instance and the billing code that is associated with the AMI.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The current state of the AMI."
    )
    description: PropertyRef = PropertyRef(
        "Description",
        description="The description of the AMI that was provided during image creation.",
    )
    enasupport: PropertyRef = PropertyRef(
        "EnaSupport",
        description="Specifies whether enhanced networking with ENA is enabled.",
    )
    hypervisor: PropertyRef = PropertyRef(
        "Hypervisor", description="The hypervisor type of the image."
    )
    rootdevicename: PropertyRef = PropertyRef(
        "RootDeviceName",
        description="The device name of the root device volume (for example, `/dev/sda1` ).",
    )
    rootdevicetype: PropertyRef = PropertyRef(
        "RootDeviceType", description="The type of root device used by the AMI."
    )
    virtualizationtype: PropertyRef = PropertyRef(
        "VirtualizationType", description="The type of virtualization of the AMI."
    )
    sriov_net_support: PropertyRef = PropertyRef(
        "SriovNetSupport",
        description="SR-IOV networking capability advertised by the machine image.",
    )
    bootmode: PropertyRef = PropertyRef(
        "BootMode", description="The boot mode of the image."
    )
    owner: PropertyRef = PropertyRef(
        "OwnerId", description="AWS account ID of the machine image owner."
    )
    image_owner_alias: PropertyRef = PropertyRef(
        "ImageOwnerAlias",
        description="AWS-provided alias for the machine image owner.",
    )
    kernel_id: PropertyRef = PropertyRef(
        "KernelId",
        description="Identifier of the kernel linked to this `AWSEC2Image` node.",
    )
    ramdisk_id: PropertyRef = PropertyRef(
        "RamdiskId",
        description="Identifier of the ramdisk linked to this `AWSEC2Image` node.",
    )
    region: PropertyRef = PropertyRef("Region", description="The region of the image.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2ImageToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ImageToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Image`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2ImageToAWSAccountRelRelProperties = (
        EC2ImageToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2ImageSchema(CartographyNodeSchema):
    "Represents an `AWSEC2Image` node in the AWS graph."

    label: str = "AWSEC2Image"
    # DEPRECATED: legacy EC2Image node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Image"])
    properties: EC2ImageNodeProperties = EC2ImageNodeProperties()
    sub_resource_relationship: EC2ImageToAWSAccountRel = EC2ImageToAWSAccountRel()
