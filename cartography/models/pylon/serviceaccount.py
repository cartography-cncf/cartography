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
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class PylonServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Pylon user ID of the identity.")
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the API token or bot.",
    )
    is_deactivated: PropertyRef = PropertyRef(
        "is_deactivated",
        description="Whether the identity is deactivated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PylonServiceAccountToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonOrganization)-[:RESOURCE]->(:PylonServiceAccount)
class PylonServiceAccountToOrganizationRel(CartographyRelSchema):
    """The organization contains the service account."""

    target_node_label: str = "PylonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PylonServiceAccountToOrganizationRelProperties = (
        PylonServiceAccountToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class PylonServiceAccountToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonServiceAccount)-[:HAS_ROLE]->(:PylonRole)
class PylonServiceAccountToRoleRel(CartographyRelSchema):
    """The service account is assigned the role, which is all a token can do."""

    target_node_label: str = "PylonRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: PylonServiceAccountToRoleRelProperties = (
        PylonServiceAccountToRoleRelProperties()
    )


@dataclass(frozen=True)
class PylonServiceAccountSchema(CartographyNodeSchema):
    """A non-human identity in a Pylon organization, read from `GET /users`.

    `GET /users` also returns API tokens that have their own identity and bots.
    These entries have no email address, because API identities and bots can't
    sign in, so Cartography loads every user without an email as a
    `PylonServiceAccount`. The API doesn't distinguish tokens from bots, and it
    doesn't return a token's value, creator, last use, or IP allowlist. Pylon
    tokens don't expire and have no scopes, so the assigned role is the
    token's entire access.
    """

    label: str = "PylonServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: PylonServiceAccountNodeProperties = PylonServiceAccountNodeProperties()
    sub_resource_relationship: PylonServiceAccountToOrganizationRel = (
        PylonServiceAccountToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [PylonServiceAccountToRoleRel()],
    )
