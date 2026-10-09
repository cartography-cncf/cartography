from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ECRImagePackagedByCodeBuildProjectMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the PACKAGED_BY relationship between an ECR image and the CodeBuild
    project whose build pushed it.

    The source_* properties record the repository and commit the build checked out. The
    ontology analysis reads them to derive (:Image)-[:PACKAGED_FROM]->(repository).
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    match_method: PropertyRef = PropertyRef(
        "match_method",
        description="How the image was tied to the build: `codebuild_build_id_tag` or `codebuild_tag_revision`.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence of the match, from 0 to 1.",
    )
    build_id: PropertyRef = PropertyRef(
        "build_id",
        description="ID of the CodeBuild build that pushed the image, when a single build is identified.",
    )
    source_revision: PropertyRef = PropertyRef(
        "source_revision",
        description="Commit the build resolved its source to (`resolvedSourceVersion`).",
    )
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        description="Canonical HTTPS URL of the repository the build checked out.",
    )
    source_provider: PropertyRef = PropertyRef(
        "source_provider",
        description="Code host of `source_uri`: `github` or `gitlab`.",
    )


@dataclass(frozen=True)
class ECRImagePackagedByCodeBuildProjectMatchLink(CartographyRelSchema):
    """
    Links an ECR image to the CodeBuild project whose build pushed it.

    Derived from the project's builds: an image tag that carries a build ID, or that
    equals the commit a recent build resolved, identifies the build.
    """

    target_node_label: str = "AWSCodeBuildProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_arn")},
    )
    source_node_label: str = "AWSECRImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_BY"
    properties: ECRImagePackagedByCodeBuildProjectMatchLinkProperties = (
        ECRImagePackagedByCodeBuildProjectMatchLinkProperties()
    )
