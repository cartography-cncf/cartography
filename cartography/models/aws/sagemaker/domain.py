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
class AWSSageMakerDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DomainArn", description="The ARN of the Domain")
    arn: PropertyRef = PropertyRef(
        "DomainArn", extra_index=True, description="The ARN of the Domain"
    )
    domain_id: PropertyRef = PropertyRef("DomainId", description="The Domain ID")
    domain_name: PropertyRef = PropertyRef(
        "DomainName", description="The name of the Domain"
    )
    status: PropertyRef = PropertyRef("Status", description="The status of the Domain")
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Domain was created"
    )
    last_modified_time: PropertyRef = PropertyRef(
        "LastModifiedTime", description="When the Domain was last modified"
    )
    url: PropertyRef = PropertyRef("Url", description="URL of the SageMaker domain.")
    home_efs_file_system_id: PropertyRef = PropertyRef(
        "HomeEfsFileSystemId",
        description="Identifier of the home efs file system linked to this `AWSSageMakerDomain` node.",
    )
    auth_mode: PropertyRef = PropertyRef(
        "AuthMode",
        description="Authentication mode used by the SageMaker domain.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Domain exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerDomainToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerDomain`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerDomainToAWSAccountRelProperties = (
        AWSSageMakerDomainToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerDomainSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerDomain` node in the AWS graph."

    label: str = "AWSSageMakerDomain"
    properties: AWSSageMakerDomainNodeProperties = AWSSageMakerDomainNodeProperties()
    sub_resource_relationship: AWSSageMakerDomainToAWSAccountRel = (
        AWSSageMakerDomainToAWSAccountRel()
    )
