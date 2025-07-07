from typing import Set
from typing import Tuple

import neo4j

from cartography.client.core.tx import read_list_of_tuples_tx
from cartography.util import timeit


@timeit
def get_ecr_images(
    neo4j_session: neo4j.Session, aws_account_id: str
) -> Set[Tuple[str, str, str, str, str]]:
    """
    Queries the graph for all ECR images and their parent images.
    Returns 5-tuples of ECR repository regions, tags, URIs, names, and binary digests. This is used to identify which
    images to scan.
    :param neo4j_session: The neo4j session object.
    :param aws_account_id: The AWS account ID to get ECR repo data for.
    :return: 5-tuples of repo region, image tag, image URI, repo_name, and image_digest.
    """
    # See https://community.neo4j.com/t/extract-list-of-nodes-and-labels-from-path/13665/4
    query = """
MATCH (e1:ECRRepositoryImage)<-[:REPO_IMAGE]-(repo:ECRRepository)
MATCH (repo)<-[:RESOURCE]-(:AWSAccount {id: $AWS_ID})

// OPTIONAL traversal of parent hierarchy
OPTIONAL MATCH path = (e1)-[:PARENT*1..]->(ancestor:ECRRepositoryImage)
WITH e1,
     CASE
         WHEN path IS NULL THEN [e1]
         ELSE [n IN nodes(path) | n] + [e1]
     END AS repo_img_collection_unflattened

// Flatten and dedupe
UNWIND repo_img_collection_unflattened AS repo_img
WITH DISTINCT repo_img

// Match image metadata
MATCH (er:ECRRepository)-[:REPO_IMAGE]->(repo_img)-[:IMAGE]->(img:ECRImage)

RETURN DISTINCT
    er.region AS region,
    repo_img.tag AS tag,
    repo_img.id AS uri,
    er.name AS repo_name,
    img.digest AS digest
    """
    return neo4j_session.read_transaction(
        read_list_of_tuples_tx, query, AWS_ID=aws_account_id
    )
