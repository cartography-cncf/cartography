"""
Shared supply chain logic for matching container images to Dockerfiles.

This module contains the provider-agnostic core of the supply chain sync:
- Unified data classes (ContainerImage, ImageDockerfileMatch, SupplyChainSyncResult)
- PackagingConfig for parameterizing provider-specific load/cleanup
- The Dockerfile-to-image matching algorithm
- Parameterized load/cleanup helpers
- Common parsing helpers

Provider modules (github/supply_chain.py, gitlab/supply_chain.py) import from here
and supply platform-specific API calls, Cypher queries, and matchlink schemas.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.dockerfile_parser import extract_layer_commands_from_history
from cartography.intel.dockerfile_parser import find_best_dockerfile_matches
from cartography.intel.dockerfile_parser import parse as parse_dockerfile
from cartography.intel.dockerfile_parser import ParsedDockerfile
from cartography.models.core.relationships import CartographyRelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass
class ContainerImage:
    """Represents a container image from the graph (ECR, GCR, GitLab, etc.)."""

    digest: str
    uri: str
    registry_id: str | None
    display_name: str | None
    tag: str | None
    layer_diff_ids: list[str]
    image_type: str | None
    architecture: str | None
    os: str | None
    layer_history: list[dict[str, Any]]


@dataclass
class ImageDockerfileMatch:
    """Represents a match between a container registry repository and a Dockerfile."""

    registry_id: str
    source_repo_id: str
    dockerfile_path: str | None
    confidence: float
    matched_commands: int
    total_commands: int
    command_similarity: float


@dataclass
class PackagingConfig:
    """Provider-specific parameters for load/cleanup/transform."""

    matchlink_schema: CartographyRelSchema
    sub_resource_label: str
    source_repo_field: str
    registry_id_field: str


@dataclass
class SupplyChainSyncResult:
    """Results from a supply chain sync operation."""

    dockerfiles: list[dict[str, Any]]
    images: list[ContainerImage] | None = None
    matches: list[ImageDockerfileMatch] | None = None

    @property
    def dockerfile_count(self) -> int:
        return len(self.dockerfiles)

    @property
    def image_count(self) -> int:
        return len(self.images) if self.images else 0

    @property
    def match_count(self) -> int:
        return len(self.matches) if self.matches else 0


def match_images_to_dockerfiles(
    images: list[ContainerImage],
    dockerfiles: list[dict[str, Any]],
    min_confidence: float = 0.5,
) -> list[ImageDockerfileMatch]:
    """
    Match container images to Dockerfiles based on layer history commands.

    :param images: List of container images to match (with layer_history already populated)
    :param dockerfiles: List of dockerfile dictionaries (from provider-specific get_dockerfiles)
    :param min_confidence: Minimum confidence threshold for matches
    :return: List of ImageDockerfileMatch objects
    """
    parsed_dockerfiles: list[ParsedDockerfile] = []
    dockerfile_info_map: dict[str, dict[str, Any]] = {}

    for df_info in dockerfiles:
        try:
            parsed = parse_dockerfile(df_info["content"])
            dockerfile_info_map[parsed.content_hash] = df_info
            parsed_dockerfiles.append(parsed)
        except Exception as e:
            logger.warning("Failed to parse dockerfile %s: %s", df_info.get("path"), e)

    if not parsed_dockerfiles:
        logger.warning("No valid Dockerfiles to match against")
        return []

    matches: list[ImageDockerfileMatch] = []

    for image in images:
        if not image.registry_id:
            logger.debug(
                "No registry_id for image %s:%s, skipping",
                image.display_name,
                image.tag,
            )
            continue
        if not image.layer_history:
            logger.debug(
                "No layer history for image %s:%s", image.display_name, image.tag
            )
            continue

        image_commands = extract_layer_commands_from_history(image.layer_history)
        if not image_commands:
            logger.debug(
                "No commands extracted for image %s:%s",
                image.display_name,
                image.tag,
            )
            continue

        df_matches = find_best_dockerfile_matches(
            image_commands, parsed_dockerfiles, min_confidence
        )

        if df_matches:
            best_match = df_matches[0]
            df_info = dockerfile_info_map.get(best_match.dockerfile.content_hash, {})

            matches.append(
                ImageDockerfileMatch(
                    registry_id=image.registry_id,
                    source_repo_id=df_info.get("source_repo_id", ""),
                    dockerfile_path=df_info.get("path"),
                    confidence=best_match.confidence,
                    matched_commands=best_match.matched_commands,
                    total_commands=best_match.total_commands,
                    command_similarity=best_match.command_similarity,
                )
            )
            logger.debug(
                "Matched %s:%s -> %s (confidence: %.2f)",
                image.display_name,
                image.tag,
                df_info.get("path"),
                best_match.confidence,
            )
        else:
            logger.debug(
                "No match found for image %s:%s", image.display_name, image.tag
            )

    logger.info(
        "Matched %d images to Dockerfiles (out of %d images, %d Dockerfiles)",
        len(matches),
        len(images),
        len(parsed_dockerfiles),
    )
    return matches


def transform_matches_for_matchlink(
    matches: list[ImageDockerfileMatch],
    config: PackagingConfig,
) -> list[dict[str, Any]]:
    """
    Transform ImageDockerfileMatch objects into dictionaries for load_matchlinks.

    Uses the PackagingConfig to map generic fields to provider-specific field names
    expected by the matchlink schema.

    :param matches: List of ImageDockerfileMatch objects
    :param config: Provider-specific configuration
    :return: List of dictionaries with fields matching the MatchLink schema
    """
    return [
        {
            config.source_repo_field: m.source_repo_id,
            config.registry_id_field: m.registry_id,
            "match_method": "dockerfile_analysis",
            "dockerfile_path": m.dockerfile_path,
            "confidence": m.confidence,
            "matched_commands": m.matched_commands,
            "total_commands": m.total_commands,
            "command_similarity": m.command_similarity,
        }
        for m in matches
        if m.source_repo_id
    ]


@timeit
def load_packaging_relationships(
    neo4j_session: neo4j.Session,
    matches: list[ImageDockerfileMatch],
    sub_resource_id: str,
    update_tag: int,
    config: PackagingConfig,
) -> None:
    """
    Load PACKAGED_FROM relationships using the provider's matchlink schema.

    :param neo4j_session: Neo4j session
    :param matches: List of ImageDockerfileMatch objects
    :param sub_resource_id: The organization/group identifier (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    :param config: Provider-specific configuration
    """
    if not matches:
        logger.info("No matches to load")
        return

    matchlink_data = transform_matches_for_matchlink(matches, config)

    if not matchlink_data:
        logger.info("No valid matches with source repo IDs to load")
        return

    logger.info("Loading %d PACKAGED_FROM relationships...", len(matchlink_data))

    load_matchlinks(
        neo4j_session,
        config.matchlink_schema,
        matchlink_data,
        lastupdated=update_tag,
        _sub_resource_label=config.sub_resource_label,
        _sub_resource_id=sub_resource_id,
    )

    logger.info("Loaded %d PACKAGED_FROM relationships", len(matchlink_data))


@timeit
def cleanup_packaging_relationships(
    neo4j_session: neo4j.Session,
    sub_resource_id: str,
    update_tag: int,
    config: PackagingConfig,
) -> None:
    """
    Clean up stale PACKAGED_FROM relationships.

    :param neo4j_session: Neo4j session
    :param sub_resource_id: The organization/group identifier (used as sub_resource_id)
    :param update_tag: The update timestamp tag
    :param config: Provider-specific configuration
    """
    logger.info("Cleaning up stale PACKAGED_FROM relationships...")

    cleanup_job = GraphJob.from_matchlink(
        config.matchlink_schema,
        config.sub_resource_label,
        sub_resource_id,
        update_tag,
    )
    cleanup_job.run(neo4j_session)

    logger.info("Cleanup complete")


def parse_dockerfile_info(
    content: str,
    path: str,
    display_name: str,
) -> dict[str, Any] | None:
    """
    Parse a Dockerfile and return structured info, or None on failure.

    Provider modules call this and then add their own identifier fields
    (repo_url/project_url, repo_name/project_name, sha, html_url, etc.).

    :param content: Raw Dockerfile content
    :param path: File path within the repository
    :param display_name: Human-readable repo/project name (for logging)
    :return: Dict with parsed fields, or None if parsing fails
    """
    try:
        parsed = parse_dockerfile(content)
        return {
            "path": path,
            "content": content,
            "is_multistage": parsed.is_multistage,
            "stage_count": parsed.stage_count,
            "final_base_image": parsed.final_base_image,
            "all_base_images": parsed.all_base_images,
            "layer_count": parsed.layer_creating_instruction_count,
            "stages": [
                {
                    "name": stage.name,
                    "base_image": stage.base_image,
                    "base_image_tag": stage.base_image_tag,
                    "layer_count": stage.layer_count,
                }
                for stage in parsed.stages
            ],
        }
    except Exception as e:
        logger.warning("Failed to parse Dockerfile %s/%s: %s", display_name, path, e)
        return None


def convert_layer_history_records(
    raw_records: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """
    Convert raw layer history records from Neo4j query results into the format
    expected by the matching algorithm.

    :param raw_records: Raw layer records from Neo4j (with 'history', 'is_empty', 'diff_id')
    :return: List of dicts with 'created_by', 'empty_layer', 'diff_id' keys
    """
    return [
        {
            "created_by": layer.get("history") or "",
            "empty_layer": layer.get("is_empty") or False,
            "diff_id": layer.get("diff_id"),
        }
        for layer in (raw_records or [])
    ]


def normalize_vcs_url(url: str) -> str:
    """
    Normalize a VCS URL from BuildKit provenance to a canonical HTTPS repo URL.

    BuildKit vcs.source can report URLs in various formats:
    - https://github.com/org/repo.git
    - git@github.com:org/repo.git
    - https://github.com/org/repo

    Downstream matching compares source_uri against GitHubRepository.id / GitLabProject.id,
    which use the canonical HTTPS URL without .git suffix (e.g., https://github.com/org/repo).

    :param url: The raw VCS URL from provenance
    :return: Normalized HTTPS URL without .git suffix
    """
    normalized = url.strip()

    # Convert SSH format (git@host:org/repo.git) to HTTPS
    ssh_match = re.match(r"git@([^:]+):(.+)", normalized)
    if ssh_match:
        host, path = ssh_match.groups()
        normalized = f"https://{host}/{path}"

    # Strip .git suffix
    if normalized.endswith(".git"):
        normalized = normalized[:-4]

    return normalized


def extract_workflow_path_from_ref(workflow_ref: str | None) -> str | None:
    """
    Extract the workflow file path from a GitHub workflow ref.

    The workflow ref format is: {owner}/{repo}/{path}@{ref}
    Example: "subimagesec/subimage/.github/workflows/docker-push.yaml@refs/pull/1042/merge"
    Returns: ".github/workflows/docker-push.yaml"

    This extracts the path for matching against GitHubWorkflow.path to establish
    the PACKAGED_BY relationship between images and workflows (combined with repo_url matching).

    :param workflow_ref: The full workflow reference string
    :return: The workflow file path, or None if parsing fails
    """
    if not workflow_ref:
        return None

    # Split off the @ref suffix
    path_part = workflow_ref.split("@")[0]

    # The path is everything after {owner}/{repo}/
    # Find the second slash to skip owner/repo
    parts = path_part.split("/", 2)
    if len(parts) >= 3:
        return parts[2]  # The path after owner/repo/

    return None
