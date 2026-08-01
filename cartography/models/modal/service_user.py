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
class ModalServiceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    # Modal reports the creator as a workspace *username*, not an email.
    created_by: PropertyRef = PropertyRef("created_by", extra_index=True)


@dataclass(frozen=True)
class ModalServiceUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalServiceUser)
class ModalServiceUserToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalServiceUserToWorkspaceRelProperties = (
        ModalServiceUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class ModalServiceUserToCreatorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalServiceUser)-[:CREATED_BY]->(:ModalUser)
# Modal exposes the creator only as a workspace username, which the intel layer resolves to
# a ModalUser id against this workspace's members. Absent when the creator is no longer a
# member of the workspace being synced.
class ModalServiceUserToCreatorRel(CartographyRelSchema):
    target_node_label: str = "ModalUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: ModalServiceUserToCreatorRelProperties = (
        ModalServiceUserToCreatorRelProperties()
    )


@dataclass(frozen=True)
# A Modal service user is a machine identity that owns exactly one API token. It is the
# recommended way to run Cartography against Modal, since Modal has no read-only token
# scope and a personal token carries all of its owner's privileges.
class ModalServiceUserSchema(CartographyNodeSchema):
    label: str = "ModalServiceUser"
    properties: ModalServiceUserNodeProperties = ModalServiceUserNodeProperties()
    sub_resource_relationship: ModalServiceUserToWorkspaceRel = (
        ModalServiceUserToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalServiceUserToCreatorRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
