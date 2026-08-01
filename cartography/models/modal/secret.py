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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class ModalSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    # Modal aggregates usage into a single timestamp. It is the only observable signal that a
    # secret is still in use, since which workloads consume it is not readable (see below).
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    # Workspace username of the creator, not an email.
    created_by: PropertyRef = PropertyRef("created_by", extra_index=True)
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)
    # NOTE: no property here holds a secret *value*, and none can. Modal exposes no read RPC
    # that returns secret contents at all, so there is nothing to ingest even by accident.


@dataclass(frozen=True)
class ModalSecretToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalSecret)
class ModalSecretToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalSecretToEnvironmentRelProperties = (
        ModalSecretToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalSecretToCreatorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalSecret)-[:CREATED_BY]->(:ModalUser)
# Modal reports the creator as a workspace username, so the intel layer resolves it to a
# ModalUser id against the members of the workspace being synced. Matching on that id rather
# than on a display name is what keeps the edge from crossing tenant boundaries, since display
# names are not globally unique. Absent when the creator is no longer a member.
class ModalSecretToCreatorRel(CartographyRelSchema):
    target_node_label: str = "ModalUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: ModalSecretToCreatorRelProperties = ModalSecretToCreatorRelProperties()


@dataclass(frozen=True)
# A Modal secret. Only metadata is stored; see the note on the properties above.
#
# IMPORTANT: there is deliberately no USES_SECRET edge from any workload. Modal accepts
# `Function.secret_ids` at deploy time but never returns it, so which apps or functions
# consume a given secret is not obtainable from the API and can only be determined from
# source code.
class ModalSecretSchema(CartographyNodeSchema):
    label: str = "ModalSecret"
    properties: ModalSecretNodeProperties = ModalSecretNodeProperties()
    sub_resource_relationship: ModalSecretToEnvironmentRel = (
        ModalSecretToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalSecretToCreatorRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
