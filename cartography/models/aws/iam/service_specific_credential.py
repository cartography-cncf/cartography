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
class ServiceSpecificCredentialNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("service_specific_credential_id")
    service_specific_credential_id: PropertyRef = PropertyRef("service_specific_credential_id", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM service-specific credentials
    service_name: PropertyRef = PropertyRef("service_name")
    service_user_name: PropertyRef = PropertyRef("service_user_name")
    status: PropertyRef = PropertyRef("status")
    createdate: PropertyRef = PropertyRef("createdate")


@dataclass(frozen=True)
class AWSUserToServiceSpecificCredentialRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToServiceSpecificCredentialRel(CartographyRelSchema):
    target_node_label: str = "ServiceSpecificCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_specific_credential_id": PropertyRef("service_specific_credential_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SERVICE_SPECIFIC_CREDENTIAL"
    properties: AWSUserToServiceSpecificCredentialRelProperties = (
        AWSUserToServiceSpecificCredentialRelProperties()
    )


@dataclass(frozen=True)
class ServiceSpecificCredentialToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ServiceSpecificCredentialToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVICE_SPECIFIC_CREDENTIAL"
    properties: ServiceSpecificCredentialToAWSUserRelProperties = (
        ServiceSpecificCredentialToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class ServiceSpecificCredentialToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ServiceSpecificCredentialToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ServiceSpecificCredentialToAWSAccountRelProperties = (
        ServiceSpecificCredentialToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ServiceSpecificCredentialSchema(CartographyNodeSchema):
    label: str = "ServiceSpecificCredential"
    properties: ServiceSpecificCredentialNodeProperties = ServiceSpecificCredentialNodeProperties()
    sub_resource_relationship: ServiceSpecificCredentialToAWSAccountRel = (
        ServiceSpecificCredentialToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ServiceSpecificCredentialToAWSUserRel(),
        ]
    )