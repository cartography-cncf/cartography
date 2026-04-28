"""
GitHub Container Image Attestation Schema.

Represents SLSA attestations (build provenance) returned by the GitHub
Attestations API for container images pushed to GHCR.

See: https://docs.github.com/en/rest/users/attestations
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
class GitHubContainerImageAttestationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    bundle_id: PropertyRef = PropertyRef("bundle_id")
    predicate_type: PropertyRef = PropertyRef("predicate_type", extra_index=True)
    attests_digest: PropertyRef = PropertyRef("attests_digest", extra_index=True)
    source_uri: PropertyRef = PropertyRef("source_uri")
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageAttestationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageAttestationToOrgRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerImageAttestationRelProperties = (
        GitHubContainerImageAttestationRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageAttestationAttestsRel(CartographyRelSchema):
    """Links an attestation to the image digest it attests."""

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("attests_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTESTS"
    properties: GitHubContainerImageAttestationRelProperties = (
        GitHubContainerImageAttestationRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageAttestationSchema(CartographyNodeSchema):
    label: str = "GitHubContainerImageAttestation"
    properties: GitHubContainerImageAttestationNodeProperties = (
        GitHubContainerImageAttestationNodeProperties()
    )
    sub_resource_relationship: GitHubContainerImageAttestationToOrgRel = (
        GitHubContainerImageAttestationToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubContainerImageAttestationAttestsRel()],
    )
