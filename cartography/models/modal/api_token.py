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
class ModalApiTokenNodeProperties(CartographyNodeProperties):
    # The `ak-` token id. It is the credential's stable identifier and is safe to store:
    # the token *secret* is only ever shown once, at creation, and is never returned by any
    # read RPC.
    id: PropertyRef = PropertyRef(
        "id", description="Token ID, e.g. `ak-4pE5t96YiNM0svmOjIet7z`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_id: PropertyRef = PropertyRef(
        "token_id",
        extra_index=True,
        description="Same value, indexed for lookups by credential.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the owning service user."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the token was created."
    )
    # Drives stale-credential detection. Modal tokens never expire, so last use is the
    # only signal that a token is dormant.
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="When the token was last used. Modal tokens do not expire, so this is the only signal that one is dormant.",
    )


@dataclass(frozen=True)
class ModalApiTokenToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalApiToken)
class ModalApiTokenToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalApiTokenToWorkspaceRelProperties = (
        ModalApiTokenToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class ModalApiTokenToServiceUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalApiToken)-[:OWNED_BY]->(:ModalServiceUser)
# OWNED_BY is the canonical APIKey -> ServiceAccount label in ONTOLOGY_REL_CONSTRAINTS.
class ModalApiTokenToServiceUserRel(CartographyRelSchema):
    target_node_label: str = "ModalServiceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: ModalApiTokenToServiceUserRelProperties = (
        ModalApiTokenToServiceUserRelProperties()
    )


@dataclass(frozen=True)
class ModalApiTokenSchema(CartographyNodeSchema):
    """Represents a Modal API token (`ak-`) belonging to a service user. Only the token id is stored; the token secret is shown once at creation and is never returned by any read API."""

    label: str = "ModalApiToken"
    properties: ModalApiTokenNodeProperties = ModalApiTokenNodeProperties()
    sub_resource_relationship: ModalApiTokenToWorkspaceRel = (
        ModalApiTokenToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalApiTokenToServiceUserRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
