import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureSecurityAssessmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    remediation_description: PropertyRef = PropertyRef("remediation_description")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToAssessmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToAssessmentRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSubscriptionToAssessmentRelProperties = (
        AzureSubscriptionToAssessmentRelProperties()
    )


@dataclass(frozen=True)
# (:AzureSecurityAssessment)<-[:HAS_ASSESSMENT]-(:AzureSubscription) - Backwards compatibility
class AzureSubscriptionToAssessmentDeprecatedRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ASSESSMENT"
    properties: AzureSubscriptionToAssessmentRelProperties = (
        AzureSubscriptionToAssessmentRelProperties()
    )


@dataclass(frozen=True)
class AzureSecurityAssessmentSchema(CartographyNodeSchema):
    label: str = "AzureSecurityAssessment"
    properties: AzureSecurityAssessmentProperties = AzureSecurityAssessmentProperties()
    sub_resource_relationship: AzureSubscriptionToAssessmentRel = (
        AzureSubscriptionToAssessmentRel()
    )
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[AzureSubscriptionToAssessmentDeprecatedRel()],
    )
