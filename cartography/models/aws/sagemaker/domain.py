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
    id: PropertyRef = PropertyRef("DomainArn")
    arn: PropertyRef = PropertyRef("DomainArn", extra_index=True)
    domain_id: PropertyRef = PropertyRef("DomainId")
    domain_name: PropertyRef = PropertyRef("DomainName")
    status: PropertyRef = PropertyRef("Status")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    url: PropertyRef = PropertyRef("Url")
    home_efs_file_system_id: PropertyRef = PropertyRef("HomeEfsFileSystemId")
    auth_mode: PropertyRef = PropertyRef("AuthMode")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerDomainToAWSAccountRel(CartographyRelSchema):
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
    label: str = "AWSSageMakerDomain"
    properties: AWSSageMakerDomainNodeProperties = AWSSageMakerDomainNodeProperties()
    sub_resource_relationship: AWSSageMakerDomainToAWSAccountRel = (
        AWSSageMakerDomainToAWSAccountRel()
    )
