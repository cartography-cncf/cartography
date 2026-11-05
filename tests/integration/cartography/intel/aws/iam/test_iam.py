import copy
import itertools
from datetime import datetime
from datetime import timezone
from unittest import mock
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam
from cartography.client.core.tx import load
from cartography.intel.aws.iam import _transform_policy_statements
from cartography.intel.aws.iam import sync_root_principal
from cartography.models.aws.iam.inline_policy import AWSInlinePolicySchema
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_permission_relationships_file_arguments():
    """
    Test that we correctly read arguments for --permission-relationships-file
    """
    from cartography.config import Config

    # Test the correct field is set in the Cartography config object
    fname = "/some/test/file.yaml"
    config = Config(
        neo4j_uri="bolt://thisdoesnotmatter:1234",
        permission_relationships_file=fname,
    )
    assert config.permission_relationships_file == fname

    # Test the default value
    config_default = Config(neo4j_uri="bolt://thisdoesnotmatter:1234")
    assert config_default.permission_relationships_file is None


def test_permission_relationships_file_cli():
    """
    Test that CLI correctly passes --permission-relationships-file to Config
    """
    from cartography.cli import CLI

    captured_config = None

    def capture_run_with_config(sync, config):
        nonlocal captured_config
        captured_config = config

    # Test custom file path
    with mock.patch(
        "cartography.sync.run_with_config", side_effect=capture_run_with_config
    ):
        cli = CLI(prog="cartography")
        cli.main(["--permission-relationships-file", "/some/test/file.yaml"])
    assert captured_config.permission_relationships_file == "/some/test/file.yaml"

    # Test default value
    captured_config = None
    with mock.patch(
        "cartography.sync.run_with_config", side_effect=capture_run_with_config
    ):
        cli = CLI(prog="cartography")
        cli.main([])
    assert (
        captured_config.permission_relationships_file
        == "cartography/data/permission_relationships.yaml"
    )


def _create_base_account(neo4j_session):
    neo4j_session.run("MERGE (a:AWSAccount{id:$AccountId})", AccountId=TEST_ACCOUNT_ID)
    # Hack to create the root principal node since we're not calling the full sync() function in this test.
    sync_root_principal(
        neo4j_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        "aws",
    )


def test_load_users(neo4j_session):
    _create_base_account(neo4j_session)
    user_data = cartography.intel.aws.iam.transform_users(
        tests.data.aws.iam.LIST_USERS["Users"]
    )
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_groups(neo4j_session):
    # Create a mock boto3 session for the test
    mock_boto3_session = MagicMock()
    mock_boto3_session.client.return_value.get_group.return_value = {"Users": []}

    # Get group memberships
    group_memberships = cartography.intel.aws.iam.get_group_memberships(
        mock_boto3_session, tests.data.aws.iam.LIST_GROUPS["Groups"]
    )

    # Transform groups with membership data
    group_data = cartography.intel.aws.iam.transform_groups(
        tests.data.aws.iam.LIST_GROUPS["Groups"], group_memberships
    )

    cartography.intel.aws.iam.load_groups(
        neo4j_session,
        group_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


SERVICE_ACCESS_ACCOUNT_ID = "000000000001"
USER_A_ARN = "arn:aws:iam::000000000001:user/example-user-a"
USER_B_ARN = "arn:aws:iam::000000000001:user/example-user-b"
USER_C_ARN = "arn:aws:iam::000000000001:user/example-user-c"

COMPLETED_JOB = tests.data.aws.iam.SERVICE_LAST_ACCESSED_DETAILS
FIRST_PAGE_OF_COMPLETED_JOB = (
    tests.data.aws.iam.SERVICE_LAST_ACCESSED_DETAILS_FIRST_PAGE
)
LAST_PAGE_OF_COMPLETED_JOB = tests.data.aws.iam.SERVICE_LAST_ACCESSED_DETAILS_LAST_PAGE
IN_PROGRESS_JOB = {"JobStatus": "IN_PROGRESS"}
FAILED_JOB = {"JobStatus": "FAILED"}
THROTTLED_POLL = ClientError(
    {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
    "GetServiceLastAccessedDetails",
)
IAM_EXCEPTIONS = boto3.session.Session(region_name=TEST_REGION).client("iam").exceptions
PRINCIPAL_NOT_FOUND = IAM_EXCEPTIONS.NoSuchEntityException(
    {"Error": {"Code": "NoSuchEntity", "Message": "not found"}},
    "GenerateServiceLastAccessedDetails",
)
GENERATE_ACCESS_DENIED = ClientError(
    {"Error": {"Code": "AccessDenied", "Message": "not authorized"}},
    "GenerateServiceLastAccessedDetails",
)
POLL_ACCESS_DENIED = ClientError(
    {"Error": {"Code": "AccessDenied", "Message": "not authorized"}},
    "GetServiceLastAccessedDetails",
)
INVALID_CREDENTIALS = ClientError(
    {"Error": {"Code": "InvalidClientTokenId", "Message": "invalid token"}},
    "GenerateServiceLastAccessedDetails",
)
GENERATE_THROTTLED = ClientError(
    {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
    "GenerateServiceLastAccessedDetails",
)
IAM_UNREACHABLE = ConnectTimeoutError(endpoint_url="https://iam.amazonaws.com/")

EC2_ACCESS = (
    "Amazon EC2",
    "ec2",
    "2019-01-02 00:00:01",
    "role/example-role-0",
    "us-west-2",
)
PREVIOUS_ACCESS = (
    "Amazon S3",
    "s3",
    "2018-06-01 00:00:00+00:00",
    "role/example-role-0",
    "us-east-1",
)
NO_ACCESS = (None, None, None, None, None)

ROLE_ARN = "arn:aws:iam::000000000001:role/example-role"
BEFORE_PREVIOUS_ACCESS = datetime(2018, 5, 1, tzinfo=timezone.utc)
AT_PREVIOUS_ACCESS = datetime(2018, 6, 1, tzinfo=timezone.utc)
AFTER_PREVIOUS_ACCESS = datetime(2019, 1, 2, tzinfo=timezone.utc)


class FakeIAMClient:
    """
    Answers each principal's GetServiceLastAccessedDetails polls from a script, in
    order. A job's ID is its principal's ARN so a poll can find that script.
    """

    exceptions = IAM_EXCEPTIONS

    def __init__(self, polls_by_arn, generate_errors_by_arn=None):
        self._polls = {arn: iter(polls) for arn, polls in polls_by_arn.items()}
        self._generate_errors = generate_errors_by_arn or {}
        self.submitted_job_arns = []

    def generate_service_last_accessed_details(self, Arn):
        if Arn in self._generate_errors:
            raise self._generate_errors[Arn]
        self.submitted_job_arns.append(Arn)
        return {"JobId": Arn}

    def get_service_last_accessed_details(self, JobId, MaxItems=None, Marker=None):
        poll = next(self._polls[JobId])
        if isinstance(poll, Exception):
            raise poll
        return copy.deepcopy(poll)


class JobsRunWhileSubmittingIAMClient(FakeIAMClient):
    """
    Reports every job IN_PROGRESS until all principals' jobs are submitted, so a sync
    sees a job complete only if it keeps submitting while earlier jobs run.
    """

    def get_service_last_accessed_details(self, JobId, MaxItems=None, Marker=None):
        if len(self.submitted_job_arns) < len(self._polls):
            return IN_PROGRESS_JOB
        return super().get_service_last_accessed_details(JobId, MaxItems, Marker)


def _create_principals(neo4j_session, arns, label="AWSUser"):
    neo4j_session.run(
        "MERGE (a:AWSAccount{id: $account_id}) "
        "WITH a "
        "OPTIONAL MATCH (a)-[:RESOURCE]->(old:AWSPrincipal) "
        "DETACH DELETE old",
        account_id=SERVICE_ACCESS_ACCOUNT_ID,
    )
    neo4j_session.run(
        "UNWIND $arns AS arn "
        "MATCH (a:AWSAccount{id: $account_id}) "
        f"MERGE (u:{label}:AWSPrincipal{{id: arn}}) "
        "SET u.arn = arn "
        "MERGE (a)-[:RESOURCE]->(u)",
        arns=arns,
        account_id=SERVICE_ACCESS_ACCOUNT_ID,
    )


def _set_access_synced_this_run(neo4j_session, arns, access):
    """
    Gives each principal the access an earlier sync recorded, stamped with this
    run's update tag as the user, group and role syncs stamp it before this step.
    """
    name, namespace, authenticated, entity, region = access
    neo4j_session.run(
        "UNWIND $arns AS arn "
        "MATCH (:AWSAccount{id: $account_id})-[r:RESOURCE]->(p:AWSPrincipal{arn: arn}) "
        "SET r.lastupdated = $update_tag, p.lastupdated = $update_tag, "
        "p.last_accessed_service_name = $name, "
        "p.last_accessed_service_namespace = $namespace, "
        "p.last_authenticated = $authenticated, "
        "p.last_authenticated_entity = $entity, "
        "p.last_authenticated_region = $region",
        arns=arns,
        account_id=SERVICE_ACCESS_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
        name=name,
        namespace=namespace,
        authenticated=authenticated,
        entity=entity,
        region=region,
    )


def _sync_service_last_accessed_details(neo4j_session, iam_client, role_last_used=None):
    cartography.intel.aws.iam.sync_service_last_accessed_details(
        neo4j_session,
        MagicMock(**{"client.return_value": iam_client}),
        SERVICE_ACCESS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": SERVICE_ACCESS_ACCOUNT_ID},
        role_last_used,
    )


def _last_accessed_services(neo4j_session):
    records = neo4j_session.run(
        "MATCH (:AWSAccount{id: $account_id})-[:RESOURCE]->(p:AWSPrincipal) "
        "RETURN p.arn AS arn, [p.last_accessed_service_name, "
        "p.last_accessed_service_namespace, p.last_authenticated, "
        "p.last_authenticated_entity, p.last_authenticated_region] AS access",
        account_id=SERVICE_ACCESS_ACCOUNT_ID,
    )
    return {record["arn"]: tuple(record["access"]) for record in records}


@mock.patch("time.sleep")
def test_sync_service_last_accessed_details_loads_most_recent_service_per_principal(
    mock_sleep, neo4j_session
):
    _create_principals(neo4j_session, [USER_A_ARN, USER_B_ARN])
    iam_client = FakeIAMClient(
        {
            USER_A_ARN: [COMPLETED_JOB],
            USER_B_ARN: [
                IN_PROGRESS_JOB,
                FIRST_PAGE_OF_COMPLETED_JOB,
                LAST_PAGE_OF_COMPLETED_JOB,
            ],
        }
    )

    _sync_service_last_accessed_details(neo4j_session, iam_client)

    assert _last_accessed_services(neo4j_session) == {
        USER_A_ARN: EC2_ACCESS,
        USER_B_ARN: EC2_ACCESS,
    }


@pytest.mark.parametrize(
    "user_b_polls, generate_errors_by_arn",
    [
        pytest.param([], {USER_B_ARN: PRINCIPAL_NOT_FOUND}, id="principal-deleted"),
        pytest.param(
            [], {USER_B_ARN: GENERATE_ACCESS_DENIED}, id="report-generation-denied"
        ),
        pytest.param([POLL_ACCESS_DENIED], {}, id="report-read-denied"),
        pytest.param([FAILED_JOB], {}, id="job-failed"),
        pytest.param(itertools.repeat(IN_PROGRESS_JOB), {}, id="job-timed-out"),
    ],
)
@mock.patch("time.sleep")
def test_sync_service_last_accessed_details_skips_principal_without_report(
    mock_sleep, neo4j_session, user_b_polls, generate_errors_by_arn
):
    _create_principals(neo4j_session, [USER_A_ARN, USER_B_ARN])
    iam_client = FakeIAMClient(
        {USER_A_ARN: [COMPLETED_JOB], USER_B_ARN: user_b_polls}, generate_errors_by_arn
    )

    _sync_service_last_accessed_details(neo4j_session, iam_client)

    assert _last_accessed_services(neo4j_session) == {
        USER_A_ARN: EC2_ACCESS,
        USER_B_ARN: NO_ACCESS,
    }


def test_sync_service_last_accessed_details_fails_on_invalid_credentials(
    neo4j_session,
):
    _create_principals(neo4j_session, [USER_A_ARN])
    iam_client = FakeIAMClient({USER_A_ARN: []}, {USER_A_ARN: INVALID_CREDENTIALS})

    with pytest.raises(ClientError):
        _sync_service_last_accessed_details(neo4j_session, iam_client)


@pytest.mark.parametrize(
    "user_b_polls, generate_errors_by_arn",
    [
        pytest.param([], {USER_B_ARN: GENERATE_THROTTLED}, id="generation-throttled"),
        pytest.param([THROTTLED_POLL], {}, id="report-read-throttled"),
        pytest.param([], {USER_B_ARN: IAM_UNREACHABLE}, id="iam-unreachable"),
    ],
)
@mock.patch.object(
    cartography.intel.aws.iam,
    "_call_iam_with_throttle_retry",
    cartography.intel.aws.iam._call_iam_with_throttle_retry.__wrapped__,
)
@mock.patch.object(cartography.intel.aws.iam, "_SERVICE_LAST_ACCESSED_BATCH_SIZE", 1)
def test_sync_service_last_accessed_details_stops_when_iam_stays_unavailable(
    neo4j_session, user_b_polls, generate_errors_by_arn
):
    principals = [USER_A_ARN, USER_B_ARN, USER_C_ARN]
    _create_principals(neo4j_session, principals)
    _set_access_synced_this_run(neo4j_session, principals, PREVIOUS_ACCESS)
    iam_client = FakeIAMClient(
        {
            USER_A_ARN: [COMPLETED_JOB],
            USER_B_ARN: user_b_polls,
            USER_C_ARN: [COMPLETED_JOB],
        },
        generate_errors_by_arn,
    )

    _sync_service_last_accessed_details(neo4j_session, iam_client)

    assert _last_accessed_services(neo4j_session) == {
        USER_A_ARN: EC2_ACCESS,
        USER_B_ARN: PREVIOUS_ACCESS,
        USER_C_ARN: PREVIOUS_ACCESS,
    }


@pytest.mark.parametrize(
    "stored_access, role_last_used, expected_access",
    [
        pytest.param(NO_ACCESS, {ROLE_ARN: None}, NO_ACCESS, id="never-used"),
        pytest.param(
            PREVIOUS_ACCESS,
            {ROLE_ARN: BEFORE_PREVIOUS_ACCESS},
            PREVIOUS_ACCESS,
            id="unused-since-stored-access",
        ),
        pytest.param(
            PREVIOUS_ACCESS,
            {ROLE_ARN: AT_PREVIOUS_ACCESS},
            PREVIOUS_ACCESS,
            id="last-use-is-stored-access",
        ),
        pytest.param(
            PREVIOUS_ACCESS,
            {ROLE_ARN: AFTER_PREVIOUS_ACCESS},
            EC2_ACCESS,
            id="used-since-stored-access",
        ),
        pytest.param(
            NO_ACCESS,
            {ROLE_ARN: AFTER_PREVIOUS_ACCESS},
            EC2_ACCESS,
            id="used-with-nothing-stored",
        ),
        pytest.param(PREVIOUS_ACCESS, {}, EC2_ACCESS, id="not-a-known-role"),
        pytest.param(PREVIOUS_ACCESS, None, EC2_ACCESS, id="no-role-last-used"),
    ],
)
def test_sync_service_last_accessed_details_skips_roles_unused_since_stored_access(
    neo4j_session, stored_access, role_last_used, expected_access
):
    _create_principals(neo4j_session, [ROLE_ARN], label="AWSRole")
    _set_access_synced_this_run(neo4j_session, [ROLE_ARN], stored_access)
    iam_client = FakeIAMClient({ROLE_ARN: [COMPLETED_JOB]})

    _sync_service_last_accessed_details(neo4j_session, iam_client, role_last_used)

    assert _last_accessed_services(neo4j_session) == {ROLE_ARN: expected_access}


@mock.patch("time.sleep")
def test_sync_service_last_accessed_details_keeps_job_after_throttled_poll(
    mock_sleep, neo4j_session
):
    _create_principals(neo4j_session, [USER_A_ARN])
    iam_client = FakeIAMClient({USER_A_ARN: [THROTTLED_POLL, COMPLETED_JOB]})

    _sync_service_last_accessed_details(neo4j_session, iam_client)

    assert _last_accessed_services(neo4j_session) == {USER_A_ARN: EC2_ACCESS}
    assert iam_client.submitted_job_arns == [USER_A_ARN]


@mock.patch("time.sleep")
def test_sync_service_last_accessed_details_runs_report_jobs_concurrently(
    mock_sleep, neo4j_session
):
    _create_principals(neo4j_session, [USER_A_ARN, USER_B_ARN, USER_C_ARN])
    iam_client = JobsRunWhileSubmittingIAMClient(
        {
            USER_A_ARN: [COMPLETED_JOB],
            USER_B_ARN: [COMPLETED_JOB],
            USER_C_ARN: [COMPLETED_JOB],
        }
    )

    _sync_service_last_accessed_details(neo4j_session, iam_client)

    assert _last_accessed_services(neo4j_session) == {
        USER_A_ARN: EC2_ACCESS,
        USER_B_ARN: EC2_ACCESS,
        USER_C_ARN: EC2_ACCESS,
    }


def _get_principal_role_nodes(neo4j_session):
    """
    Get AWSPrincipal node tuples (rolearn, arn) that have arns with substring `:role/`
    """
    return {
        (roleid, arn)
        for (roleid, arn) in check_nodes(
            neo4j_session,
            "AWSPrincipal",
            ["roleid", "arn"],
        )
        if ":role/"
        in arn  # filter out other Principals nodes, like the ec2 service princiapl
    }


def test_load_roles_creates_trust_relationships(neo4j_session):
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert: Get TRUSTS_AWS_PRINCIPAL relationships from Neo4j using check_rels.
    expected = {
        (
            "arn:aws:iam::000000000000:role/example-role-0",
            "arn:aws:iam::000000000000:root",
        ),
        (
            "arn:aws:iam::000000000000:role/example-role-1",
            "arn:aws:iam::000000000000:role/example-role-0",
        ),
        ("arn:aws:iam::000000000000:role/example-role-2", "ec2.amazonaws.com"),
        (
            "arn:aws:iam::000000000000:role/example-role-3",
            "arn:aws:iam::000000000000:saml-provider/ADFS",
        ),
    }

    actual = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSPrincipal",
        "arn",
        "TRUSTS_AWS_PRINCIPAL",
    )

    assert actual == expected


def _trust_edge_properties(neo4j_session, role_arn: str) -> dict:
    result = neo4j_session.run(
        """
        MATCH (r:AWSRole{arn: $role_arn})-[t:TRUSTS_AWS_PRINCIPAL]->(p:AWSPrincipal)
        RETURN p.arn AS principal_arn,
               t.has_condition AS has_condition,
               t.condition_keys AS condition_keys,
               t.conditions AS conditions,
               t.has_external_id AS has_external_id
        """,
        role_arn=role_arn,
    )
    return {record["principal_arn"]: dict(record) for record in result}


def test_trust_conditions_are_loaded_onto_the_edge(neo4j_session):
    """Two roles differing only in sub scoping must not produce identical trust edges."""
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    provider_arn = tests.data.aws.iam.GITHUB_OIDC_PROVIDER_ARN

    pinned = _trust_edge_properties(
        neo4j_session, "arn:aws:iam::000000000000:role/gha-pinned"
    )[provider_arn]
    org_wide = _trust_edge_properties(
        neo4j_session, "arn:aws:iam::000000000000:role/gha-org-wide"
    )[provider_arn]

    assert pinned["has_condition"] is True
    assert org_wide["has_condition"] is True
    assert (
        pinned["condition_keys"]
        == org_wide["condition_keys"]
        == [
            "token.actions.githubusercontent.com:aud",
            "token.actions.githubusercontent.com:sub",
        ]
    )
    assert "repo:octo-org/octo-repo:ref:refs/heads/main" in pinned["conditions"]
    assert "repo:octo-org/*" in org_wide["conditions"]
    assert pinned["conditions"] != org_wide["conditions"]


def test_unconditional_trust_edge_is_not_flagged(neo4j_session):
    """An unconditional Allow anywhere in the trust policy wins for that principal."""
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    mixed = _trust_edge_properties(
        neo4j_session, "arn:aws:iam::000000000000:role/gha-mixed"
    )[tests.data.aws.iam.GITHUB_OIDC_PROVIDER_ARN]

    assert mixed["has_condition"] is False
    assert mixed["condition_keys"] == []
    assert mixed["conditions"] is None
    assert mixed["has_external_id"] is False


def test_external_id_requirement_is_loaded_onto_the_edge(neo4j_session):
    """A third-party trust records whether the caller must pass an external ID."""
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES_EXTERNAL_ID,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    vendor_arn = tests.data.aws.iam.THIRD_PARTY_ROOT_ARN

    required = _trust_edge_properties(
        neo4j_session, "arn:aws:iam::000000000000:role/vendor-external-id"
    )[vendor_arn]
    optional = _trust_edge_properties(
        neo4j_session, "arn:aws:iam::000000000000:role/vendor-optional-external-id"
    )[vendor_arn]

    assert required["has_external_id"] is True
    assert required["condition_keys"] == ["sts:ExternalId"]
    assert optional["has_external_id"] is False
    assert optional["condition_keys"] == ["sts:ExternalId"]


def test_stale_trust_edges_are_cleaned_up(neo4j_session):
    """A trust removed from the policy must not survive the next sync."""
    _create_base_account(neo4j_session)
    role_arns = [
        role["Arn"] for role in tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC["Roles"]
    ]
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    for role_arn in role_arns:
        assert set(_trust_edge_properties(neo4j_session, role_arn)) == {
            tests.data.aws.iam.GITHUB_OIDC_PROVIDER_ARN
        }

    # Re-sync at a later tag with the trust policy emptied out.
    untrusting = {
        "Roles": [
            {
                **role,
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [],
                },
            }
            for role in tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC["Roles"]
        ],
    }
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        untrusting,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
    )
    cartography.intel.aws.iam.cleanup_iam(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    for role_arn in role_arns:
        assert _trust_edge_properties(neo4j_session, role_arn) == {}


def test_legacy_trust_edges_are_cleaned_up(neo4j_session):
    """A stale trust edge written before the edge became a MatchLink must still go away.

    Edges from that era carry no _sub_resource_label / _sub_resource_id, which is what the
    MatchLink cleanup selects on, so they need the dedicated migration step.
    """
    _create_base_account(neo4j_session)
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Turn every trust edge in the account into a pre-migration one.
    neo4j_session.run(
        """
        MATCH (:AWSAccount{id: $AccountId})-[:RESOURCE]->(:AWSRole)-[t:TRUSTS_AWS_PRINCIPAL]->()
        REMOVE t._sub_resource_label, t._sub_resource_id
        """,
        AccountId=TEST_ACCOUNT_ID,
    )

    # example-role-0 stops trusting root; every other trust is unchanged.
    roles = [
        (
            {
                **role,
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [],
                },
            }
            if role["RoleName"] == "example-role-0"
            else role
        )
        for role in tests.data.aws.iam.LIST_ROLES["Roles"]
    ]
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        {"Roles": roles},
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
    )
    cartography.intel.aws.iam.cleanup_iam(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    actual = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSPrincipal",
        "arn",
        "TRUSTS_AWS_PRINCIPAL",
    )
    # Only the three trusts still declared remain after the legacy migration.
    assert actual == {
        (
            "arn:aws:iam::000000000000:role/example-role-1",
            "arn:aws:iam::000000000000:role/example-role-0",
        ),
        ("arn:aws:iam::000000000000:role/example-role-2", "ec2.amazonaws.com"),
        (
            "arn:aws:iam::000000000000:role/example-role-3",
            "arn:aws:iam::000000000000:saml-provider/ADFS",
        ),
    }
    counts = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: $AccountId})-[:RESOURCE]->(:AWSRole)-[t:TRUSTS_AWS_PRINCIPAL]->()
        RETURN count(t) AS total, count(t._sub_resource_id) AS scoped
        """,
        AccountId=TEST_ACCOUNT_ID,
    ).single()
    assert counts["total"] == counts["scoped"] == 3


def test_sync_saml_providers(neo4j_session):
    _create_base_account(neo4j_session)

    cartography.intel.aws.iam.load_saml_providers(
        neo4j_session,
        tests.data.aws.iam.LIST_SAML_PROVIDERS["SAMLProviderList"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    nodes = check_nodes(neo4j_session, "AWSSAMLProvider", ["arn"])
    expected = {
        ("arn:aws:iam::000000000000:saml-provider/ADFS",),
        ("arn:aws:iam::000000000000:saml-provider/Okta",),
    }
    assert nodes == expected


def test_load_inline_policy(neo4j_session):
    # Earlier cleanup tests remove the groups, so reload the policy principal.
    group_data = cartography.intel.aws.iam.transform_groups(
        tests.data.aws.iam.LIST_GROUPS["Groups"], {}
    )
    cartography.intel.aws.iam.load_groups(
        neo4j_session, group_data, TEST_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    # Just load in a single policy.
    inline_policy_data = [
        {
            "id": "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
            "arn": None,  # Inline policies don't have arns
            "name": "group_inline_policy",
            "type": "inline",
            "principal_arns": ["arn:aws:iam::000000000000:group/example-group-0"],
        }
    ]
    load(
        neo4j_session,
        AWSInlinePolicySchema(),
        inline_policy_data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )


def test_load_inline_policy_data(neo4j_session):
    transformed_stmts = _transform_policy_statements(
        tests.data.aws.iam.INLINE_POLICY_STATEMENTS,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
    )
    cartography.intel.aws.iam.load_policy_statements(
        neo4j_session,
        transformed_stmts,
        TEST_UPDATE_TAG,
    )


def test_map_permissions(neo4j_session):
    # Insert an s3 bucket to map
    neo4j_session.run(
        """
    MERGE (s3:AWSS3Bucket{arn:'arn:aws:s3:::test_bucket'})<-[:RESOURCE]-(a:AWSAccount{id:$AccountId})
    """,
        AccountId=TEST_ACCOUNT_ID,
    )
    cartography.intel.aws.permission_relationships.sync(
        neo4j_session,
        mock.MagicMock,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "permission_relationships_file": "cartography/data/permission_relationships.yaml",
        },
    )
    results = neo4j_session.run(
        "MATCH ()-[r:CAN_READ]->() RETURN count(r) as rel_count",
    )
    assert results
    for result in results:
        assert result["rel_count"] == 1
