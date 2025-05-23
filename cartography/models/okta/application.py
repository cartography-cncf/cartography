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
class OktaApplicationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    label: PropertyRef = PropertyRef("label")
    created: PropertyRef = PropertyRef("created")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")
    status: PropertyRef = PropertyRef("status")
    activated: PropertyRef = PropertyRef("activated")
    features: PropertyRef = PropertyRef("features")
    sign_on_mode: PropertyRef = PropertyRef("sign_on_mode")


@dataclass(frozen=True)
class OktaApplicationToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)-[:APPLICATION]->(:OktaApplication)
class OktaApplicationToUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "APPLICATION"
    properties: OktaApplicationToUserProperties = OktaApplicationToUserProperties()


@dataclass(frozen=True)
class OktaApplicationToGroupProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaGroup)-[:APPLICATION]->(:OktaApplication)
class OktaApplicationToGroupRel(CartographyRelSchema):
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("groups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "APPLICATION"
    properties: OktaApplicationToGroupProperties = OktaApplicationToGroupProperties()


@dataclass(frozen=True)
class OktaApplicationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaApplication)
class OktaApplicationToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaApplicationToOrganizationRelProperties = (
        OktaApplicationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationSchema(CartographyNodeSchema):
    label: str = "OktaApplication"
    properties: OktaApplicationProperties = OktaApplicationProperties()
    sub_resource_relationship: OktaApplicationToOrganizationRel = (
        OktaApplicationToOrganizationRel()
    )
    other_relationsips: OtherRelationships = OtherRelationships(
        [
            OktaApplicationToUserRel(),
            OktaApplicationToGroupRel(),
        ]
    )


# WIP: reply_uri
"""
    MATCH (app:OktaApplication{id: $APP_ID})
    WITH app
    UNWIND $URL_LIST as url_list
    MERGE (uri:ReplyUri{id: url_list})
    ON CREATE SET uri.firstseen = timestamp()
    SET uri.uri = url_list,
    uri.lastupdated = $okta_update_tag
    WITH app, uri
    MERGE (uri)<-[r:REPLYURI]-(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """
