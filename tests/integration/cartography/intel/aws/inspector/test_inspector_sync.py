import asyncio
import operator
import threading
import time
from datetime import timedelta
from datetime import timezone
from types import SimpleNamespace

import botocore.exceptions
import pytest

import cartography.intel.ontology.packages
from cartography.intel.aws import inspector
from cartography.intel.aws.inspector import sync
from cartography.intel.trivy.util import make_normalized_package_id
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
INSPECTOR_NOT_ENABLED = botocore.exceptions.ClientError(
    error_response={"Error": {"Code": "ValidationException", "Message": ""}},
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
    ID prefix or page, and it can fail the first request for each page with a given
    error.
    """

    def __init__(
        self,
        findings=(),
        member_account_ids=(),
        list_findings_error=None,
        list_findings_errors_by_prefix=None,
        list_members_error=None,
        fail_each_page_once=None,
        list_findings_errors_by_page=None,
    ):
        self.meta = SimpleNamespace(partition="aws", region_name=TEST_REGION)
        self._findings = findings
        self._member_account_ids = member_account_ids
        self._list_findings_error = list_findings_error
        self._list_findings_errors_by_prefix = list_findings_errors_by_prefix or {}
        self._list_members_error = list_members_error
        self._fail_each_page_once = fail_each_page_once
        self._list_findings_errors_by_page = list_findings_errors_by_page or {}
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
        if page_key in self._list_findings_errors_by_page:
            raise self._list_findings_errors_by_page[page_key]
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


def _ec2_package_finding(template, instance_id, finding_id, **overrides):
    resource = {**template["resources"][0], "id": instance_id}
    return {
        **template,
        "awsAccountId": TEST_ACC_ID_1,
        "findingArn": f"arn:aws:inspector2:us-west-2:{TEST_ACC_ID_1}:finding/{finding_id}",
        "resources": [resource],
        **overrides,
    }


def _sync_package_findings(
    neo4j_session, findings, update_tag=TEST_UPDATE_TAG, batch_size=None, **client
):
    parameters = {"UPDATE_TAG": update_tag, "AWS_ID": TEST_ACC_ID_1}
    if batch_size:
        parameters["experimental_aws_inspector_batch"] = batch_size
    sync(
        neo4j_session,
        FakeAioboto3Session(FakeInspector2Client(findings=findings, **client)),
        [TEST_REGION],
        TEST_ACC_ID_1,
        update_tag,
        parameters,
    )


def _instance_findings(neo4j_session):
    return neo4j_session.run(
        """
        MATCH (i:AWSInspectorInstanceFindings)-[:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
        RETURN i.id AS instance, s.id AS finding_set
        ORDER BY instance
        """,
    ).data()


# One row per (instance, finding), the way the module docs read finding sets.
_FINDING_ROWS = """
    MATCH (i:AWSInspectorInstanceFindings)-[o:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
    WHERE s.id = i.finding_set_id
    MATCH (s)-[c:CONTAINS]->(f:AWSInspectorFindingContent)
    UNWIND c.slots AS k
    RETURN i.id AS instance, f.vulnerabilityid AS vulnerability,
           f.severity AS severity,
           o.finding_arn_prefix + o.finding_ids[k] AS arn,
           o.first_observed_at_ms[k] AS first_observed,
           o.last_observed_at_ms[k] AS last_observed,
           o.updated_at_ms[k] AS updated
    ORDER BY instance, arn
"""


def _epoch_ms(value):
    return round(value.replace(tzinfo=timezone.utc).timestamp() * 1000)


def test_sync_inspector_ec2_package_findings_as_finding_sets(neo4j_session):
    # Arrange: account 123456789011 delegates its findings to 123456789012, the
    # account being synced. A package finding from before EC2 findings moved to
    # finding sets is still in the graph.
    aioboto3_session = FakeAioboto3Session(
        FakeInspector2Client(
            findings=LIST_FINDINGS_EC2_PACKAGE,
            member_account_ids=[TEST_ACC_ID_1],
        ),
    )
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        MERGE (:AWSEC2Instance{id: 'i-88503981029833100', instanceid: 'i-88503981029833100'})
        MERGE (:AWSEC2Instance{id: 'i-88503981029833101', instanceid: 'i-88503981029833101'})
        """,
    )
    neo4j_session.run(
        """
        MATCH (a:AWSAccount {id: $acc})
        MERGE (a)-[r:RESOURCE]->(f:AWSInspectorFinding {id: $arn})
        SET f.lastupdated = $old_tag, r.lastupdated = $old_tag,
            f.type = 'PACKAGE_VULNERABILITY'
        """,
        acc=TEST_ACC_ID_2,
        arn=KERNEL_FINDING_ARN,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    sync(
        neo4j_session,
        aioboto3_session,
        [TEST_REGION],
        TEST_ACC_ID_2,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACC_ID_2,
        },
    )

    # Assert: package findings on EC2 instances are stored per instance and content,
    # not as AWSInspectorFinding nodes, so cleanup removed the old one.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == set()
    assert check_rels(
        neo4j_session,
        "AWSInspectorInstanceFindings",
        "id",
        "AWSEC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("i-88503981029833100", "i-88503981029833100"),
        ("i-88503981029833101", "i-88503981029833101"),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorInstanceFindings",
        "id",
        "MEMBER",
        rel_direction_right=True,
    ) == {
        ("123456789012", "i-88503981029833100"),
        ("123456789011", "i-88503981029833101"),
    }
    for label in (
        "AWSInspectorInstanceFindings",
        "AWSInspectorFindingSet",
        "AWSInspectorFindingContent",
    ):
        assert check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            label,
            "lastupdated",
            "RESOURCE",
            rel_direction_right=True,
        ) == {("123456789012", TEST_UPDATE_TAG)}

    # Each instance reaches its findings through its set, and each content links to
    # its vulnerability and packages, with the package's fix on the relationship.
    rows = neo4j_session.run(
        """
        MATCH (i:AWSInspectorInstanceFindings)-[:HAS_FINDING_SET]->(:AWSInspectorFindingSet)
              -[:CONTAINS]->(c:AWSInspectorFindingContent)
              -[:HAS_VULNERABILITY]->(v:AWSInspectorVulnerability:CVE)
        WHERE NOT c:CVE
        MATCH (c)-[h:HAS]->(p:AWSInspectorPackage)
        RETURN i.id AS instance, v.id AS vulnerability, c.cvssscore AS score,
               c.vendorseverity AS vendor_severity, p.id AS package,
               h.fixedinversion AS fixed_in
        ORDER BY instance, package
        """,
    ).data()
    assert rows == [
        {
            "instance": "i-88503981029833100",
            "vulnerability": "CVE-2017-9059",
            "score": 5.5,
            "vendor_severity": "Moderate",
            "package": "OS|amazon|kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
            "fixed_in": "0:4.9.18-6.30.amzn1.X86_64",
        },
        {
            "instance": "i-88503981029833100",
            "vulnerability": "CVE-2017-9059",
            "score": 5.5,
            "vendor_severity": "Moderate",
            "package": "OS|amazon|kernel|0:4.9.17-6.29.amzn1.X86_64",
            "fixed_in": "0:4.9.18-6.30.amzn1.X86_64",
        },
        {
            "instance": "i-88503981029833101",
            "vulnerability": "CVE-2023-1234",
            "score": 7.5,
            "vendor_severity": "High",
            "package": "OS|amazon|openssl|0:1.0.2k-1.amzn2.X86_64",
            "fixed_in": None,
        },
    ]

    # The finding IDs rebuild each finding's ARN.
    arns = [row["arn"] for row in neo4j_session.run(_FINDING_ROWS)]
    assert sorted(arns) == sorted([KERNEL_FINDING_ARN, OPENSSL_FINDING_ARN])


def test_sync_inspector_instances_with_the_same_findings_share_a_set(neo4j_session):
    # Arrange: two instances report the same kernel and openssl findings, and a third
    # reports only the kernel finding.
    kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    findings = [
        _ec2_package_finding(kernel, "i-a", "1" + "a" * 31),
        _ec2_package_finding(openssl, "i-a", "2" + "a" * 31),
        _ec2_package_finding(kernel, "i-b", "3" + "b" * 31),
        _ec2_package_finding(openssl, "i-b", "4" + "b" * 31),
        _ec2_package_finding(kernel, "i-c", "5" + "c" * 31),
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    _sync_package_findings(neo4j_session, findings)

    # Assert: two contents and two sets serve the three instances.
    assert len(check_nodes(neo4j_session, "AWSInspectorFindingContent", ["id"])) == 2
    instances = _instance_findings(neo4j_session)
    assert [row["instance"] for row in instances] == ["i-a", "i-b", "i-c"]
    assert instances[0]["finding_set"] == instances[1]["finding_set"]
    assert instances[2]["finding_set"] != instances[0]["finding_set"]
    # Each instance keeps its own finding IDs.
    ids = [
        {
            "instance": row["instance"],
            "vulnerability": row["vulnerability"],
            "finding_id": row["arn"].rsplit("/", 1)[1],
        }
        for row in neo4j_session.run(_FINDING_ROWS)
    ]
    assert ids == [
        {
            "instance": "i-a",
            "vulnerability": "CVE-2017-9059",
            "finding_id": "1" + "a" * 31,
        },
        {
            "instance": "i-a",
            "vulnerability": "CVE-2023-1234",
            "finding_id": "2" + "a" * 31,
        },
        {
            "instance": "i-b",
            "vulnerability": "CVE-2017-9059",
            "finding_id": "3" + "b" * 31,
        },
        {
            "instance": "i-b",
            "vulnerability": "CVE-2023-1234",
            "finding_id": "4" + "b" * 31,
        },
        {
            "instance": "i-c",
            "vulnerability": "CVE-2017-9059",
            "finding_id": "5" + "c" * 31,
        },
    ]


def test_sync_inspector_keeps_each_findings_own_times(neo4j_session):
    # Arrange: Inspector reported the openssl finding on i-late two days after the
    # instance's other findings, and on i-same at the same time as the others.
    kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    later = kernel["firstObservedAt"] + timedelta(days=2)
    findings = [
        _ec2_package_finding(kernel, "i-late", "1" + "d" * 31),
        _ec2_package_finding(
            openssl,
            "i-late",
            "2" + "d" * 31,
            firstObservedAt=later,
            lastObservedAt=later,
            updatedAt=later,
        ),
        _ec2_package_finding(kernel, "i-same", "3" + "e" * 31),
        _ec2_package_finding(openssl, "i-same", "4" + "e" * 31),
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    _sync_package_findings(neo4j_session, findings)

    # Assert: both instances share a set, and each finding keeps Inspector's times
    # to the millisecond.
    assert len({row["finding_set"] for row in _instance_findings(neo4j_session)}) == 1
    first = _epoch_ms(kernel["firstObservedAt"])
    shifted = _epoch_ms(later)
    assert [
        (r["instance"], r["vulnerability"], r["first_observed"], r["last_observed"])
        for r in neo4j_session.run(_FINDING_ROWS)
    ] == [
        ("i-late", "CVE-2017-9059", first, _epoch_ms(kernel["lastObservedAt"])),
        ("i-late", "CVE-2023-1234", shifted, shifted),
        ("i-same", "CVE-2017-9059", first, _epoch_ms(kernel["lastObservedAt"])),
        ("i-same", "CVE-2023-1234", first, _epoch_ms(openssl["lastObservedAt"])),
    ]


@pytest.mark.parametrize("newer_first", [True, False])
def test_sync_inspector_keeps_every_finding_arn(neo4j_session, newer_first):
    # Arrange: two findings on i-dup report identical content. Inspector returns one
    # of them twice: as it was, and as updated less than a millisecond later with a
    # higher severity.
    kernel, _openssl = LIST_FINDINGS_EC2_PACKAGE
    updated = kernel["updatedAt"] + timedelta(microseconds=300)
    older = _ec2_package_finding(kernel, "i-dup", "2" + "a" * 31)
    newer = _ec2_package_finding(
        kernel, "i-dup", "2" + "a" * 31, updatedAt=updated, severity="HIGH"
    )
    findings = [
        _ec2_package_finding(kernel, "i-dup", "1" + "a" * 31),
        *([newer, older] if newer_first else [older, newer]),
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    _sync_package_findings(neo4j_session, findings)

    # Assert: one row per ARN, and the finding returned twice is its later version.
    prefix = f"arn:aws:inspector2:us-west-2:{TEST_ACC_ID_1}:finding/"
    assert [(r["arn"], r["severity"]) for r in neo4j_session.run(_FINDING_ROWS)] == [
        (prefix + "1" + "a" * 31, kernel["severity"]),
        (prefix + "2" + "a" * 31, "HIGH"),
    ]

    # Two findings with the same content fill two slots of one set.
    _sync_package_findings(
        neo4j_session,
        [
            _ec2_package_finding(kernel, "i-dup", "1" + "a" * 31),
            _ec2_package_finding(kernel, "i-dup", "2" + "a" * 31),
        ],
        update_tag=TEST_UPDATE_TAG + 1,
    )
    assert neo4j_session.run(
        "MATCH (:AWSInspectorFindingSet)-[c:CONTAINS]->() RETURN c.slots",
    ).value() == [[0, 1]]


def test_sync_inspector_removes_instances_that_inspector_stopped_reporting(
    neo4j_session,
):
    # Arrange: a previous sync stored i-kept with the kernel finding and i-gone with
    # the openssl finding.
    kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)
    kept = _ec2_package_finding(kernel, "i-kept", "1" + "f" * 31)
    gone = _ec2_package_finding(openssl, "i-gone", "2" + "f" * 31)
    _sync_package_findings(neo4j_session, [kept, gone], update_tag=TEST_UPDATE_TAG - 1)

    # Act: Inspector no longer reports i-gone.
    _sync_package_findings(neo4j_session, [kept])

    # Assert: i-gone, its set, and its content are gone; i-kept is untouched.
    assert check_nodes(neo4j_session, "AWSInspectorInstanceFindings", ["id"]) == {
        ("i-kept",),
    }
    assert [r["instance"] for r in _instance_findings(neo4j_session)] == ["i-kept"]
    assert len(check_nodes(neo4j_session, "AWSInspectorFindingSet", ["id"])) == 1
    assert check_nodes(
        neo4j_session, "AWSInspectorFindingContent", ["vulnerabilityid"]
    ) == {("CVE-2017-9059",)}


def test_sync_inspector_migrates_only_the_synced_accounts_cve_findings(
    neo4j_session,
):
    # Arrange: two admin accounts each hold a finding that an earlier version
    # labeled :CVE. Only one of them syncs.
    _kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (:AWSAccount {id: $acc})-[:RESOURCE]->(:AWSInspectorFinding:CVE {id: $arn})
        MERGE (:AWSAccount {id: '999999999999'})
              -[:RESOURCE]->(:AWSInspectorFinding:CVE {id: 'arn:other-admin'})
        """,
        acc=TEST_ACC_ID_1,
        arn=OPENSSL_FINDING_ARN,
    )

    # Act
    _sync_package_findings(neo4j_session, [openssl])

    # Assert: the other account's finding keeps :CVE until that account syncs and
    # its findings link to their vulnerability.
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        ("CVE-2023-1234",),
        ("arn:other-admin",),
    }


def test_sync_inspector_keeps_an_instance_whose_findings_were_read_partially(
    neo4j_session,
):
    # Arrange: a previous sync stored i-kept with two findings.
    kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)
    findings = [
        _ec2_package_finding(kernel, "i-kept", "1" + "a" * 31),
        _ec2_package_finding(openssl, "i-kept", "1" + "b" * 31),
    ]
    _sync_package_findings(neo4j_session, findings, update_tag=TEST_UPDATE_TAG - 1)

    # Act: Inspector serves the first finding, then rejects the next page.
    _sync_package_findings(
        neo4j_session,
        findings,
        batch_size=1,
        list_findings_errors_by_page={("1", "1"): INSPECTOR_NOT_ENABLED},
    )

    # Assert: the instance keeps both findings from the previous sync.
    arns = [row["arn"] for row in neo4j_session.run(_FINDING_ROWS)]
    assert [arn.rsplit("/", 1)[1] for arn in arns] == ["1" + "a" * 31, "1" + "b" * 31]


@pytest.mark.parametrize(
    "rejection",
    [
        # Inspector serves one page of a shard, then rejects the next page.
        {"list_findings_errors_by_page": {("1", "1"): INSPECTOR_NOT_ENABLED}},
        # Inspector rejects one shard while another returns findings, and the
        # rejection cancels the sync before it loads them.
        {"list_findings_errors_by_prefix": {"0": INSPECTOR_NOT_ENABLED}},
    ],
)
def test_sync_inspector_preserves_data_when_a_read_fails_after_some_findings(
    neo4j_session, rejection
):
    # Arrange: a finding from a previous run, and an account whose network findings
    # Inspector rejects part of the way through.
    findings = [
        {
            **LIST_FINDINGS_NETWORK[0],
            "findingArn": f"{NETWORK_FINDING_ARN.rsplit('/', 1)[0]}/1{'0' * 30}{digit}",
        }
        for digit in "12"
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _add_stale_finding(neo4j_session, "arn:aws:stale")

    # Act
    _sync_package_findings(neo4j_session, findings, batch_size=1, **rejection)

    # Assert: the read was incomplete, so cleanup kept the previous run's finding.
    assert ("arn:aws:stale",) in check_nodes(
        neo4j_session, "AWSInspectorFinding", ["id"]
    )


@pytest.mark.parametrize("ubuntu_first", [True, False])
def test_sync_inspector_vulnerability_keeps_reference_urls_from_every_batch(
    neo4j_session, ubuntu_first
):
    # Arrange: two findings of one vulnerability, each listing a different
    # distribution's advisory, on one finding ID shard so that Inspector returns
    # them in list order, and loaded in separate batches in either order.
    details = LIST_FINDINGS_EC2_PACKAGE[1]["packageVulnerabilityDetails"]
    advisories = [
        ("1", "NVD", "https://alas.aws.amazon.com/AL2023/ALAS2023-2023-001.html"),
        ("2", "UBUNTU_CVE", "https://ubuntu.com/security/CVE-2023-1234"),
    ]
    findings = [
        {
            **LIST_FINDINGS_EC2_PACKAGE[1],
            "findingArn": f"arn:aws:inspector2:us-west-2:123456789011:finding/1{digit}{'0' * 30}",
            "packageVulnerabilityDetails": {
                **details,
                "source": source,
                "referenceUrls": [url],
            },
        }
        for digit, source, url in (reversed(advisories) if ubuntu_first else advisories)
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    _sync_package_findings(neo4j_session, findings, batch_size=1)

    # Assert
    # The vulnerability keeps one advisory's fields whatever order they arrive in.
    vulnerabilities = neo4j_session.run(
        """
        MATCH (v:AWSInspectorVulnerability)
        RETURN v.id AS id, v.source AS source, v.referenceurls AS urls
        """,
    ).data()
    assert vulnerabilities == [
        {
            "id": "CVE-2023-1234",
            "source": "NVD",
            "urls": [
                "https://alas.aws.amazon.com/AL2023/ALAS2023-2023-001.html",
                "https://ubuntu.com/security/CVE-2023-1234",
            ],
        },
    ]


def test_sync_inspector_packages_reach_package_version(neo4j_session):
    # Arrange: the same openssl build on a Debian instance and an Ubuntu instance.
    _kernel, openssl = LIST_FINDINGS_EC2_PACKAGE
    resource = openssl["resources"][0]
    findings = [
        {
            **_ec2_package_finding(openssl, instance_id, finding_id),
            "resources": [
                {
                    **resource,
                    "id": instance_id,
                    "details": {
                        "awsEc2Instance": {
                            **resource["details"]["awsEc2Instance"],
                            "platform": platform,
                        },
                    },
                },
            ],
        }
        for instance_id, finding_id, platform in [
            ("i-debian", "1" + "a" * 31, "DEBIAN_12"),
            ("i-ubuntu", "2" + "a" * 31, "UBUNTU_22_04"),
        ]
    ]
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $acc})", acc=TEST_ACC_ID_1)

    # Act
    _sync_package_findings(neo4j_session, findings)
    cartography.intel.ontology.packages.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert: each distribution's package reaches the PackageVersion that Trivy's
    # package URL for it names.
    debian = make_normalized_package_id(
        purl="pkg:deb/debian/openssl@1.0.2k-1.amzn2?arch=amd64&distro=debian-12.8",
    )
    ubuntu = make_normalized_package_id(
        purl="pkg:deb/ubuntu/openssl@1.0.2k-1.amzn2?arch=amd64&distro=ubuntu-22.04",
    )
    assert check_rels(
        neo4j_session,
        "PackageVersion",
        "id",
        "AWSInspectorPackage",
        "id",
        "DETECTED_AS",
    ) == {
        (debian, "OS|debian|openssl|0:1.0.2k-1.amzn2.X86_64"),
        (ubuntu, "OS|ubuntu|openssl|0:1.0.2k-1.amzn2.X86_64"),
    }
    assert check_nodes(
        neo4j_session, "PackageVersion", ["id", "name", "version", "type"]
    ) == {
        (debian, "openssl", "1.0.2k-1.amzn2", "deb"),
        (ubuntu, "openssl", "1.0.2k-1.amzn2", "deb"),
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
