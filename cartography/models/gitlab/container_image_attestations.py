"""
GitLab Container Image Attestation Schema

Represents attestations (signatures, provenance, SBOMs) for container images.
Attestations are discovered via cosign's tag-based scheme:
- Signatures: sha256-{digest}.sig
- Attestations: sha256-{digest}.att

See: https://docs.sigstore.dev/cosign/signing/signing_with_containers/
"""

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
class GitLabContainerImageAttestationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    media_type: PropertyRef = PropertyRef("media_type")
    attestation_type: PropertyRef = PropertyRef("attestation_type", extra_index=True)
    predicate_type: PropertyRef = PropertyRef("predicate_type")
    attests_digest: PropertyRef = PropertyRef("attests_digest", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageAttestationToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageAttestationToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabContainerImageAttestation to GitLabOrganization.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabContainerImageAttestationToOrgRelProperties = (
        GitLabContainerImageAttestationToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerImageAttestationAttestsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageAttestationAttestsRel(CartographyRelSchema):
    """
    Relationship from attestation to the image it attests.
    """

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("attests_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTESTS"
    properties: GitLabContainerImageAttestationAttestsRelProperties = (
        GitLabContainerImageAttestationAttestsRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerImageAttestationSchema(CartographyNodeSchema):
    """
    Schema for GitLab Container Image Attestation nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitLabOrganization for cleanup
    - ATTESTS: Links to the GitLabContainerImage this attestation validates
    """

    label: str = "GitLabContainerImageAttestation"
    properties: GitLabContainerImageAttestationNodeProperties = (
        GitLabContainerImageAttestationNodeProperties()
    )
    sub_resource_relationship: GitLabContainerImageAttestationToOrgRel = (
        GitLabContainerImageAttestationToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabContainerImageAttestationAttestsRel(),
        ],
    )
