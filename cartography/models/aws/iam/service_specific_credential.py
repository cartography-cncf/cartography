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
class AWSServiceSpecificCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("service_specific_credential_id")
    service_specific_credential_id: PropertyRef = PropertyRef(
        "service_specific_credential_id",
        extra_index=True,
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    service_name: PropertyRef = PropertyRef("service_name")
    service_user_name: PropertyRef = PropertyRef("service_user_name")
    status: PropertyRef = PropertyRef("status")
    username: PropertyRef = PropertyRef("username")
    createdate: PropertyRef = PropertyRef("createdate")
    createdate_dt: PropertyRef = PropertyRef("createdate_dt")


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("user_arn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVICE_SPECIFIC_CREDENTIAL"
    properties: AWSServiceSpecificCredentialToAWSUserRelProperties = (
        AWSServiceSpecificCredentialToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSServiceSpecificCredentialToAWSAccountRelProperties = (
        AWSServiceSpecificCredentialToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceSpecificCredentialSchema(CartographyNodeSchema):
    label: str = "AWSServiceSpecificCredential"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: AWSServiceSpecificCredentialNodeProperties = (
        AWSServiceSpecificCredentialNodeProperties()
    )
    sub_resource_relationship: AWSServiceSpecificCredentialToAWSAccountRel = (
        AWSServiceSpecificCredentialToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSServiceSpecificCredentialToAWSUserRel()],
    )
