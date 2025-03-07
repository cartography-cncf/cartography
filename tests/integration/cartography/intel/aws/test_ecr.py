import datetime
import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr
import tests.data.aws.ecr
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session):
    repo_data = tests.data.aws.ecr.DESCRIBE_REPOSITORIES
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data['repositories'],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.ecr,
    'get_ecr_repositories',
    return_value=tests.data.aws.ecr.DESCRIBE_REPOSITORIES['repositories'],
)
@patch.object(
    cartography.intel.aws.ecr,
    'get_ecr_repository_images',
    side_effect=[
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES['000000000000.dkr.ecr.us-east-1/example-repository'],
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES['000000000000.dkr.ecr.us-east-1/sample-repository'],
        tests.data.aws.ecr.LIST_REPOSITORY_IMAGES['000000000000.dkr.ecr.us-east-1/test-repository'],
    ],
)
def test_sync_ecr(mock_get_images, mock_get_repos, neo4j_session):
    """
    Ensure that ECR repositories and images are properly synced and connected
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert ECR repositories exist
    assert check_nodes(neo4j_session, 'ECRRepository', ['id', 'name']) == {
        ('arn:aws:ecr:us-east-1:000000000000:repository/example-repository', 'example-repository'),
        ('arn:aws:ecr:us-east-1:000000000000:repository/sample-repository', 'sample-repository'),
        ('arn:aws:ecr:us-east-1:000000000000:repository/test-repository', 'test-repository'),
    }

    # Assert ECR images exist (excluding those without digests)
    assert check_nodes(neo4j_session, 'ECRImage', ['id', 'digest']) == {
        (
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
        ),
        (
            'sha256:0000000000000000000000000000000000000000000000000000000000000001',
            'sha256:0000000000000000000000000000000000000000000000000000000000000001',
        ),
        (
            'sha256:0000000000000000000000000000000000000000000000000000000000000011',
            'sha256:0000000000000000000000000000000000000000000000000000000000000011',
        ),
        (
            'sha256:0000000000000000000000000000000000000000000000000000000000000021',
            'sha256:0000000000000000000000000000000000000000000000000000000000000021',
        ),
        (
            'sha256:0000000000000000000000000000000000000000000000000000000000000031',
            'sha256:0000000000000000000000000000000000000000000000000000000000000031',
        ),
    }

    # Assert ECR repository images exist
    assert check_nodes(neo4j_session, 'ECRRepositoryImage', ['id', 'tag', 'image_size_bytes', 'image_pushed_at']) == {
        ('000000000000.dkr.ecr.us-east-1/example-repository:1', '1', 1024, '2025-01-01T00:00:00.000000-00:00'),
        ('000000000000.dkr.ecr.us-east-1/example-repository:2', '2', 1024, '2025-01-01T00:00:00.000000-00:00'),
        ('000000000000.dkr.ecr.us-east-1/sample-repository:1', '1', 1024, '2025-01-01T00:00:00.000000-00:00'),
        ('000000000000.dkr.ecr.us-east-1/sample-repository:2', '2', 1024, '2025-01-01T00:00:00.000000-00:00'),
        (
            '000000000000.dkr.ecr.us-east-1/test-repository:1234567890', '1234567890', 1024,
            '2025-01-01T00:00:00.000000-00:00',
        ),
        ('000000000000.dkr.ecr.us-east-1/test-repository:1', '1', 1024, '2025-01-01T00:00:00.000000-00:00'),
        ('000000000000.dkr.ecr.us-east-1/test-repository', None, 1024, '2025-01-01T00:00:00.000000-00:00'),
    }

    # Assert repository to AWS account relationship
    assert check_rels(
        neo4j_session,
        'ECRRepository',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('arn:aws:ecr:us-east-1:000000000000:repository/example-repository', '000000000000'),
        ('arn:aws:ecr:us-east-1:000000000000:repository/sample-repository', '000000000000'),
        ('arn:aws:ecr:us-east-1:000000000000:repository/test-repository', '000000000000'),
    }

    # Assert repository to repository image relationship
    assert check_rels(
        neo4j_session,
        'ECRRepository',
        'uri',
        'ECRRepositoryImage',
        'id',
        'REPO_IMAGE',
        rel_direction_right=True,
    ) == {
        ('000000000000.dkr.ecr.us-east-1/example-repository', '000000000000.dkr.ecr.us-east-1/example-repository:1'),
        ('000000000000.dkr.ecr.us-east-1/example-repository', '000000000000.dkr.ecr.us-east-1/example-repository:2'),
        ('000000000000.dkr.ecr.us-east-1/sample-repository', '000000000000.dkr.ecr.us-east-1/sample-repository:1'),
        ('000000000000.dkr.ecr.us-east-1/sample-repository', '000000000000.dkr.ecr.us-east-1/sample-repository:2'),
        ('000000000000.dkr.ecr.us-east-1/test-repository', '000000000000.dkr.ecr.us-east-1/test-repository:1234567890'),
        ('000000000000.dkr.ecr.us-east-1/test-repository', '000000000000.dkr.ecr.us-east-1/test-repository:1'),
        ('000000000000.dkr.ecr.us-east-1/test-repository', '000000000000.dkr.ecr.us-east-1/test-repository'),
    }

    # Assert repository image to image relationship
    assert check_rels(
        neo4j_session,
        'ECRRepositoryImage',
        'id',
        'ECRImage',
        'id',
        'IMAGE',
        rel_direction_right=True,
    ) == {
        (
            '000000000000.dkr.ecr.us-east-1/example-repository:1',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/example-repository:2',
            'sha256:0000000000000000000000000000000000000000000000000000000000000001',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/sample-repository:1',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/sample-repository:2',
            'sha256:0000000000000000000000000000000000000000000000000000000000000011',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/test-repository:1234567890',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/test-repository:1',
            'sha256:0000000000000000000000000000000000000000000000000000000000000021',
        ),
        (
            '000000000000.dkr.ecr.us-east-1/test-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000031',
        ),
    }

    # Clean up the database after the test
    neo4j_session.run("MATCH (n) detach delete n")


def test_load_ecr_repositories(neo4j_session):
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    expected_nodes = {
        "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ECRRepository) RETURN r.arn;
        """,
    )
    actual_nodes = {n['r.arn'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_cleanup_repositories(neo4j_session):
    '''
    Ensure that after the cleanup job runs, all ECRRepository nodes
    with a different UPDATE_TAG are removed from the AWSAccount node.
    We load 100 additional nodes, because the cleanup job is configured
    to run iteratively, processing 100 nodes at a time. So this test also ensures
    that iterative cleanups do work.
    '''
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    repo_data = {**tests.data.aws.ecr.DESCRIBE_REPOSITORIES}
    # add additional repository noes, for a total of 103, since
    cleanup_jobs = json.load(open('./cartography/data/jobs/cleanup/aws_import_ecr_cleanup.json'))
    iter_size = cleanup_jobs['statements'][-1]['iterationsize']
    repo_data['repositories'].extend([
        {
            'repositoryArn': f'arn:aws:ecr:us-east-1:000000000000:repository/test-repository{i}',
            'registryId': '000000000000',
            'repositoryName': f'test-repository{i}',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/test-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        }
        for i in range(iter_size)
    ])

    # Act
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data['repositories'],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    common_job_params = {
        'AWS_ID': TEST_ACCOUNT_ID,
        'UPDATE_TAG': TEST_UPDATE_TAG,
    }
    nodes = neo4j_session.run(
        f"""
        MATCH (a:AWSAccount{{id:'{TEST_ACCOUNT_ID}'}})--(repo:ECRRepository)
        RETURN count(repo)
        """,
    )
    # there should be 103 nodes
    expected_nodes = {
        len(repo_data['repositories']),
    }
    actual_nodes = {(n['count(repo)']) for n in nodes}
    # Assert
    assert expected_nodes == actual_nodes

    # Arrange
    additional_repo_data = {
        'repositories': [
            {
                'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/test-repositoryX',
                'registryId': '000000000000',
                'repositoryName': 'test-repositoryX',
                'repositoryUri': '000000000000.dkr.ecr.us-east-1/test-repository',
                'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
            },
        ],
    }
    additional_update_tag = 2
    common_job_params['UPDATE_TAG'] = additional_update_tag
    # Act
    # load an additional node with a different update_tag
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        additional_repo_data['repositories'],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        additional_update_tag,
    )
    # run the cleanup job
    cartography.intel.aws.ecr.cleanup(neo4j_session, common_job_params)
    nodes = neo4j_session.run(
        f"""
        MATCH (a:AWSAccount{{id:'{TEST_ACCOUNT_ID}'}})--(repo:ECRRepository)
        RETURN repo.arn, repo.lastupdated
        """,
    )
    actual_nodes = {(n['repo.arn'], n['repo.lastupdated']) for n in nodes}
    # there should be just one remaining node with the new update_tag
    expected_nodes = {
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/test-repositoryX',
            additional_update_tag,
        ),
    }

    # Assert
    assert expected_nodes == actual_nodes


def test_load_ecr_repository_images(neo4j_session):
    """
    Ensure the connection (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage) exists.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list = cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo ARN, image tag)
    expected_nodes = {
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            '1',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            '2',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo:ECRRepository{id:"arn:aws:ecr:us-east-1:000000000000:repository/example-repository"})
        -[:REPO_IMAGE]->(image:ECRRepositoryImage)
        RETURN repo.arn, image.tag;
        """,
    )
    actual_nodes = {(n['repo.arn'], n['image.tag']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_ecr_images(neo4j_session):
    """
    Ensure the connection (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage) exists.
    A single ECRImage may be referenced by many ECRRepositoryImages.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list = cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo image ARN, image SHA)
    expected_nodes = {
        (
            "000000000000.dkr.ecr.us-east-1/test-repository:1234567890",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1/sample-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1/example-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo_image:ECRRepositoryImage)-[:IMAGE]->
        (image:ECRImage{digest:"sha256:0000000000000000000000000000000000000000000000000000000000000000"})
        RETURN repo_image.id, image.digest;
        """,
    )
    actual_nodes = {(n['repo_image.id'], n['image.digest']) for n in nodes}
    assert actual_nodes == expected_nodes
