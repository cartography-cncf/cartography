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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class NeonApiKeyNodeProperties(CartographyNodeProperties):
    # The API never returns the token itself: it is shown once, at creation.
    id: PropertyRef = PropertyRef(
        "id",
        description="The numeric API key id, as a string. The token itself is never returned by the API",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the API key"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the API key was created"
    )
    created_by_id: PropertyRef = PropertyRef(
        "created_by_id", description="User id of the member who created the key"
    )
    created_by_name: PropertyRef = PropertyRef(
        "created_by_name", description="Display name of the member who created the key"
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at", description="When the key last authenticated a request"
    )
    last_used_from_addr: PropertyRef = PropertyRef(
        "last_used_from_addr",
        description="The IP address the key was last used from",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="When set, the key is scoped to this single project instead of the whole organization",
    )
    org_id: PropertyRef = PropertyRef(
        "ORG_ID",
        set_in_kwargs=True,
        description="Id of the organization the key belongs to",
    )


@dataclass(frozen=True)
class NeonApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonOrganization)-[:RESOURCE]->(:NeonApiKey)
class NeonApiKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "NeonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonApiKeyToOrganizationRelProperties = (
        NeonApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class NeonApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonApiKey)-[:SCOPED_TO]->(:NeonProject)
class NeonApiKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCOPED_TO"
    properties: NeonApiKeyToProjectRelProperties = NeonApiKeyToProjectRelProperties()


@dataclass(frozen=True)
class NeonApiKeyToMemberRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonApiKey)-[:OWNED_BY]->(:NeonOrganizationMember)
class NeonApiKeyToMemberRel(CartographyRelSchema):
    target_node_label: str = "NeonOrganizationMember"
    # Membership nodes are per organization, so match on the organization too:
    # the creator's user id alone would also match their memberships elsewhere.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "user_id": PropertyRef("created_by_id"),
            "org_id": PropertyRef("ORG_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: NeonApiKeyToMemberRelProperties = NeonApiKeyToMemberRelProperties()


@dataclass(frozen=True)
class NeonApiKeySchema(CartographyNodeSchema):
    """Represents an organization API key. A key with a `project_id` is limited to that project; one without it can manage every project in the organization."""

    label: str = "NeonApiKey"
    properties: NeonApiKeyNodeProperties = NeonApiKeyNodeProperties()
    sub_resource_relationship: NeonApiKeyToOrganizationRel = (
        NeonApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonApiKeyToProjectRel(),
            NeonApiKeyToMemberRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
