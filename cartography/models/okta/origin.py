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
class OktaTrustedOriginNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    created_by: PropertyRef = PropertyRef("created_by", description="Okta created by.")
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    last_updated_by: PropertyRef = PropertyRef(
        "last_updated_by", description="Okta last updated by."
    )
    name: PropertyRef = PropertyRef("name", description="Okta name.")
    origin: PropertyRef = PropertyRef("origin", description="Okta origin.")
    cors_allowed_okta_apps: PropertyRef = PropertyRef(
        "cors_allowed_okta_apps", description="Okta cors allowed okta apps."
    )
    cors_value: PropertyRef = PropertyRef("cors_value", description="Okta cors value.")
    cors_allowed: PropertyRef = PropertyRef(
        "cors_allowed", description="Okta cors allowed."
    )
    redirect_allowed_okta_apps: PropertyRef = PropertyRef(
        "redirect_allowed_okta_apps", description="Okta redirect allowed okta apps."
    )
    redirect_value: PropertyRef = PropertyRef(
        "redirect_value", description="Okta redirect value."
    )
    redirect_allowed: PropertyRef = PropertyRef(
        "redirect_allowed", description="Okta redirect allowed."
    )
    iframe_allowed_okta_apps: PropertyRef = PropertyRef(
        "iframe_allowed_okta_apps", description="Okta iframe allowed okta apps."
    )
    iframe_value: PropertyRef = PropertyRef(
        "iframe_value", description="Okta iframe value."
    )
    iframe_allowed: PropertyRef = PropertyRef(
        "iframe_allowed", description="Okta iframe allowed."
    )
    status: PropertyRef = PropertyRef("status", description="Okta status.")


@dataclass(frozen=True)
class OktaTrustedOriginToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaUser)<-[:RESOURCE]-(:OktaOrganization)
class OktaTrustedOriginToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaTrustedOriginToOktaOrganizationRelProperties = (
        OktaTrustedOriginToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class TrustedOriginCreatedByToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:TrustedOrigin)-[:CREATED_BY]->(:OktaUser)
class TrustedOriginCreatedByToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by", description="Okta created by.")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: TrustedOriginCreatedByToOktaUserRelProperties = (
        TrustedOriginCreatedByToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class TrustedOriginLastUpdateByToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:TrustedOrigin)-[:LAST_UPDATED_BY]->(:OktaUser)
class TrustedOriginLastUpdateByToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("last_updated_by", description="Okta last updated by.")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LAST_UPDATED_BY"
    properties: TrustedOriginLastUpdateByToOktaUserRelProperties = (
        TrustedOriginLastUpdateByToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class OktaTrustedOriginSchema(CartographyNodeSchema):
    label: str = "OktaTrustedOrigin"
    properties: OktaTrustedOriginNodeProperties = OktaTrustedOriginNodeProperties()
    sub_resource_relationship: OktaTrustedOriginToOktaOrganizationRel = (
        OktaTrustedOriginToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            TrustedOriginLastUpdateByToOktaUserRel(),
            TrustedOriginCreatedByToOktaUserRel(),
        ],
    )
