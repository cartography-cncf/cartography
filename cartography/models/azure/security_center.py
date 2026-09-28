import logging
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
from cartography.models.ontology.labels import SECURITY_ISSUE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureSecurityAssessmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the security assessment.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the security assessment.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Display name of the security assessment.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Explanation of the security issue identified by the assessment.",
    )
    remediation_description: PropertyRef = PropertyRef(
        "remediation_description",
        description="Recommended steps for remediating the security issue.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToAssessmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToAssessmentRel(CartographyRelSchema):
    """An Azure subscription contains the security assessment as a resource."""

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
    """Deprecated compatibility edge linking a subscription to an assessment."""

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
    """A Microsoft Defender for Cloud security assessment."""

    label: str = "AzureSecurityAssessment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    properties: AzureSecurityAssessmentProperties = AzureSecurityAssessmentProperties()
    sub_resource_relationship: AzureSubscriptionToAssessmentRel = (
        AzureSubscriptionToAssessmentRel()
    )
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[AzureSubscriptionToAssessmentDeprecatedRel()],
    )
