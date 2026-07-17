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
class EKSAccessEntryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("accessEntryArn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_name: PropertyRef = PropertyRef("clusterName")
    principal_arn: PropertyRef = PropertyRef("principalArn", extra_index=True)
    username: PropertyRef = PropertyRef("username")
    type: PropertyRef = PropertyRef("type")
    kubernetes_groups: PropertyRef = PropertyRef("kubernetesGroups")
    created_at: PropertyRef = PropertyRef("createdAt")
    modified_at: PropertyRef = PropertyRef("modifiedAt")


@dataclass(frozen=True)
class EKSAccessEntryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EKSAccessEntryToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EKSAccessEntryToAWSAccountRelProperties = (
        EKSAccessEntryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EKSClusterToAccessEntryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EKSClusterToAccessEntryRel(CartographyRelSchema):
    target_node_label: str = "AWSEKSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("cluster_arn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ACCESS_ENTRY"
    properties: EKSClusterToAccessEntryRelProperties = (
        EKSClusterToAccessEntryRelProperties()
    )


@dataclass(frozen=True)
class AWSPrincipalToEKSAccessEntryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPrincipalToEKSAccessEntryRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("principalArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GRANTED_ACCESS_TO"
    properties: AWSPrincipalToEKSAccessEntryRelProperties = (
        AWSPrincipalToEKSAccessEntryRelProperties()
    )


@dataclass(frozen=True)
class EKSAccessEntrySchema(CartographyNodeSchema):
    label: str = "AWSEKSAccessEntry"
    # DEPRECATED: legacy EKSAccessEntry node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EKSAccessEntry"])
    properties: EKSAccessEntryNodeProperties = EKSAccessEntryNodeProperties()
    sub_resource_relationship: EKSAccessEntryToAWSAccountRel = (
        EKSAccessEntryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EKSClusterToAccessEntryRel(),
            AWSPrincipalToEKSAccessEntryRel(),
        ],
    )
