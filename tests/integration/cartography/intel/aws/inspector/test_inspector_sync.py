import asyncio
import operator
import threading
import time
from types import SimpleNamespace

import botocore.exceptions
import pytest

from cartography.intel.aws import inspector
from cartography.intel.aws.inspector import sync
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456
TEST_REGION = "us-west-2"
TEST_ACC_ID_1 = "123456789011"
TEST_ACC_ID_2 = "123456789012"

NETWORK_FINDING_ARN = (
    "arn:aws:inspector2:us-west-2:123456789011:finding/0123456789abcdef0123456789abc123"
)
KERNEL_FINDING_ARN = (
    "arn:aws:inspector2:us-west-2:123456789012:finding/7123456789abcdef0123456789abc456"
)
OPENSSL_FINDING_ARN = (
    "arn:aws:inspector2:us-west-2:123456789011:finding/f123456789abcdef0123456789abc789"
)

THROTTLED = botocore.exceptions.ClientError(
    error_response={"Error": {"Code": "ThrottlingException", "Message": ""}},
    operation_name="ListFindings",
)
SIGNATURE_EXPIRED = botocore.exceptions.ClientError(
    error_response={
        "Error": {
            "Code": "InvalidSignatureException",
            "Message": "Signature expired: 20260101T000000Z is now earlier than "
            "20260101T000500Z (20260101T001000Z - 5 min.)",
        },
    },
    operation_name="ListFindings",
)

_COMPARISONS = {
    "EQUALS": operator.eq,
    "NOT_EQUALS": operator.ne,
    "PREFIX": str.startswith,
}
_FINDING_FIELDS = {
    "awsAccountId": "awsAccountId",
    "findingArn": "findingArn",
    "findingStatus": "status",
}


class FakeInspector2Client:
    """
    An in-memory inspector2 regional endpoint. ListFindings applies the filter
    criteria it receives, returns one finding per page and records the ARN of each
    finding it serves, signalling once it has served every finding. Either
    operation can be made to fail, ListFindings can fail differently per finding
    ID prefix, and it can fail the first request for each page with a given error.
    """

    def __init__(
        self,
        findings=(),
        member_account_ids=(),
        list_findings_error=None,
        list_findings_errors_by_prefix=None,
        list_members_error=None,
        fail_each_page_once=None,
    ):
        self.meta = SimpleNamespace(partition="aws", region_name=TEST_REGION)
        self._findings = findings
        self._member_account_ids = member_account_ids
        self._list_findings_error = list_findings_error
        self._list_findings_errors_by_prefix = list_findings_errors_by_prefix or {}
        self._list_members_error = list_members_error
        self._fail_each_page_once = fail_each_page_once
        self._failed_pages = set()
        self.served_finding_arns = []
        self.all_findings_served = threading.Event()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    def get_paginator(self, operation_name):
        assert operation_name == "list_members"
        return SimpleNamespace(paginate=self._list_members_pages)

    async def _list_members_pages(self):
        if self._list_members_error:
            raise self._list_members_error
        yield {
            "members": [
                {"accountId": account_id} for account_id in self._member_account_ids
            ],
        }

    async def list_findings(self, filterCriteria, nextToken="0"):
        # Lets every concurrent request start before any fails, as they do against
        # a real endpoint.
        await asyncio.sleep(0)
        if self._list_findings_error:
            raise self._list_findings_error
        finding_id_prefix = filterCriteria["findingArn"][0]["value"][-1]
        if finding_id_prefix in self._list_findings_errors_by_prefix:
            raise self._list_findings_errors_by_prefix[finding_id_prefix]
        page_key = (finding_id_prefix, nextToken)
        if self._fail_each_page_once and page_key not in self._failed_pages:
            self._failed_pages.add(page_key)
            raise self._fail_each_page_once
        matching = [
            finding
            for finding in self._findings
            if all(
                _COMPARISONS[f["comparison"]](finding[_FINDING_FIELDS[key]], f["value"])
                for key, filters in filterCriteria.items()
                for f in filters
            )
        ]
        index = int(nextToken)
        page = {"findings": matching[index : index + 1]}
        self.served_finding_arns.extend(f["findingArn"] for f in page["findings"])
        if len(self.served_finding_arns) == len(self._findings):
            self.all_findings_served.set()
        if index + 1 < len(matching):
            page["nextToken"] = str(index + 1)
        return page


class FakeAioboto3Session:
    def __init__(self, inspector2_client):
        self._inspector2_client = inspector2_client

    def client(self, service_name, **kwargs):
        assert service_name == "inspector2"
        return self._inspector2_client


def _add_stale_finding(neo4j_session, finding_arn):
    neo4j_session.run(
        """
        MERGE (a:AWSAccount{id: $acc})
        MERGE (f:AWSInspectorFinding{id: $arn})
        SET f.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(f)
        SET r.lastupdated = $old_tag
        """,
        acc=TEST_ACC_ID_1,
        arn=finding_arn,
        old_tag=TEST_UPDATE_TAG - 1,
    )


def test_sync_inspector_network_findings(neo4j_session):
    # Arrange
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(findings=LIST_FINDINGS_NETWORK),
    )
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:AWSEC2Instance{id: 'i-instanceid', instanceid: 'i-instanceid'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert Finding to AWSEC2Instance exists
    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "AWSEC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (NETWORK_FINDING_ARN, "i-instanceid"),
    }

    # Assert AWSAccount to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789011", NETWORK_FINDING_ARN),
    }

    # Network-reachability findings are labeled as configuration security issues,
    # not CVEs.
    labels = neo4j_session.run(
        "MATCH (f:AWSInspectorFinding {id: $arn}) RETURN labels(f) AS labels",
        arn=NETWORK_FINDING_ARN,
    ).single()["labels"]
    assert "SecurityIssue" in labels
    assert "CVE" not in labels


def test_sync_inspector_ec2_package_findings(neo4j_session):
    # Arrange: account 123456789011 delegates its findings to 123456789012, the
    # account being synced.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            findings=LIST_FINDINGS_EC2_PACKAGE,
            member_account_ids=[TEST_ACC_ID_1],
        ),
    )
    # Remove everything previously put in the test graph since the fixture scope is set to module and not function.
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n;
        """,
    )
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:AWSEC2Instance{id: 'i-88503981029833100', instanceid: 'i-88503981029833100'})
        MERGE (:AWSEC2Instance{id: 'i-88503981029833101', instanceid: 'i-88503981029833101'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_2,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_2},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "AWSEC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (KERNEL_FINDING_ARN, "i-88503981029833100"),
        (OPENSSL_FINDING_ARN, "i-88503981029833101"),
    }

    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "AWSInspectorPackage",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (KERNEL_FINDING_ARN, "kernel-tools|0:4.9.17-6.29.amzn1.X86_64"),
        (KERNEL_FINDING_ARN, "kernel|0:4.9.17-6.29.amzn1.X86_64"),
        (OPENSSL_FINDING_ARN, "openssl|0:1.0.2k-1.amzn2.X86_64"),
    }

    # Assert AWSAccount RESOURCE to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789012", KERNEL_FINDING_ARN),
        ("123456789012", OPENSSL_FINDING_ARN),
    }

    # Assert AWSAccount MEMBER to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "MEMBER",
        rel_direction_right=True,
    ) == {
        ("123456789011", OPENSSL_FINDING_ARN),
        ("123456789012", KERNEL_FINDING_ARN),
    }

    # Assert AWSAccount RESOURCE to Package exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorPackage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789012", "kernel-tools|0:4.9.17-6.29.amzn1.X86_64"),
        ("123456789012", "kernel|0:4.9.17-6.29.amzn1.X86_64"),
        ("123456789012", "openssl|0:1.0.2k-1.amzn2.X86_64"),
    }

    # Package-vulnerability findings are CVE-backed and labeled as such.
    labels = neo4j_session.run(
        "MATCH (f:AWSInspectorFinding {id: $arn}) RETURN labels(f) AS labels",
        arn=KERNEL_FINDING_ARN,
    ).single()["labels"]
    assert "CVE" in labels
    assert "SecurityIssue" not in labels

    # Package-vulnerability findings expose the CVE id via the normalized cve_id
    # property so they participate in the :CVE ontology and CVEMetadata enrichment.
    assert check_nodes(
        neo4j_session,
        "AWSInspectorFinding",
        ["id", "cve_id"],
    ) == {
        (KERNEL_FINDING_ARN, "CVE-2017-9059"),
        (OPENSSL_FINDING_ARN, "CVE-2023-1234"),
    }

    # Inspector's adjusted CVSS vector (inspectorScoreDetails.adjustedCvss.scoringVector)
    # is stored as a single scalar property.
    assert check_nodes(
        neo4j_session,
        "AWSInspectorFinding",
        ["id", "cvssvector"],
    ) == {
        (KERNEL_FINDING_ARN, "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H"),
        (OPENSSL_FINDING_ARN, "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    }

    # packageVulnerabilityDetails.cvss[].scoringVector (vendor/NVD entries) are
    # stored as a list property.
    vendorcvssvectors_by_id = {
        row["id"]: row["vendorcvssvectors"]
        for row in neo4j_session.run(
            "MATCH (f:AWSInspectorFinding) RETURN f.id AS id, f.vendorcvssvectors AS vendorcvssvectors",
        )
    }
    assert vendorcvssvectors_by_id == {
        KERNEL_FINDING_ARN: [
            "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
            "AV:L/AC:L/Au:N/C:N/I:N/A:C",
            "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
        ],
        OPENSSL_FINDING_ARN: ["CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"],
    }

    # packageVulnerabilityDetails.cvss[].baseScore (vendor/NVD entries) are
    # stored as a parallel list property.
    vendorcvssscores_by_id = {
        row["id"]: row["vendorcvssscores"]
        for row in neo4j_session.run(
            "MATCH (f:AWSInspectorFinding) RETURN f.id AS id, f.vendorcvssscores AS vendorcvssscores",
        )
    }
    assert vendorcvssscores_by_id == {
        KERNEL_FINDING_ARN: [5.5, 4.9, 5.5],
        OPENSSL_FINDING_ARN: [7.5],
    }


def test_sync_inspector_loads_findings_from_every_finding_id_prefix(neo4j_session):
    # Arrange: one finding for each hex digit a finding ID can start with, more
    # findings than one load batch holds.
    finding_arns = {
        f"arn:aws:inspector2:us-west-2:123456789011:finding/{digit}{'0' * 31}"
        for digit in "0123456789abcdef"
    }
    findings = [{**LIST_FINDINGS_NETWORK[0], "findingArn": arn} for arn in finding_arns]
    inspector2 = FakeInspector2Client(findings=findings)
    aioboto3_session = FakeAioboto3Session(inspector2)
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACC_ID_1,
            "experimental_aws_inspector_batch": 5,
        },
    )

    # Assert: every finding was loaded, and fetched exactly once.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        (arn,) for arn in finding_arns
    }
    assert sorted(inspector2.served_finding_arns) == sorted(finding_arns)


@pytest.mark.parametrize("page_error", [THROTTLED, SIGNATURE_EXPIRED])
def test_sync_inspector_resumes_failed_pages(neo4j_session, page_error):
    # Arrange: three findings share a finding ID prefix, so their shard spans
    # three pages, and the endpoint fails the first request for every page. A
    # finding from a previous run is still in the graph.
    finding_arns = [
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000001",
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000002",
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000003",
    ]
    findings = [{**LIST_FINDINGS_NETWORK[0], "findingArn": arn} for arn in finding_arns]
    inspector2 = FakeInspector2Client(findings=findings, fail_each_page_once=page_error)
    aioboto3_session = FakeAioboto3Session(inspector2)
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _add_stale_finding(neo4j_session, "arn:aws:stale")

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: each retry resumed from the failed page, so every finding was
    # fetched exactly once, and the sync completed, so cleanup removed the finding
    # the previous run left behind.
    assert inspector2.served_finding_arns == finding_arns
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        (finding_arns[0],),
        (finding_arns[1],),
        (finding_arns[2],),
    }


def test_sync_inspector_fetches_pages_while_a_batch_loads(neo4j_session, monkeypatch):
    # Arrange: one shard spans three pages and findings load one per batch. The
    # first load holds the Neo4j write until the endpoint has served every page,
    # giving up after five seconds.
    finding_arns = [
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000001",
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000002",
        "arn:aws:inspector2:us-west-2:123456789011:finding/a0000000000000000000000000000003",
    ]
    findings = [{**LIST_FINDINGS_NETWORK[0], "findingArn": arn} for arn in finding_arns]
    inspector2 = FakeInspector2Client(findings=findings)
    served_during_first_load = []
    load_findings = inspector.load_inspector_findings

    def slow_first_load(*args, **kwargs):
        if not served_during_first_load:
            inspector2.all_findings_served.wait(timeout=5)
            served_during_first_load.extend(inspector2.served_finding_arns)
        load_findings(*args, **kwargs)

    monkeypatch.setattr(inspector, "load_inspector_findings", slow_first_load)
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    sync(
        neo4j_session,
        FakeAioboto3Session(inspector2),
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACC_ID_1,
            "experimental_aws_inspector_batch": 1,
        },
    )

    # Assert: the shard fetched its remaining pages while the first batch was still
    # loading, and every finding was loaded.
    assert served_during_first_load == finding_arns
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        (finding_arns[0],),
        (finding_arns[1],),
        (finding_arns[2],),
    }


def test_sync_inspector_cleans_up_when_inspector_is_not_enabled(neo4j_session):
    # Arrange: a finding from a previous run, and a region where Inspector now
    # rejects the request because it is not enabled.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            list_findings_error=botocore.exceptions.ClientError(
                error_response={
                    "Error": {"Code": "ValidationException", "Message": ""},
                },
                operation_name="ListFindings",
            ),
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _add_stale_finding(neo4j_session, "arn:aws:stale")

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the region counts as having no findings, so cleanup removed the
    # finding the previous run left behind.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == set()


def test_sync_inspector_survives_connection_timeout(neo4j_session):
    # Arrange: a finding from a previous (successful) run already lives in the
    # graph, stamped with an older update tag.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            list_findings_error=botocore.exceptions.ConnectTimeoutError(
                endpoint_url="https://inspector2.me-south-1.amazonaws.com/findings/list",
            ),
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _add_stale_finding(neo4j_session, "arn:aws:stale")

    # Act: a fresh sync hits a transient connection failure for the region.
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the account sync completed without raising, and cleanup was skipped
    # so the last-known-good finding from the previous run was preserved.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        ("arn:aws:stale",),
    }


def test_sync_inspector_preserves_data_on_member_listing_timeout(neo4j_session):
    # A transient connection failure while listing members must NOT be swallowed
    # into an empty member list (which would let cleanup run and delete stale
    # member findings).
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            list_members_error=botocore.exceptions.ConnectTimeoutError(
                endpoint_url="https://inspector2.me-south-1.amazonaws.com/members/list",
            ),
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    # A delegated-member finding from a previous successful run, stamped older.
    _add_stale_finding(neo4j_session, "arn:aws:stale-member")

    # Act: list_members connect-times-out for the region.
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the region was skipped, cleanup was skipped, and the stale member
    # finding was preserved rather than deleted.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        ("arn:aws:stale-member",),
    }


INSPECTOR_NOT_ENABLED = botocore.exceptions.ClientError(
    error_response={"Error": {"Code": "ValidationException", "Message": ""}},
    operation_name="ListFindings",
)


def test_sync_inspector_preserves_data_when_one_shard_times_out(neo4j_session):
    # Arrange: one shard is rejected as "not enabled" while another times out.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            list_findings_errors_by_prefix={
                "0": INSPECTOR_NOT_ENABLED,
                "1": botocore.exceptions.ConnectTimeoutError(
                    endpoint_url="https://inspector2.us-west-2.amazonaws.com/findings/list",
                ),
            },
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _add_stale_finding(neo4j_session, "arn:aws:stale")

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the timeout, not the rejection, decides the outcome, so cleanup was
    # skipped and the finding from the previous run was preserved.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        ("arn:aws:stale",),
    }


def test_sync_inspector_raises_when_one_shard_fails_unexpectedly(neo4j_session):
    # Arrange: one shard is rejected as "not enabled" while another hits an
    # unexpected server error.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            list_findings_errors_by_prefix={
                "0": INSPECTOR_NOT_ENABLED,
                "1": botocore.exceptions.ClientError(
                    error_response={
                        "Error": {"Code": "InternalServerException", "Message": ""},
                    },
                    operation_name="ListFindings",
                ),
            },
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act and assert
    with pytest.raises(
        botocore.exceptions.ClientError, match="InternalServerException"
    ):
        sync(
            neo4j_session,
            aioboto3_session,
            [TEST_REGION],
            TEST_ACC_ID_1,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
        )


def test_sync_inspector_raises_a_load_that_fails_while_a_shard_is_rejected(
    neo4j_session, monkeypatch
):
    # Arrange: one shard serves a finding whose load fails. Another shard is
    # rejected as "not enabled" while that load is still running.
    finding_arn = (
        "arn:aws:inspector2:us-west-2:123456789011:finding/"
        "a0000000000000000000000000000001"
    )
    inspector2 = FakeInspector2Client(
        findings=[{**LIST_FINDINGS_NETWORK[0], "findingArn": finding_arn}],
    )
    load_started = threading.Event()
    shard_rejected = threading.Event()

    def load_that_fails(*args, **kwargs):
        load_started.set()
        shard_rejected.wait(timeout=5)
        # Lets the task group cancel the wait for this load before it fails.
        time.sleep(0.2)
        raise RuntimeError("Neo4j write failed")

    monkeypatch.setattr(inspector, "load_inspector_findings", load_that_fails)
    list_findings = inspector2.list_findings

    async def reject_shard_b_during_load(filterCriteria, nextToken="0"):
        if filterCriteria["findingArn"][0]["value"][-1] == "b":
            while not load_started.is_set():
                await asyncio.sleep(0.01)
            shard_rejected.set()
            raise INSPECTOR_NOT_ENABLED
        return await list_findings(filterCriteria, nextToken)

    inspector2.list_findings = reject_shard_b_during_load
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act and assert: the failed write stops the sync, so cleanup does not run.
    with pytest.raises(RuntimeError, match="Neo4j write failed"):
        sync(
            neo4j_session,
            FakeAioboto3Session(inspector2),
            [TEST_REGION],
            TEST_ACC_ID_1,
            TEST_UPDATE_TAG,
            {
                "UPDATE_TAG": TEST_UPDATE_TAG,
                "AWS_ID": TEST_ACC_ID_1,
                "experimental_aws_inspector_batch": 1,
            },
        )
