import logging

from neo4j import Session

from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.client.gcp.artifact_registry import get_gcp_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_tags
from cartography.config import Config
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_images_from_graph(neo4j_session: Session) -> set[str]:
    """
    Query Neo4j for container image URIs from ECR, GCP Artifact Registry,
    and GitLab container registries using the shared client functions.
    Returns image URIs that can be passed directly to `docker scout`.
    """
    image_uris: set[str] = set()

    # ECR images
    for account_id in list_accounts(neo4j_session):
        for _, _, image_uri, _, _ in get_ecr_images(neo4j_session, account_id):
            if image_uri:
                image_uris.add(image_uri)

    # GCP Artifact Registry images
    for _, _, image_uri, _, _ in get_gcp_container_images(neo4j_session):
        if image_uri:
            image_uris.add(image_uri)

    # GitLab container images (base URIs and tagged URIs)
    for uri, _ in get_gitlab_container_images(neo4j_session):
        if uri:
            image_uris.add(uri)
    for tag_location, _ in get_gitlab_container_tags(neo4j_session):
        if tag_location:
            image_uris.add(tag_location)

    return image_uris


@timeit
def start_docker_scout_ingestion(neo4j_session: Session, config: Config) -> None:
    """Entry point for Docker Scout ingestion."""
    images: set[str] = set()

    # Add explicitly specified images
    if config.docker_scout_images:
        explicit = {
            img.strip() for img in config.docker_scout_images.split(",") if img.strip()
        }
        images.update(explicit)
        logger.info("Found %d explicitly configured Docker Scout images", len(explicit))

    # Add images discovered from the graph
    graph_images = _get_images_from_graph(neo4j_session)
    if graph_images:
        images.update(graph_images)
        logger.info("Found %d container images in the graph to scan", len(graph_images))

    if not images:
        logger.info("No Docker Scout images to scan. Skipping.")
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    logger.info("Starting Docker Scout sync for %d images", len(images))
    synced_count = 0
    for image in sorted(images):
        sync(neo4j_session, image, config.update_tag)
        synced_count += 1

    if synced_count > 0:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "No images synced successfully, skipping cleanup to preserve existing data"
        )
