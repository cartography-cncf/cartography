import logging
import time
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import batch
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_ecr_repositories(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    logger.info("Getting ECR repositories for region '%s'.", region)
    client = boto3_session.client("ecr", region_name=region, config=get_botocore_config())
    paginator = client.get_paginator("describe_repositories")
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page["repositories"])

    return ecr_repositories


@timeit
def transform_repositories(repositories: List[Dict], region: str) -> List[Dict]:
    ecr_repositories = []
    for repo in repositories:
        repo["region"] = region
        repo["consolelink"] = aws_console_link.get_console_link(arn=repo["repositoryArn"])
        ecr_repositories.append(repo)

    return ecr_repositories


@timeit
@aws_handle_regions
def get_ecr_repository_images(
    boto3_session: boto3.session.Session,
    region: str,
    repository_name: str,
    current_aws_account_id: str,
) -> List[Dict]:
    logger.debug("Getting ECR images in repository '%s' for region '%s'.", repository_name, region)
    client = boto3_session.client("ecr", region_name=region, config=get_botocore_config())
    paginator = client.get_paginator("list_images")
    ecr_repository_images: List[Dict] = []
    for page in paginator.paginate(repositoryName=repository_name, maxResults=10):
        ecr_repository_images.extend(page["imageIds"])

    for image in ecr_repository_images:
        image["region"] = region
        # image["consolelink"] = aws_console_link.get_console_link(
        #     arn=f"arn:aws:ecr::{current_aws_account_id}:image/{repository_name}:{image.get('imageTag', image.get('imageDigest'))}"
        # )

    return ecr_repository_images


@timeit
def load_ecr_repositories(
    neo4j_session: neo4j.Session,
    repos: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query = """
    UNWIND $Repositories as ecr_repo
        MERGE (repo:ECRRepository{id: ecr_repo.repositoryArn})
        ON CREATE SET repo.firstseen = timestamp(),
            repo.arn = ecr_repo.repositoryArn,
            repo.name = ecr_repo.repositoryName,
            repo.consolelink = ecr_repo.consolelink,
            repo.region = ecr_repo.region,
            repo.created_at = ecr_repo.createdAt
        SET repo.lastupdated = $aws_update_tag,
            repo.uri = ecr_repo.repositoryUri
        WITH repo

        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(repo)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        query,
        Repositories=repos,
        aws_update_tag=aws_update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    ).consume()  # See issue #440


@timeit
def transform_ecr_repository_images(repo_data: Dict) -> List[Dict]:
    """
    Ensure that we only load ECRImage nodes to the graph if they have a defined imageDigest field.
    """
    repo_images_list = []
    for repo_uri, repo_images in repo_data.items():
        for img in repo_images:
            if "imageDigest" in img and img["imageDigest"]:
                img["repo_uri"] = repo_uri
                repo_images_list.append(img)
            else:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get("imageTag"),
                )

    return repo_images_list


def _load_ecr_repo_img_tx(
    tx: neo4j.Transaction,
    repo_images_list: List[Dict],
    aws_update_tag: int,
) -> None:
    query = """
    UNWIND $RepoList as repo_img
        MERGE (ri:ECRRepositoryImage{id: repo_img.repo_uri + COALESCE(":" + repo_img.imageTag, '')})
        ON CREATE SET ri.firstseen = timestamp()
        SET ri.lastupdated = $aws_update_tag,
            ri.tag = repo_img.imageTag,
            ri.uri = repo_img.repo_uri + COALESCE(":" + repo_img.imageTag, ''),
            ri.digest = repo_img.imageDigest,
            ri.region = repo_img.region,
            ri.consolelink = repo_img.consolelink
        WITH ri, repo_img

        MERGE (img:ECRImage{id: repo_img.imageDigest})
        ON CREATE SET img.firstseen = timestamp(),
            img.digest = repo_img.imageDigest
        SET img.lastupdated = $aws_update_tag,
            img.region = repo_img.region,
            img.consolelink = repo_img.consolelink
        WITH ri, img, repo_img

        MERGE (ri)-[r1:IMAGE]->(img)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $aws_update_tag
        WITH ri, repo_img

        MATCH (repo:ECRRepository{uri: repo_img.repo_uri})
        MERGE (repo)-[r2:REPO_IMAGE]->(ri)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
    """
    tx.run(query, RepoList=repo_images_list, aws_update_tag=aws_update_tag)


@timeit
def load_ecr_repository_images(
    neo4j_session: neo4j.Session,
    repo_images_list: List[Dict],
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(repo_images_list)} ECR repository images into graph.")
    for repo_image_batch in batch(repo_images_list, size=500):
        neo4j_session.execute_write(_load_ecr_repo_img_tx, repo_image_batch, aws_update_tag)


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running ECR cleanup job.")
    run_cleanup_job("aws_import_ecr_cleanup.json", neo4j_session, common_job_parameters)


def _get_image_data(
    boto3_session: boto3.session.Session,
    region: str,
    repositories: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Given a list of repositories, get the image data for each repository,
    return as a mapping from repositoryUri to image object
    """
    image_data = {}

    async def async_get_images(repo: Dict[str, Any]) -> None:
        repo_image_obj = await to_asynchronous(get_ecr_repository_images, boto3_session, region, repo["repositoryName"])
        image_data[repo["repositoryUri"]] = repo_image_obj

    to_synchronous(*[async_get_images(repo) for repo in repositories])

    return image_data


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing ECR for account '%s', at %s.", current_aws_account_id, tic)

    repositories = []
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        repos = get_ecr_repositories(boto3_session, region)
        repositories.extend(transform_repositories(repos, region))

    logger.info(f"Total ECR Repositories: {len(repositories)}")

    load_ecr_repositories(neo4j_session, repositories, current_aws_account_id, update_tag)

    image_data = {}
    for repo in repositories:
        repo_image_obj = get_ecr_repository_images(
            boto3_session,
            repo["region"],
            repo["repositoryName"],
            current_aws_account_id,
        )
        image_data[repo["repositoryUri"]] = repo_image_obj

    repo_images_list = transform_ecr_repository_images(image_data)
    load_ecr_repository_images(neo4j_session, repo_images_list, update_tag)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process ECR: {toc - tic:0.4f} seconds")
