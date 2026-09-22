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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class LangSmithUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ls_user_id",
        description=(
            "Stable LangSmith user ID. Used instead of the user_id field, which mirrors the "
            "first linked auth provider subject and is not stable across login methods."
        ),
    )
    ls_user_id: PropertyRef = PropertyRef(
        "ls_user_id", description="Stable LangSmith user ID."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    name: PropertyRef = PropertyRef("full_name", description="User full name.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User display name."
    )
    avatar_url: PropertyRef = PropertyRef(
        "avatar_url", description="URL of the user's avatar image."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUser)-[:MEMBER_OF]->(:LangSmithWorkspace)
class LangSmithUserToWorkspaceRel(CartographyRelSchema):
    """A user is a member of a workspace. The role held there is on the membership node."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tenant_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: LangSmithUserToWorkspaceRelProperties = (
        LangSmithUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserSchema(CartographyNodeSchema):
    """
    A LangSmith user account, keyed on the stable ls_user_id.

    A user can belong to several organizations, so this node deliberately carries only
    identity that is true of the person everywhere. Everything organization-specific —
    whether the identity is disabled, which organization role it holds, how it was
    provisioned — lives on LangSmithOrgMembership, because storing it here would mean one
    organization's sync overwriting another's view of the same human.

    For the same reason the node has no sub-resource relationship: it is not owned by any
    single organization. Cartography therefore prunes its stale relationships but never
    deletes the node, so one organization's sync cannot destroy an identity another
    organization still references.
    """

    label: str = "LangSmithUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT]
    )  # UserAccount label is used for ontology mapping
    properties: LangSmithUserNodeProperties = LangSmithUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithUserToWorkspaceRel(),
        ],
    )
