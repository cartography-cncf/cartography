from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail_management_events
import cartography.intel.aws.iam
import cartography.intel.aws.identitycenter
from cartography.intel.aws.cloudtrail_management_events import sync
from cartography.intel.aws.iam import transform_users
from tests.data.aws.cloudtrail_management_events import (
    AGGREGATION_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    BASIC_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    CROSS_ACCOUNT_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    GITHUB_ACTIONS_AGGREGATION_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    GITHUB_ACTIONS_AGGREGATION_IAM_ROLES,
)
from tests.data.aws.cloudtrail_management_events import GITHUB_ACTIONS_IAM_ROLES
from tests.data.aws.cloudtrail_management_events import (
    GITHUB_WEB_IDENTITY_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_IAM_ROLES,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_IAM_USERS,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_BASIC_ACCOUNT_ID,
)
from tests.data.aws.cloudtrail_management_events import INTEGRATION_TEST_BASIC_IAM_ROLES
from tests.data.aws.cloudtrail_management_events import INTEGRATION_TEST_BASIC_IAM_USERS
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_ID,
)
from tests.data.aws.cloudtrail_management_events import (
    SAML_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import TEST_SSO_USERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _cleanup_cloudtrail_test_data(neo4j_session):
    """Clean up CloudTrail test data between tests."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _ensure_local_neo4j_has_basic_test_data(neo4j_session):
    """Set up test IAM users and roles for basic relationships test."""
    # Transform and load test users using cartography's IAM loader
    user_data = transform_users(INTEGRATION_TEST_BASIC_IAM_USERS)
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_data,
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test roles using cartography's IAM loader
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": INTEGRATION_TEST_BASIC_IAM_ROLES},
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create cross-account role using IAM loader with different account
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {
            "Roles": [
                {
                    "RoleName": "CrossAccountRole",
                    "RoleId": "AROA00000000CROSSACCOUNT",
                    "Arn": "arn:aws:iam::987654321098:role/CrossAccountRole",
                    "Path": "/",
                    "CreateDate": "2024-01-01T10:00:00Z",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    },
                }
            ]
        },
        "987654321098",  # Different account ID
        TEST_UPDATE_TAG,
    )

    # Load AWSSSOUser nodes using identity center loader
    cartography.intel.aws.identitycenter.load_sso_users(
        neo4j_session,
        cartography.intel.aws.identitycenter.transform_sso_users(TEST_SSO_USERS),
        "d-1234567890",  # identity_store_id
        TEST_REGION,
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_aggregation_test_data(neo4j_session):
    """Set up test IAM users and roles for aggregation test."""
    # Transform and load test users using cartography's IAM loader
    user_data = transform_users(INTEGRATION_TEST_AGGREGATION_IAM_USERS)
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_data,
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": INTEGRATION_TEST_AGGREGATION_IAM_ROLES},
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_cross_account_test_data(neo4j_session):
    """Set up test IAM users and roles for cross-account test."""
    # Transform and load test users using cartography's IAM loader
    user_data = transform_users(INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS)
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_data,
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES},
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create external role using IAM loader with different account
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {
            "Roles": [
                {
                    "RoleName": "ExternalRole",
                    "RoleId": "AROA00000000EXTERNAL",
                    "Arn": "arn:aws:iam::333333333333:role/ExternalRole",
                    "Path": "/",
                    "CreateDate": "2024-01-01T10:00:00Z",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "arn:aws:iam::222222222222:root"},
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    },
                }
            ]
        },
        "333333333333",  # Different account ID
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=BASIC_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=[],
)
def test_cloudtrail_management_events_creates_assumed_role_relationships(
    mock_get_saml_events, mock_get_assume_role_events, neo4j_session
):
    """
    Test that CloudTrail AssumeRole events create ASSUMED_ROLE relationships
    between existing principals and roles.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_BASIC_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_basic_test_data(neo4j_session)

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_BASIC_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::123456789012:user/john.doe",
            "arn:aws:iam::123456789012:role/ApplicationRole",
        ),
    }


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=AGGREGATION_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=[],
)
def test_cloudtrail_management_events_aggregates_multiple_role_assumptions(
    mock_get_saml_events, mock_get_assume_role_events, neo4j_session
):
    """
    Test that multiple CloudTrail AssumeRole events for the same
    (source, destination) pair are aggregated into a single relationship.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_aggregation_test_data(neo4j_session)

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert: Single aggregated relationship created
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::111111111111:user/test-user",
            "arn:aws:iam::111111111111:role/TestRole",
        ),
    }

    # Assert: Aggregated properties reflect multiple uses
    aggregated_usage = neo4j_session.run(
        """
        MATCH (p:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/test-user'})
              -[r:ASSUMED_ROLE]->
              (role:AWSRole {arn: 'arn:aws:iam::111111111111:role/TestRole'})
        RETURN r.times_used as times_used, r.first_seen_in_time_window as first_seen_in_time_window,
               r.last_used as last_used
        """
    ).single()

    assert aggregated_usage["times_used"] == 3
    assert aggregated_usage["first_seen_in_time_window"] == "2024-01-15T09:00:00.000000"
    assert aggregated_usage["last_used"] == "2024-01-15T17:00:00.000000"


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=CROSS_ACCOUNT_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=[],
)
def test_cloudtrail_management_events_handles_cross_account_relationships(
    mock_get_saml_events, mock_get_assume_role_events, neo4j_session
):
    """
    Test that CloudTrail events create ASSUMED_ROLE relationships
    even when source and destination are in different AWS accounts.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_CROSS_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_cross_account_test_data(neo4j_session)

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_CROSS_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::222222222222:user/cross-user",
            "arn:aws:iam::333333333333:role/ExternalRole",
        ),
    }


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=SAML_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
def test_cloudtrail_management_events_creates_assumed_role_with_saml_relationships(
    mock_get_saml_events, mock_get_assume_role_events, neo4j_session
):
    """
    Test that CloudTrail SAML management events create ASSUMED_ROLE_WITH_SAML relationships
    between AWSSSOUser nodes and roles.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_BASIC_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_basic_test_data(neo4j_session)

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_BASIC_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSSSOUser",
        "user_name",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE_WITH_SAML",
        rel_direction_right=True,
    ) == {
        ("admin@example.com", "arn:aws:iam::123456789012:role/ApplicationRole"),
        ("alice@example.com", "arn:aws:iam::987654321098:role/CrossAccountRole"),
    }

    # Assert: Verify SAML usage properties
    saml_role_usage_results = neo4j_session.run(
        """
        MATCH (p:AWSSSOUser)-[r:ASSUMED_ROLE_WITH_SAML]->(role:AWSRole)
        WHERE p.user_name IN ['admin@example.com', 'alice@example.com']
        RETURN r.times_used as times_used, r.last_used as last_used
        """
    ).data()

    assert len(saml_role_usage_results) == 2
    for usage in saml_role_usage_results:
        assert usage["times_used"] == 1
        assert usage["last_used"] is not None


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_web_identity_role_events",
    return_value=GITHUB_WEB_IDENTITY_CLOUDTRAIL_EVENTS,
)
def test_cloudtrail_management_events_creates_assumed_role_with_web_identity_relationships(
    mock_get_web_identity_events,
    mock_get_saml_events,
    mock_get_assume_role_events,
    neo4j_session,
):
    """
    Test that CloudTrail GitHub Actions events create ASSUMED_ROLE_WITH_WEB_IDENTITY relationships
    between GitHubRepository nodes and AWS roles with user tracking.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_BASIC_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_basic_test_data(neo4j_session)

    # Create AWS roles that GitHub repos will assume
    github_target_roles = GITHUB_ACTIONS_IAM_ROLES

    # Use IAM loader to create target roles
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": github_target_roles},
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create GitHubRepository nodes that will be the source of the relationships
    neo4j_session.run(
        """
        CREATE (repo1:GitHubRepository {
            fullname: 'sublimagesec/sublimage',
            name: 'sublimage',
            id: 'https://github.com/sublimagesec/sublimage',
            lastupdated: $update_tag
        }),
        (repo2:GitHubRepository {
            fullname: 'myorg/demo-app',
            name: 'demo-app',
            id: 'https://github.com/myorg/demo-app',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_BASIC_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert: Verify GitHubRepository nodes exist
    repo_nodes = check_nodes(neo4j_session, "GitHubRepository", ["fullname"])
    expected_repos = {
        ("sublimagesec/sublimage",),
        ("myorg/demo-app",),
    }
    assert repo_nodes is not None and expected_repos.issubset(repo_nodes)

    # Assert: Verify ASSUMED_ROLE_WITH_WEB_IDENTITY relationships exist
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "fullname",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE_WITH_WEB_IDENTITY",
        rel_direction_right=True,
    ) == {
        ("sublimagesec/sublimage", "arn:aws:iam::123456789012:role/GitHubActionsRole"),
        ("myorg/demo-app", "arn:aws:iam::987654321098:role/CrossAccountGitHubRole"),
    }

    # Assert: Verify WebIdentity usage properties including user tracking
    web_identity_role_usage_results = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository)-[r:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(role:AWSRole)
        WHERE repo.fullname IN ['sublimagesec/sublimage', 'myorg/demo-app']
        RETURN repo.fullname as repo_fullname, r.times_used as times_used, r.last_used as last_used
        """
    ).data()

    assert len(web_identity_role_usage_results) == 2

    # Create lookup by repo for easier assertions
    usage_by_repo = {
        result["repo_fullname"]: result for result in web_identity_role_usage_results
    }

    # Verify sublimagesec/sublimage repo relationship
    sublimage_usage = usage_by_repo["sublimagesec/sublimage"]
    assert sublimage_usage["times_used"] == 1
    assert sublimage_usage["last_used"] is not None

    # Verify myorg/demo-app repo relationship
    demo_app_usage = usage_by_repo["myorg/demo-app"]
    assert demo_app_usage["times_used"] == 1
    assert demo_app_usage["last_used"] is not None


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_saml_role_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_web_identity_role_events",
    return_value=GITHUB_ACTIONS_AGGREGATION_CLOUDTRAIL_EVENTS,
)
def test_cloudtrail_web_identity_events_aggregates_multiple_users_and_tracks_individuals(
    mock_get_web_identity_events,
    mock_get_saml_events,
    mock_get_assume_role_events,
    neo4j_session,
):
    """
    Test that multiple GitHub Actions events from the same repository
    are aggregated into a single relationship with proper event tracking.
    """
    # Arrange
    _cleanup_cloudtrail_test_data(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_aggregation_test_data(neo4j_session)

    # Create role that GitHub repo will assume
    github_roles = GITHUB_ACTIONS_AGGREGATION_IAM_ROLES

    # Use IAM loader to create target role
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": github_roles},
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create GitHubRepository node
    neo4j_session.run(
        """
        CREATE (repo:GitHubRepository {
            fullname: 'myorg/test-repo',
            name: 'test-repo',
            id: 'https://github.com/myorg/test-repo',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    # Assert: Single aggregated relationship created
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "fullname",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE_WITH_WEB_IDENTITY",
        rel_direction_right=True,
    ) == {
        ("myorg/test-repo", "arn:aws:iam::111111111111:role/GitHubTestRole"),
    }

    # Assert: Aggregated properties reflect multiple events from same repo
    aggregated_usage = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository {fullname: 'myorg/test-repo'})
              -[r:ASSUMED_ROLE_WITH_WEB_IDENTITY]->
              (role:AWSRole {arn: 'arn:aws:iam::111111111111:role/GitHubTestRole'})
        RETURN r.times_used as times_used, r.first_seen_in_time_window as first_seen_in_time_window,
               r.last_used as last_used
        """
    ).single()

    # Verify aggregation counts
    assert aggregated_usage["times_used"] == 3
    assert aggregated_usage["first_seen_in_time_window"] == "2024-01-15T09:10:25.123000"
    assert aggregated_usage["last_used"] == "2024-01-15T14:15:30.456000"
