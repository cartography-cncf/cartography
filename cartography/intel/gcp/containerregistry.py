import logging
import time
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


def get_artifact_registry_client(credentials, project_id: str) -> Resource:
    from googleapiclient.discovery import build

    return build("artifactregistry", "v1", credentials=credentials)


def get_container_registry_client(credentials, project_id: str) -> Resource:
    from googleapiclient.discovery import build

    return build("containerregistry", "v1alpha1", credentials=credentials)


def get_artifact_registry_repositories(
    client: Resource,
    project_id: str,
    locations: Optional[List[str]],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        repositories = []

        # If no locations specified, get all available locations
        if not locations:
            locations_req = client.projects().locations().list(name=f"projects/{project_id}")
            locations_result = locations_req.execute()
            locations = [loc["locationId"] for loc in locations_result.get("locations", [])]

        for location in locations:
            try:
                parent = f"projects/{project_id}/locations/{location}"
                req = client.projects().locations().repositories().list(parent=parent)

                while req:
                    result = req.execute()

                    if result.get("repositories"):
                        for repo in result["repositories"]:
                            repo_dict = {
                                "name": repo["name"],
                                "display_name": repo.get("displayName", ""),
                                "description": repo.get("description", ""),
                                "format": repo.get("format", ""),
                                "location": location,
                                "project_id": project_id,
                                "create_time": repo.get("createTime", ""),
                                "update_time": repo.get("updateTime", ""),
                                "kms_key_name": repo.get("kmsKeyName", ""),
                                "size_bytes": repo.get("sizeBytes", 0),
                                "labels": repo.get("labels", {}),
                                "console_link": gcp_console_link.get_console_link(
                                    project_id=project_id,
                                    resource_name="artifact_registry_repository",
                                    location=location,
                                    repository_name=repo["name"].split("/")[-1],
                                ),
                            }
                            repositories.append(repo_dict)

                    req = client.projects().locations().repositories().list_next(req, result)

            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(f"Access denied for Artifact Registry in location {location}: {e}")
                else:
                    logger.warning(f"Failed to retrieve Artifact Registry repositories in {location}: {e}")

        return repositories

    except HttpError as e:
        logger.warning(f"Failed to retrieve Artifact Registry repositories for project {project_id}: {e}")
        return []


def get_container_registry_repositories(
    client: Resource,
    project_id: str,
    locations: Optional[List[str]],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        repositories = []

        # Container Registry uses specific regional hostnames
        if not locations:
            gcr_locations = ["us", "eu", "asia"]
        else:
            gcr_locations = locations

        for location in gcr_locations:
            try:
                # Get repositories from Container Registry
                hostname = f"{location}.gcr.io" if location != "us" else "gcr.io"
                req = (
                    client.projects()
                    .locations()
                    .repositories()
                    .list(
                        parent=f"projects/{project_id}/locations/{location}",
                    )
                )

                try:
                    result = req.execute()
                    for repo in result.get("repositories", []):
                        repo_dict = {
                            "name": repo["name"],
                            "display_name": repo.get("displayName", f"Container Registry - {location}"),
                            "description": repo.get("description", f"Google Container Registry in {location}"),
                            "format": "DOCKER",
                            "location": location,
                            "project_id": project_id,
                            "create_time": repo.get("createTime", ""),
                            "update_time": repo.get("updateTime", ""),
                            "kms_key_name": "",
                            "size_bytes": 0,
                            "labels": {},
                            "console_link": gcp_console_link.get_console_link(
                                project_id=project_id,
                                resource_name="container_registry",
                            ),
                        }
                        repositories.append(repo_dict)
                except HttpError as e:
                    if e.resp.status == 404:
                        # No repositories in this location, create a placeholder
                        repo_dict = {
                            "name": f"projects/{project_id}/locations/{location}/repositories/gcr.io",
                            "display_name": f"Container Registry - {location}",
                            "description": f"Google Container Registry in {location}",
                            "format": "DOCKER",
                            "location": location,
                            "project_id": project_id,
                            "create_time": "",
                            "update_time": "",
                            "kms_key_name": "",
                            "size_bytes": 0,
                            "labels": {},
                            "console_link": gcp_console_link.get_console_link(
                                project_id=project_id,
                                resource_name="container_registry",
                            ),
                        }
                        repositories.append(repo_dict)

            except Exception as e:
                logger.warning(f"Failed to process Container Registry in {location}: {e}")

        return repositories

    except Exception as e:
        logger.warning(f"Failed to retrieve Container Registry repositories for project {project_id}: {e}")
        return []


def get_artifact_registry_packages(
    client: Resource,
    project_id: str,
    location: str,
    repository_name: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        packages = []
        parent = f"projects/{project_id}/locations/{location}/repositories/{repository_name}"

        req = client.projects().locations().repositories().packages().list(parent=parent)

        while req:
            result = req.execute()

            if result.get("packages"):
                for package in result["packages"]:
                    package_dict = {
                        "name": package["name"],
                        "display_name": package.get("displayName", ""),
                        "create_time": package.get("createTime", ""),
                        "update_time": package.get("updateTime", ""),
                        "project_id": project_id,
                        "location": location,
                        "repository_name": repository_name,
                    }
                    packages.append(package_dict)

            req = client.projects().locations().repositories().packages().list_next(req, result)

        return packages

    except HttpError as e:
        logger.warning(f"Failed to retrieve packages for repository {repository_name}: {e}")
        return []


def get_artifact_registry_versions(
    client: Resource,
    project_id: str,
    location: str,
    repository_name: str,
    package_name: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        versions = []
        parent = f"projects/{project_id}/locations/{location}/repositories/{repository_name}/packages/{package_name}"

        req = client.projects().locations().repositories().packages().versions().list(parent=parent)

        while req:
            result = req.execute()

            if result.get("versions"):
                for version in result["versions"]:
                    version_dict = {
                        "name": version["name"],
                        "description": version.get("description", ""),
                        "create_time": version.get("createTime", ""),
                        "update_time": version.get("updateTime", ""),
                        "related_tags": version.get("relatedTags", []),
                        "metadata": version.get("metadata", {}),
                        "size_bytes": version.get("sizeBytes", 0),
                        "digest": version.get("name", "").split("/")[-1]
                        if "@sha256:" in version.get("name", "")
                        else "",
                        "architecture": version.get("metadata", {}).get("architecture", ""),
                        "os": version.get("metadata", {}).get("os", ""),
                        "project_id": project_id,
                        "location": location,
                        "repository_name": repository_name,
                        "package_name": package_name,
                    }
                    versions.append(version_dict)

            req = client.projects().locations().repositories().packages().versions().list_next(req, result)

        return versions

    except HttpError as e:
        logger.warning(f"Failed to retrieve versions for package {package_name}: {e}")
        return []


def get_container_registry_images(
    client: Resource,
    project_id: str,
    location: str,
    repository_name: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        images = []
        parent = f"projects/{project_id}/locations/{location}/repositories/{repository_name.split('/')[-1]}"

        req = client.projects().locations().repositories().packages().list(parent=parent)

        while req:
            result = req.execute()

            if result.get("packages"):
                for package in result["packages"]:
                    package_name = package["name"].split("/")[-1]

                    # Get versions (images) for this package
                    versions_req = (
                        client.projects()
                        .locations()
                        .repositories()
                        .packages()
                        .versions()
                        .list(
                            parent=package["name"],
                        )
                    )

                    while versions_req:
                        versions_result = versions_req.execute()

                        if versions_result.get("versions"):
                            for version in versions_result["versions"]:
                                image_dict = {
                                    "name": version["name"],
                                    "package_name": package_name,
                                    "repository_name": repository_name,
                                    "create_time": version.get("createTime", ""),
                                    "update_time": version.get("updateTime", ""),
                                    "related_tags": version.get("relatedTags", []),
                                    "metadata": version.get("metadata", {}),
                                    "size_bytes": version.get("sizeBytes", 0),
                                    "digest": version.get("name", "").split("/")[-1]
                                    if "@sha256:" in version.get("name", "")
                                    else "",
                                    "architecture": version.get("metadata", {}).get("architecture", ""),
                                    "os": version.get("metadata", {}).get("os", ""),
                                    "project_id": project_id,
                                    "location": location,
                                }
                                images.append(image_dict)

                        versions_req = (
                            client.projects()
                            .locations()
                            .repositories()
                            .packages()
                            .versions()
                            .list_next(
                                versions_req,
                                versions_result,
                            )
                        )

            req = client.projects().locations().repositories().packages().list_next(req, result)

        return images

    except HttpError as e:
        logger.warning(f"Failed to retrieve images for repository {repository_name}: {e}")
        return []


def _load_artifact_registry_repositories_tx(
    tx: neo4j.Transaction,
    project_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $repositories as repo
    MERGE (r:GCPArtifactRegistryRepository{name: repo.name})
    ON CREATE SET r.firstseen = timestamp()
    SET
        r.lastupdated = $update_tag,
        r.display_name = repo.display_name,
        r.description = repo.description,
        r.format = repo.format,
        r.location = repo.location,
        r.project_id = repo.project_id,
        r.create_time = repo.create_time,
        r.update_time = repo.update_time,
        r.kms_key_name = repo.kms_key_name,
        r.size_bytes = repo.size_bytes,
        r.labels = repo.labels,
        r.console_link = repo.console_link

    WITH r
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[rel:RESOURCE]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        repositories=data_list,
        project_id=project_id,
        update_tag=update_tag,
    )


def _load_container_registry_repositories_tx(
    tx: neo4j.Transaction,
    project_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $repositories as repo
    MERGE (r:GCPContainerRegistryRepository{name: repo.name})
    ON CREATE SET r.firstseen = timestamp()
    SET
        r.lastupdated = $update_tag,
        r.display_name = repo.display_name,
        r.description = repo.description,
        r.format = repo.format,
        r.location = repo.location,
        r.project_id = repo.project_id,
        r.create_time = repo.create_time,
        r.update_time = repo.update_time,
        r.kms_key_name = repo.kms_key_name,
        r.size_bytes = repo.size_bytes,
        r.labels = repo.labels,
        r.console_link = repo.console_link

    WITH r
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[rel:RESOURCE]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        repositories=data_list,
        project_id=project_id,
        update_tag=update_tag,
    )


def _load_artifact_registry_packages_tx(
    tx: neo4j.Transaction,
    repository_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $packages as pkg
    MERGE (p:GCPArtifactRegistryPackage{name: pkg.name})
    ON CREATE SET p.firstseen = timestamp()
    SET
        p.lastupdated = $update_tag,
        p.display_name = pkg.display_name,
        p.create_time = pkg.create_time,
        p.update_time = pkg.update_time,
        p.project_id = pkg.project_id,
        p.location = pkg.location,
        p.repository_name = pkg.repository_name

    WITH p
    MATCH (r:GCPArtifactRegistryRepository{name: $repository_name})
    MERGE (r)-[rel:CONTAINS]->(p)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        packages=data_list,
        repository_name=repository_name,
        update_tag=update_tag,
    )


def _load_artifact_registry_versions_tx(
    tx: neo4j.Transaction,
    package_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $versions as ver
    MERGE (v:GCPArtifactRegistryVersion{name: ver.name})
    ON CREATE SET v.firstseen = timestamp()
    SET
        v.lastupdated = $update_tag,
        v.description = ver.description,
        v.create_time = ver.create_time,
        v.update_time = ver.update_time,
        v.related_tags = ver.related_tags,
        v.metadata = ver.metadata,
        v.size_bytes = ver.size_bytes,
        v.digest = ver.digest,
        v.architecture = ver.architecture,
        v.os = ver.os,
        v.project_id = ver.project_id,
        v.location = ver.location,
        v.repository_name = ver.repository_name,
        v.package_name = ver.package_name

    WITH v
    MATCH (p:GCPArtifactRegistryPackage{name: $package_name})
    MERGE (p)-[rel:CONTAINS]->(v)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        versions=data_list,
        package_name=package_name,
        update_tag=update_tag,
    )


def _load_container_registry_images_tx(
    tx: neo4j.Transaction,
    repository_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $images as img
    MERGE (i:GCPContainerRegistryImage{name: img.name})
    ON CREATE SET i.firstseen = timestamp()
    SET
        i.lastupdated = $update_tag,
        i.package_name = img.package_name,
        i.repository_name = img.repository_name,
        i.create_time = img.create_time,
        i.update_time = img.update_time,
        i.related_tags = img.related_tags,
        i.metadata = img.metadata,
        i.size_bytes = img.size_bytes,
        i.digest = img.digest,
        i.architecture = img.architecture,
        i.os = img.os,
        i.project_id = img.project_id,
        i.location = img.location

    WITH i
    MATCH (r:GCPContainerRegistryRepository{name: $repository_name})
    MERGE (r)-[rel:CONTAINS]->(i)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_query,
        images=data_list,
        repository_name=repository_name,
        update_tag=update_tag,
    )


def load_artifact_registry_repositories(
    session: neo4j.Session,
    project_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_artifact_registry_repositories_tx, project_id, data_list, update_tag)


def load_container_registry_repositories(
    session: neo4j.Session,
    project_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_container_registry_repositories_tx, project_id, data_list, update_tag)


def load_artifact_registry_packages(
    session: neo4j.Session,
    repository_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_artifact_registry_packages_tx, repository_name, data_list, update_tag)


def load_artifact_registry_versions(
    session: neo4j.Session,
    package_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_artifact_registry_versions_tx, package_name, data_list, update_tag)


def load_container_registry_images(
    session: neo4j.Session,
    repository_name: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_container_registry_images_tx, repository_name, data_list, update_tag)


def cleanup_artifact_registry_repositories(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_artifact_registry_repositories_cleanup.json", session, common_job_parameters)


def cleanup_container_registry_repositories(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_container_registry_repositories_cleanup.json", session, common_job_parameters)


def cleanup_artifact_registry_packages(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_artifact_registry_packages_cleanup.json", session, common_job_parameters)


def cleanup_artifact_registry_versions(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_artifact_registry_versions_cleanup.json", session, common_job_parameters)


def cleanup_container_registry_images(session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gcp_container_registry_images_cleanup.json", session, common_job_parameters)


@timeit
def sync(
    session: neo4j.Session,
    credentials,
    project_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    locations: Optional[List[str]] = None,
) -> None:
    logger.info("Syncing GCP Container Registries for project '%s'", project_id)
    tic = time.perf_counter()

    # Get Artifact Registry repositories
    artifact_registry_client = get_artifact_registry_client(credentials, project_id)
    artifact_repositories = get_artifact_registry_repositories(
        artifact_registry_client,
        project_id,
        locations,
        common_job_parameters,
    )

    load_artifact_registry_repositories(session, project_id, artifact_repositories, update_tag)

    # Sync packages and versions for Artifact Registry repositories only
    for repository in artifact_repositories:
        repo_name = repository["name"].split("/")[-1]
        logger.info(f"Syncing packages for repository '{repo_name}'")

        packages = get_artifact_registry_packages(
            artifact_registry_client,
            project_id,
            repository["location"],
            repo_name,
            common_job_parameters,
        )
        load_artifact_registry_packages(session, repository["name"], packages, update_tag)

        for package in packages:
            pkg_name = package["name"].split("/")[-1]
            logger.info(f"Syncing versions for package '{pkg_name}'")

            versions = get_artifact_registry_versions(
                artifact_registry_client,
                project_id,
                repository["location"],
                repo_name,
                pkg_name,
                common_job_parameters,
            )
            load_artifact_registry_versions(session, package["name"], versions, update_tag)

    cleanup_artifact_registry_repositories(session, common_job_parameters)
    cleanup_artifact_registry_packages(session, common_job_parameters)
    cleanup_artifact_registry_versions(session, common_job_parameters)

    # Get Container Registry repositories (legacy GCR)
    container_registry_client = get_container_registry_client(credentials, project_id)
    container_repositories = get_container_registry_repositories(
        container_registry_client,
        project_id,
        locations,
        common_job_parameters,
    )

    # Load repositories separately
    load_container_registry_repositories(session, project_id, container_repositories, update_tag)

    # Sync images for Container Registry repositories
    for repository in container_repositories:
        repo_name = repository["name"].split("/")[-1]
        logger.info(f"Syncing images for Container Registry repository '{repo_name}'")

        images = get_container_registry_images(
            container_registry_client,
            project_id,
            repository["location"],
            repository["name"],
            common_job_parameters,
        )
        load_container_registry_images(session, repository["name"], images, update_tag)

    cleanup_container_registry_repositories(session, common_job_parameters)
    cleanup_container_registry_images(session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process GCP Container Registries: {toc - tic:0.4f} seconds")
