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


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyFormNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify form id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the form was detected on."
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Form name, from the `name` attribute of the HTML form.",
    )
    # The site paths the form was detected on.
    paths: PropertyRef = PropertyRef(
        "paths", description="Site paths the form was detected on."
    )
    # Netlify stores every submission, so a form is a data store holding whatever visitors typed
    # into it. The field names say what kind of data that is; the submissions themselves are not
    # ingested.
    field_names: PropertyRef = PropertyRef(
        "field_names", description="Names of the form's input fields."
    )
    submission_count: PropertyRef = PropertyRef(
        "submission_count", description="Number of submissions Netlify has stored."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the form was first detected."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyFormToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyForm)
class NetlifyFormToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyFormToNetlifyAccountRelProperties = (
        NetlifyFormToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyFormToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_FORM]->(:NetlifyForm)
class NetlifyFormToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_FORM"
    properties: NetlifyFormToSiteRelProperties = NetlifyFormToSiteRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyFormSchema(CartographyNodeSchema):
    """
    A form Netlify detected on a site, together with the submissions it collects.
    """

    label: str = "NetlifyForm"
    properties: NetlifyFormNodeProperties = NetlifyFormNodeProperties()
    sub_resource_relationship: NetlifyFormToNetlifyAccountRel = (
        NetlifyFormToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyFormToSiteRel()],
    )
