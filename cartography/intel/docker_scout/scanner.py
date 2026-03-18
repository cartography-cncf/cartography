import logging
from dataclasses import dataclass
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.docker_scout.recommendation_parser import (
    parse_recommendation_text,
)
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.docker_scout.image import DockerScoutPublicImageSchema
from cartography.models.docker_scout.public_image_tag import (
    DockerScoutPublicImageTagSchema,
)
from cartography.util import timeit
from cartography.version import get_cartography_version

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DockerScoutPublicImageCleanupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageCleanupBuiltOnRel(CartographyRelSchema):
    """
    Cleanup-only relationship schema.

    The target matcher is intentionally irrelevant here: GraphJob unscoped cleanup
    only needs the relationship label and target node label to delete stale
    BUILT_ON edges. Relationship creation still happens via targeted Cypher because
    Docker Scout exposes only a digest prefix.
    """

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_unused_cleanup_matcher")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageCleanupRelProperties = (
        DockerScoutPublicImageCleanupRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageCleanupSchema(DockerScoutPublicImageSchema):
    other_relationships: OtherRelationships = OtherRelationships(
        [DockerScoutPublicImageCleanupBuiltOnRel()],
    )


def _normalize_digest_for_compare(digest: str) -> str:
    return digest.removeprefix("sha256:").strip().lower()


def _merge_string_lists(
    left: list[str] | None,
    right: list[str] | None,
) -> list[str] | None:
    merged: list[str] = []
    for value in left or []:
        if value not in merged:
            merged.append(value)
    for value in right or []:
        if value not in merged:
            merged.append(value)
    return merged or None


def parse_recommendation_raw(raw_recommendation: str) -> dict[str, Any]:
    """Parse a raw Docker Scout recommendation report into a structured dict."""
    return parse_recommendation_text(raw_recommendation)


def transform_public_image(recommendation_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build the current public base image node from a Docker Scout recommendation report.
    """
    base_image = recommendation_data["base_image"]
    target = recommendation_data.get("target", {})
    return {
        "id": f'{base_image["name"]}:{base_image["tag"]}',
        "name": base_image["name"],
        "tag": base_image["tag"],
        "alternative_tags": base_image.get("alternative_tags"),
        "version": base_image.get("runtime"),
        "digest": base_image.get("digest"),
        "target_digest": target.get("digest"),
        "target_image": target.get("image"),
    }


def transform_public_image_tags(
    recommendation_data: dict[str, Any],
    public_image_id: str,
) -> list[dict[str, Any]]:
    """Transform parsed recommendation data into DockerScoutPublicImageTag rows."""
    transformed: list[dict[str, Any]] = []
    canonical_by_id: dict[str, dict[str, Any]] = {}

    base_image = recommendation_data.get("base_image")
    if base_image:
        base_row = {
            "id": f'{base_image["name"]}:{base_image["tag"]}',
            "name": base_image["name"],
            "tag": base_image["tag"],
            "alternative_tags": base_image.get("alternative_tags"),
            "size": base_image.get("size"),
            "flavor": base_image.get("flavor"),
            "os": base_image.get("os"),
            "runtime": base_image.get("runtime"),
            "is_slim": base_image.get("is_slim"),
            "built_from_public_image_id": public_image_id,
        }
        transformed.append(base_row)
        canonical_by_id[base_row["id"]] = {
            key: value
            for key, value in base_row.items()
            if key
            not in {
                "built_from_public_image_id",
                "recommended_for_public_image_id",
                "benefits",
                "fix_critical",
                "fix_high",
                "fix_medium",
                "fix_low",
            }
        }

    recommendations = recommendation_data.get("recommendations", {})
    for recommendation in recommendations.values():
        recommendation_id = f'{recommendation["name"]}:{recommendation["tag"]}'
        node_fields = {
            "id": recommendation_id,
            "name": recommendation["name"],
            "tag": recommendation["tag"],
            "alternative_tags": recommendation.get("alternative_tags"),
            "size": recommendation.get("size"),
            "flavor": recommendation.get("flavor"),
            "os": recommendation.get("os"),
            "runtime": recommendation.get("runtime"),
            "is_slim": recommendation.get("is_slim"),
        }
        existing = canonical_by_id.get(recommendation_id, {})
        canonical_by_id[recommendation_id] = {
            **node_fields,
            **existing,
            "alternative_tags": _merge_string_lists(
                existing.get("alternative_tags"),
                node_fields.get("alternative_tags"),
            ),
        }
        transformed.append(
            {
                "id": recommendation_id,
                "benefits": recommendation.get("benefits"),
                "fix_critical": recommendation.get("fix", {}).get("C"),
                "fix_high": recommendation.get("fix", {}).get("H"),
                "fix_medium": recommendation.get("fix", {}).get("M"),
                "fix_low": recommendation.get("fix", {}).get("L"),
                "recommended_for_public_image_id": public_image_id,
            },
        )

    relation_fields = {
        "built_from_public_image_id",
        "recommended_for_public_image_id",
        "benefits",
        "fix_critical",
        "fix_high",
        "fix_medium",
        "fix_low",
    }
    for row in transformed:
        canonical = canonical_by_id[row["id"]]
        for key, value in canonical.items():
            if key not in relation_fields:
                row[key] = value

    logger.info("Transformed %d public image tag rows", len(transformed))
    return transformed


@timeit
def load_public_image(
    neo4j_session: neo4j.Session,
    public_image_data: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DockerScoutPublicImageSchema(),
        [public_image_data],
        lastupdated=update_tag,
    )


@timeit
def load_public_image_tags(
    neo4j_session: neo4j.Session,
    public_image_tags_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DockerScoutPublicImageTagSchema(),
        public_image_tags_list,
        lastupdated=update_tag,
    )


@timeit
def attach_public_image_to_target_image(
    neo4j_session: neo4j.Session,
    public_image_data: dict[str, Any],
    update_tag: int,
) -> None:
    """
    Attach DockerScoutPublicImage to ontology Image nodes using _ont_digest.
    """
    target_digest = public_image_data.get("target_digest")
    if not target_digest:
        return

    target_digest = _normalize_digest_for_compare(target_digest)
    public_image_id = public_image_data["id"]

    query = """
    WITH $public_image_id AS public_image_id, $target_digest AS target_digest, $update_tag AS update_tag
    MATCH (p:DockerScoutPublicImage {id: public_image_id})
    OPTIONAL MATCH (img:Image)
    WHERE toLower(replace(coalesce(img._ont_digest, ''), 'sha256:', '')) STARTS WITH target_digest
    WITH p, img, update_tag WHERE img IS NOT NULL
    MERGE (img)-[r:BUILT_ON]->(p)
    ON CREATE SET r.firstseen = timestamp()
    SET r._module_name = 'cartography:docker_scout',
        r._module_version = $module_version,
        r.lastupdated = update_tag
    RETURN count(img) AS total_matches
    """
    result = neo4j_session.run(
        query,
        public_image_id=public_image_id,
        target_digest=target_digest,
        update_tag=update_tag,
        module_version=get_cartography_version(),
    ).single()
    total_matches = result["total_matches"] if result else 0
    logger.info(
        "Attached DockerScoutPublicImage %s to %d target image node(s)",
        public_image_id,
        total_matches,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Running Docker Scout cleanup")
    GraphJob.from_node_schema(
        DockerScoutPublicImageTagSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DockerScoutPublicImageCleanupSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_from_file(
    neo4j_session: neo4j.Session,
    raw_recommendation: str,
    source: str,
    update_tag: int,
) -> bool:
    """
    Sync Docker Scout recommendation data from a raw text report.
    """
    try:
        recommendation_data = parse_recommendation_raw(raw_recommendation)
    except ValueError:
        logger.warning(
            "Skipping %s: invalid or non-Docker Scout recommendation report",
            source,
            exc_info=True,
        )
        return False
    target = recommendation_data.get("target", {})
    base_image = recommendation_data.get("base_image")
    if not target or not base_image:
        logger.warning(
            "Skipping %s: missing target or base image data in Docker Scout report",
            source,
        )
        return False

    public_image = transform_public_image(recommendation_data)
    public_image_tags = transform_public_image_tags(
        recommendation_data, public_image["id"]
    )

    load_public_image(neo4j_session, public_image, update_tag)
    load_public_image_tags(neo4j_session, public_image_tags, update_tag)
    attach_public_image_to_target_image(neo4j_session, public_image, update_tag)

    logger.info(
        "Completed Docker Scout sync for %s: public_image=%s, %d public image tags",
        source,
        public_image["id"],
        len(public_image_tags),
    )
    return True
