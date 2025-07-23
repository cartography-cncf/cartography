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
class AWSFederatedNonlocalPrincipalNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM federated principals
    type: PropertyRef = PropertyRef("type")


@dataclass(frozen=True)
class AWSFederatedNonlocalPrincipalToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSFederatedNonlocalPrincipalToAWSAccountRel(CartographyRelSchema):
    """
    This federated principal belongs to a different AWS account than the
    current AWS account being synced in cartography/intel/aws/iam.py.
    (This is rare but possible.)
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("other_account_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSFederatedNonlocalPrincipalToAWSAccountRelProperties = (
        AWSFederatedNonlocalPrincipalToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSFederatedNonlocalPrincipalSchema(CartographyNodeSchema):
    """
    A federated principal as discovered from a role's trust relationship.
    """

    label: str = "AWSFederatedNonlocalPrincipal"
    properties: AWSFederatedNonlocalPrincipalNodeProperties = (
        AWSFederatedNonlocalPrincipalNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSFederatedNonlocalPrincipalToAWSAccountRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])
