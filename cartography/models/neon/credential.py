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
class NeonCredentialNodeProperties(CartographyNodeProperties):
    # token_id is the credential's public identifier. The listing never returns
    # the api_token or the S3 secret access key.
    id: PropertyRef = PropertyRef(
        "token_id",
        description="The credential's token id (`nak_live_...`). This is an identifier, not a secret: the listing never returns the API token or S3 secret access key",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_id_short: PropertyRef = PropertyRef(
        "token_id_short",
        extra_index=True,
        description="Short form of the token id shown in the Console",
    )
    name: PropertyRef = PropertyRef("name", description="Label of the credential")
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description="Capabilities the credential grants (`storage:read`, `storage:write`, `ai_gateway:invoke`, `functions:invoke`, ...)",
    )
    can_write_storage: PropertyRef = PropertyRef(
        "can_write_storage",
        description="`True` when the credential holds `storage:write`, so it can overwrite or delete objects in every bucket on its branch",
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id",
        description="Id of the branch the credential was issued on. Child branches inherit it",
    )
    principal_type: PropertyRef = PropertyRef(
        "principal_type",
        description="What kind of principal the credential belongs to (`user`, `function`, ...)",
    )
    function_id: PropertyRef = PropertyRef(
        "function_id",
        description="Id of the Neon Function the credential was issued to, when it belongs to one",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the credential was issued"
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at", description="When the credential was last used"
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="When the credential expires, if it does"
    )
    revoked_at: PropertyRef = PropertyRef(
        "revoked_at", description="When the credential was revoked, if it was"
    )


@dataclass(frozen=True)
class NeonCredentialToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonCredential)
class NeonCredentialToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonCredentialToProjectRelProperties = (
        NeonCredentialToProjectRelProperties()
    )


@dataclass(frozen=True)
class NeonCredentialToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonCredential)-[:ISSUED_ON]->(:NeonBranch)
class NeonCredentialToBranchRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("branch_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ISSUED_ON"
    properties: NeonCredentialToBranchRelProperties = (
        NeonCredentialToBranchRelProperties()
    )


@dataclass(frozen=True)
class NeonCredentialSchema(CartographyNodeSchema):
    """Represents a scoped branch credential: the access key used for Neon Object Storage (S3), the AI Gateway and Neon Functions. Only metadata is stored, never the secrets."""

    label: str = "NeonCredential"
    properties: NeonCredentialNodeProperties = NeonCredentialNodeProperties()
    sub_resource_relationship: NeonCredentialToProjectRel = NeonCredentialToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonCredentialToBranchRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
