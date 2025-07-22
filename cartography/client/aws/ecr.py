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
    Query the graph for all ECR images and their parent images.

    This function retrieves ECR repository images along with their parent image hierarchy,
    returning essential metadata used to identify which images to scan.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session object for database queries.
        aws_account_id (str): The AWS account ID to get ECR repository data for.

    Returns:
        Set[Tuple[str, str, str, str, str]]: A set of 5-tuples containing:
            - repo region (str): The AWS region of the ECR repository
            - image tag (str): The tag of the repository image
            - image URI (str): The URI identifier of the repository image
            - repo name (str): The name of the ECR repository
            - image digest (str): The binary digest of the ECR image

    Note:
        The function uses an optional traversal to include parent images in the hierarchy,
        ensuring all related images are captured for scanning purposes.

    See Also:
        Neo4j Community discussion on extracting nodes from paths:
        https://community.neo4j.com/t/extract-list-of-nodes-and-labels-from-path/13665/4
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
