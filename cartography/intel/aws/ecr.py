import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.repository import ECRRepositorySchema
from cartography.models.aws.ecr.repository_image import ECRRepositoryImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ecr_repositories(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    logger.info("Getting ECR repositories for region '%s'.", region)
    client = boto3_session.client("ecr", region_name=region)
    paginator = client.get_paginator("describe_repositories")
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page["repositories"])
    return ecr_repositories


@timeit
@aws_handle_regions
def get_ecr_repository_images(
    boto3_session: boto3.session.Session, region: str, repository_name: str
) -> List[Dict]:
    logger.debug(
        "Getting ECR images in repository '%s' for region '%s'.",
        repository_name,
        region,
    )
    client = boto3_session.client("ecr", region_name=region)
    list_paginator = client.get_paginator("list_images")
    ecr_repository_images: List[Dict] = []
    for page in list_paginator.paginate(repositoryName=repository_name):
        image_ids = page["imageIds"]
        if not image_ids:
            continue
        describe_paginator = client.get_paginator("describe_images")
        describe_response = describe_paginator.paginate(
            repositoryName=repository_name, imageIds=image_ids
        )
        for response in describe_response:
            image_details = response["imageDetails"]
            image_details = [
                (
                    {**detail, "imageTag": detail["imageTags"][0]}
                    if detail.get("imageTags")
                    else detail
                )
                for detail in image_details
            ]
            ecr_repository_images.extend(image_details)
    return ecr_repository_images


@timeit
def load_ecr_repositories(
    neo4j_session: neo4j.Session,
    repos: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(repos)} ECR repositories for region {region} into graph.",
    )
    load(
        neo4j_session,
        ECRRepositorySchema(),
        repos,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def transform_ecr_repository_images(repo_data: Dict) -> List[Dict]:
    """
    Ensure that we only load ECRImage nodes to the graph if they have a defined imageDigest field.
    Process repositories in a consistent order to handle overlapping image digests deterministically.
    """
    repo_images_list = []
    # Sort repository URIs to ensure consistent processing order
    for repo_uri in sorted(repo_data.keys()):
        repo_images = repo_data[repo_uri]
        for img in repo_images:
            digest = img.get("imageDigest")
            if digest:
                tag = img.get("imageTag")
                uri = repo_uri + (f":{tag}" if tag else "")
                img["repo_uri"] = repo_uri
                img["uri"] = uri
                img["id"] = uri
                repo_images_list.append(img)
            else:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get("imageTag"),
                )

    return repo_images_list


@timeit
def load_ecr_repository_images(
    neo4j_session: neo4j.Session,
    repo_images_list: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(repo_images_list)} ECR repository images in {region} into graph.",
    )
    image_digests = {img["imageDigest"] for img in repo_images_list}
    ecr_images = [{"imageDigest": d} for d in image_digests]

    load(
        neo4j_session,
        ECRImageSchema(),
        ecr_images,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )

    load(
        neo4j_session,
        ECRRepositoryImageSchema(),
        repo_images_list,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running ECR cleanup job.")
    GraphJob.from_node_schema(ECRRepositorySchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECRRepositoryImageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECRImageSchema(), common_job_parameters).run(
        neo4j_session
    )


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
        repo_image_obj = await to_asynchronous(
            get_ecr_repository_images,
            boto3_session,
            region,
            repo["repositoryName"],
        )
        image_data[repo["repositoryUri"]] = repo_image_obj

    # Sort repositories by name to ensure consistent processing order
    sorted_repos = sorted(repositories, key=lambda x: x["repositoryName"])
    to_synchronous(*[async_get_images(repo) for repo in sorted_repos])

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
    for region in regions:
        logger.info(
            "Syncing ECR for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        image_data = {}
        repositories = get_ecr_repositories(boto3_session, region)
        image_data = _get_image_data(boto3_session, region, repositories)
        # len here should be 1!
        load_ecr_repositories(
            neo4j_session,
            repositories,
            region,
            current_aws_account_id,
            update_tag,
        )
        repo_images_list = transform_ecr_repository_images(image_data)
        load_ecr_repository_images(
            neo4j_session,
            repo_images_list,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
