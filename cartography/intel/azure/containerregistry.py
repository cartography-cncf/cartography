import json
import logging
import time
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def get_client(credentials: Credentials, subscription_id: str) -> ContainerRegistryManagementClient:
    client = ContainerRegistryManagementClient(credentials, subscription_id)
    return client


def _safe_console_link(resource_id: str, common_job_parameters: Dict) -> str:
    try:
        return azure_console_link.get_console_link(
            id=resource_id,
            primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
        )
    except (ValueError, KeyError) as e:
        logger.warning("Could not generate console link for %s: %s", resource_id, e)
        return ''


def get_registry_list(
    credentials: Credentials,
    subscription_id: str,
    regions: Optional[List[str]],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        registries = []

        for registry in client.registries.list():
            if regions and registry.location not in regions:
                continue

            registry_dict = {
                "id": registry.id,
                "name": registry.name,
                "location": registry.location,
                "resource_group": get_azure_resource_group_name(registry.id),
                "login_server": registry.login_server,
                "sku_name": registry.sku.name if registry.sku else None,
                "sku_tier": registry.sku.tier if registry.sku else None,
                "admin_user_enabled": registry.admin_user_enabled,
                "public_network_access": registry.public_network_access,
                "zone_redundancy": registry.zone_redundancy,
                "encryption_status": registry.encryption.status if registry.encryption else None,
                "trust_policy_status": registry.policies.trust_policy.status
                if registry.policies and registry.policies.trust_policy
                else None,
                "quarantine_policy_status": registry.policies.quarantine_policy.status
                if registry.policies and registry.policies.quarantine_policy
                else None,
                "retention_policy_status": registry.policies.retention_policy.status
                if registry.policies and registry.policies.retention_policy
                else None,
                "creation_date": registry.creation_date.isoformat() if registry.creation_date else None,
                "console_link": _safe_console_link(registry.id, common_job_parameters),
                "subscription_id": subscription_id,
                "type": registry.type,
                "tags": json.dumps(registry.tags) if registry.tags else None,
            }
            registries.append(registry_dict)

        return registries
    except HttpResponseError as e:
        logger.warning(f"Failed to retrieve container registries for subscription {subscription_id}: {e}")
        return []


def get_repository_list(
    credentials: Credentials,
    subscription_id: str,
    registry_name: str,
    resource_group: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        repositories = []

        for repo in client.repositories.list(resource_group, registry_name):
            repo_dict = {
                "name": repo.name,
                "registry_name": registry_name,
                "created_time": repo.created_time.isoformat() if repo.created_time else None,
                "last_update_time": repo.last_update_time.isoformat() if repo.last_update_time else None,
                "manifest_count": repo.manifest_count,
                "tag_count": repo.tag_count,
                "size": repo.size,
                "subscription_id": subscription_id,
                "resource_group": resource_group,
            }
            repositories.append(repo_dict)

        return repositories
    except AttributeError as e:
        logger.warning(
            f"Repositories API not available on management client for registry {registry_name} "
            f"(data-plane operation): {e}",
        )
        return []
    except HttpResponseError as e:
        logger.warning(f"Failed to retrieve repositories for registry {registry_name}: {e}")
        return []


def get_image_list(
    credentials: Credentials,
    subscription_id: str,
    registry_name: str,
    resource_group: str,
    repository_name: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        images = []

        for manifest in client.manifests.list(resource_group, registry_name, repository_name):
            quarantine_details = getattr(manifest, "quarantine_details", "")
            if isinstance(quarantine_details, dict):
                quarantine_details = json.dumps(quarantine_details)
            image_dict = {
                "digest": manifest.digest,
                "repository_name": repository_name,
                "registry_name": registry_name,
                "created_time": manifest.created_time.isoformat() if manifest.created_time else None,
                "last_update_time": manifest.last_update_time.isoformat() if manifest.last_update_time else None,
                "architecture": manifest.architecture,
                "os": manifest.os,
                "size": manifest.size,
                "size_bytes": manifest.size,
                "tags": manifest.tags or [],
                "media_type": getattr(manifest, "media_type", ""),
                "config_media_type": getattr(manifest, "config_media_type", ""),
                "quarantine_state": getattr(manifest, "quarantine_state", ""),
                "quarantine_details": quarantine_details,
                "subscription_id": subscription_id,
                "resource_group": resource_group,
            }
            images.append(image_dict)

        return images
    except AttributeError as e:
        logger.warning(
            f"Manifests API not available on management client for repository {repository_name} "
            f"(data-plane operation): {e}",
        )
        return []
    except HttpResponseError as e:
        logger.warning(f"Failed to retrieve images for repository {repository_name}: {e}")
        return []


def _load_registries_tx(tx: neo4j.Transaction, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_query = """
    UNWIND $registries as registry
    MERGE (r:AzureContainerRegistry{id: registry.id})
    ON CREATE SET r.firstseen = timestamp()
    SET
        r.lastupdated = $update_tag,
        r.name = registry.name,
        r.location = registry.location,
        r.resource_group = registry.resource_group,
        r.login_server = registry.login_server,
        r.sku_name = registry.sku_name,
        r.sku_tier = registry.sku_tier,
        r.admin_user_enabled = registry.admin_user_enabled,
        r.public_network_access = registry.public_network_access,
        r.zone_redundancy = registry.zone_redundancy,
        r.encryption_status = registry.encryption_status,
        r.trust_policy_status = registry.trust_policy_status,
        r.quarantine_policy_status = registry.quarantine_policy_status,
        r.retention_policy_status = registry.retention_policy_status,
        r.creation_date = registry.creation_date,
        r.console_link = registry.console_link,
        r.type = registry.type,
        r.tags = registry.tags

    WITH r
    MATCH (sub:AzureSubscription{id: $subscription_id})
    MERGE (sub)-[rel:RESOURCE]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        registries=data_list,
        subscription_id=subscription_id,
        update_tag=update_tag,
    )


def _load_repositories_tx(tx: neo4j.Transaction, registry_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_query = """
    UNWIND $repositories as repo
    MERGE (r:AzureContainerRepository{name: repo.name, registry_name: repo.registry_name})
    ON CREATE SET r.firstseen = timestamp()
    SET
        r.lastupdated = $update_tag,
        r.created_time = repo.created_time,
        r.last_update_time = repo.last_update_time,
        r.manifest_count = repo.manifest_count,
        r.tag_count = repo.tag_count,
        r.size = repo.size,
        r.subscription_id = repo.subscription_id,
        r.resource_group = repo.resource_group

    WITH r
    MATCH (reg:AzureContainerRegistry{id: $registry_id})
    MERGE (reg)-[rel:CONTAINS]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        repositories=data_list,
        registry_id=registry_id,
        update_tag=update_tag,
    )


def _load_images_tx(
    tx: neo4j.Transaction,
    repository_name: str,
    registry_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $images as image
    MERGE (i:AzureContainerImage{digest: image.digest, repository_name: image.repository_name, registry_name: image.registry_name})
    ON CREATE SET i.firstseen = timestamp()
    SET
        i.lastupdated = $update_tag,
        i.created_time = image.created_time,
        i.last_update_time = image.last_update_time,
        i.architecture = image.architecture,
        i.os = image.os,
        i.size = image.size,
        i.size_bytes = image.size_bytes,
        i.tags = image.tags,
        i.media_type = image.media_type,
        i.config_media_type = image.config_media_type,
        i.quarantine_state = image.quarantine_state,
        i.quarantine_details = image.quarantine_details,
        i.subscription_id = image.subscription_id,
        i.resource_group = image.resource_group

    WITH i
    MATCH (repo:AzureContainerRepository{name: $repository_name, registry_name: $registry_name})
    MERGE (repo)-[rel:CONTAINS]->(i)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        images=data_list,
        repository_name=repository_name,
        registry_name=registry_name,
        update_tag=update_tag,
    )


def load_registries(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_registries_tx, subscription_id, data_list, update_tag)


def load_repositories(session: neo4j.Session, registry_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_repositories_tx, registry_id, data_list, update_tag)


def load_images(
    session: neo4j.Session,
    repository_name: str,
    registry_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_images_tx, repository_name, registry_name, data_list, update_tag)


def cleanup_container_registries(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_container_registries_cleanup.json", session, common_job_parameters)


def cleanup_container_repositories(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_container_repositories_cleanup.json", session, common_job_parameters)


def cleanup_container_images(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_container_images_cleanup.json", session, common_job_parameters)


@timeit
def sync(
    session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: Optional[List[str]] = None,
) -> None:
    logger.info("Syncing Azure Container Registries for subscription '%s'", subscription_id)
    tic = time.perf_counter()

    registries = get_registry_list(credentials, subscription_id, regions, common_job_parameters)
    load_registries(session, subscription_id, registries, update_tag)

    for registry in registries:
        logger.info(f"Syncing repositories for registry '{registry['name']}'")
        repositories = get_repository_list(
            credentials,
            subscription_id,
            registry["name"],
            registry["resource_group"],
            common_job_parameters,
        )
        load_repositories(session, registry["id"], repositories, update_tag)

        for repository in repositories:
            logger.info(f"Syncing images for repository '{repository['name']}'")
            images = get_image_list(
                credentials,
                subscription_id,
                registry["name"],
                registry["resource_group"],
                repository["name"],
                common_job_parameters,
            )
            load_images(session, repository["name"], registry["name"], images, update_tag)

    cleanup_container_registries(session, common_job_parameters)
    cleanup_container_repositories(session, common_job_parameters)
    cleanup_container_images(session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process IAM: {toc - tic:0.4f} seconds")
