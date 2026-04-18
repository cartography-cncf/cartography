from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraUserToAWSSSOUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraUserToAWSSSOUserMatchLink(CartographyRelSchema):
    target_node_label: str = "AWSSSOUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "user_name": PropertyRef("aws_user_name"),
            "identity_store_id": PropertyRef("identity_store_id"),
        }
    )
    source_node_label: str = "EntraUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "user_principal_name": PropertyRef("entra_user_principal_name"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_SIGN_ON_TO"
    properties: EntraUserToAWSSSOUserRelProperties = (
        EntraUserToAWSSSOUserRelProperties()
    )
