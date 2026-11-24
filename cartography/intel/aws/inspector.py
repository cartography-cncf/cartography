import asyncio
import logging
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Set
from typing import Tuple

import aioboto3
import backoff
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.helpers import backoff_handler
from cartography.intel.aws.inspector_finding_sets import InstanceFindingSets
from cartography.intel.aws.inspector_finding_sets import is_ec2_package_finding
from cartography.intel.aws.inspector_finding_sets import transform_finding_content
from cartography.intel.aws.inspector_packages import os_distribution
from cartography.intel.aws.inspector_packages import package_url
from cartography.intel.aws.inspector_packages import resource_platform
from cartography.intel.aws.util.botocore_config import create_aioboto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.intel.trivy.util import canonical_cve_id
from cartography.intel.trivy.util import make_normalized_package_id
from cartography.intel.trivy.util import parse_purl
from cartography.models.aws.inspector.finding_sets import (
    AWSInspectorFindingContentSchema,
)
from cartography.models.aws.inspector.finding_sets import AWSInspectorFindingSetSchema
from cartography.models.aws.inspector.finding_sets import (
    AWSInspectorInstanceFindingsSchema,
)
from cartography.models.aws.inspector.finding_sets import (
    InspectorFindingContentToPackageMatchLink,
)
from cartography.models.aws.inspector.finding_sets import (
    InspectorFindingSetToContentMatchLink,
)
from cartography.models.aws.inspector.findings import AWSInspectorFindingSchema
from cartography.models.aws.inspector.findings import InspectorFindingToPackageMatchLink
from cartography.models.aws.inspector.packages import AWSInspectorPackageSchema
from cartography.models.aws.inspector.vulnerabilities import (
    AWSInspectorVulnerabilitySchema,
)
from cartography.util import AWS_REGION_ACCESS_DENIED_ERROR_CODES
from cartography.util import is_aws_region_skippable_client_error
from cartography.util import is_throttling_exception
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

# As of 7/1/25, Inspector is only available in the below regions. We will need to update this hardcoded list here over
# time. :\ https://docs.aws.amazon.com/general/latest/gr/inspector2.html
AWS_INSPECTOR_REGIONS = {
    "us-east-2",
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "af-south-1",
    "ap-east-1",
    "ap-southeast-3",
    "ap-south-1",
    "ap-northeast-3",
    "ap-northeast-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
    "eu-west-3",
    "eu-north-1",
    "eu-central-2",
    "me-south-1",
    "sa-east-1",
    "us-gov-east-1",
    "us-gov-west-1",
}

BATCH_SIZE = 1000
FINDINGS_PER_WRITE = 100_000


# ListFindings returns at most 100 findings per page, so one paginator spends most
# of a large account's sync waiting on round trips. The API pins finding IDs to 32
# lowercase hex characters, so one finding ARN prefix per hex digit splits an
# account's findings into disjoint shards that together cover every finding, and
# the shards can be paged concurrently.
FINDING_ID_SHARDS = "0123456789abcdef"

# Bounds the findings held in memory when fetching outpaces loading.
MAX_BUFFERED_PAGES = 2 * len(FINDING_ID_SHARDS)

# Connection-level failures that indicate a regional inspector2 endpoint could not
# be reached (e.g. an opt-in region listed in AWS_INSPECTOR_REGIONS but not enabled
# on the account). These are NOT botocore ClientError subclasses.
_INSPECTOR_TRANSIENT_CONNECTION_ERRORS = (
    botocore.exceptions.ConnectTimeoutError,
    botocore.exceptions.EndpointConnectionError,
    botocore.exceptions.ReadTimeoutError,
    botocore.exceptions.ConnectionClosedError,
)

# Errors that mean the account's findings cannot be read in this region, either
# because access is denied or because Inspector is not enabled there.
_SKIPPABLE_FINDINGS_ERROR_CODES = {
    *AWS_REGION_ACCESS_DENIED_ERROR_CODES,
    "ValidationException",
}


async def get_member_accounts(client: Any) -> List[str]:
    """
    List all the accounts that have delegated access to the account the client belongs to.
    """
    try:
        return [
            member["accountId"]
            async for page in client.get_paginator("list_members").paginate()
            for member in page["members"]
        ]
    except botocore.exceptions.ClientError as e:
        if not is_aws_region_skippable_client_error(e):
            raise
        logger.warning(
            "Cannot list Inspector member accounts in region %s. Skipping members: %s",
            client.meta.region_name,
            e,
        )
        return []


async def _get_inspector_findings_shard(
    client: Any,
    account_id: str,
    shard: str,
    pages: asyncio.Queue[List[Dict[str, Any]] | None],
    state: "_SyncState",
) -> None:
    finding_arn_prefix = (
        f"arn:{client.meta.partition}:inspector2:{client.meta.region_name}:"
        f"{account_id}:finding/{shard}"
    )
    params: Dict[str, Any] = {
        "filterCriteria": {
            "awsAccountId": [{"comparison": "EQUALS", "value": account_id}],
            # There may be millions of CLOSED findings that never go away, so only
            # fetch those in ACTIVE or SUPPRESSED statuses.
            "findingStatus": [{"comparison": "NOT_EQUALS", "value": "CLOSED"}],
            "findingArn": [{"comparison": "PREFIX", "value": finding_arn_prefix}],
        },
    }
    while True:
        page = await _list_findings_page(client, params)
        # Counted here rather than when the page loads: a failing shard cancels the
        # loader, which could otherwise miss a page another shard already returned.
        state.responses_received += 1
        await pages.put(page["findings"])
        next_token = page.get("nextToken")
        if not next_token:
            break
        params["nextToken"] = next_token
    await pages.put(None)


def _is_retryable_findings_error(error: botocore.exceptions.ClientError) -> bool:
    if is_throttling_exception(error):
        return True
    # A request that waited too long to be sent; a retry signs it again.
    details = error.response.get("Error", {})
    return details.get("Code") == "InvalidSignatureException" and (
        "Signature expired" in details.get("Message", "")
    )


# A large account pages through its findings for hours with every shard in flight,
# so one throttle can outlast the client's own retries before the last page.
# Retrying the page resumes the shard from that page. Failing instead discards the
# account's sync and skips the cleanup of findings that have since closed.
@backoff.on_exception(  # type: ignore[misc]
    backoff.expo,
    botocore.exceptions.ClientError,
    max_time=600,
    giveup=lambda e: not _is_retryable_findings_error(e),
    on_backoff=backoff_handler,
)
async def _list_findings_page(client: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return await client.list_findings(**params)


@dataclass
class _SyncState:
    """Data that spans the batches, member accounts, and regions of one sync."""

    # A vulnerability's findings arrive across many batches, regions, and member
    # accounts. Merging them all here means each load writes every reference URL and
    # the same advisory, whatever order the findings arrive in, and a vulnerability
    # is written again only when that merge changes it.
    vulnerabilities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    loaded_package_ids: Set[str] = field(default_factory=set)
    loaded_content_ids: Set[str] = field(default_factory=set)
    finding_sets: InstanceFindingSets = field(default_factory=InstanceFindingSets)
    # ListFindings responses for the account being read, so a read that fails after
    # some of them is not mistaken for an account where Inspector is not enabled.
    responses_received: int = 0


def transform_inspector_findings(
    results: List[Dict[str, Any]],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, str]],
    List[Dict[str, Any]],
]:
    findings_list: List[Dict] = []
    packages_by_id: Dict[str, Dict[str, Any]] = {}
    finding_to_package_map: List[Dict[str, str]] = []
    vulnerabilities: Dict[str, Dict[str, Any]] = {}

    for f in results:
        finding: Dict = {}

        finding["id"] = f["findingArn"]
        finding["arn"] = f["findingArn"]
        finding["severity"] = f["severity"]
        finding["name"] = f["title"]
        finding["firstobservedat"] = f["firstObservedAt"]
        finding["updatedat"] = f["updatedAt"]
        finding["awsaccount"] = f["awsAccountId"]
        finding["type"] = f["type"]
        finding["status"] = f["status"]
        finding["fixavailable"] = f.get("fixAvailable")
        finding["exploitavailable"] = f.get("exploitAvailable")
        if f.get("exploitabilityDetails"):
            finding["lastknownexploitat"] = f["exploitabilityDetails"].get(
                "lastKnownExploitAt",
            )
        if f.get("epss"):
            finding["epss_score_inspector"] = f["epss"].get("score")
        if f.get("inspectorScoreDetails"):
            finding["cvssscore"] = f["inspectorScoreDetails"]["adjustedCvss"]["score"]
            finding["cvssvector"] = f["inspectorScoreDetails"]["adjustedCvss"][
                "scoringVector"
            ]
        if f["resources"][0]["type"] == "AWS_EC2_INSTANCE":
            finding["instanceid"] = f["resources"][0]["id"]
        if f["resources"][0]["type"] == "AWS_ECR_CONTAINER_IMAGE":
            finding["ecrimageid"] = f["resources"][0]["id"].split("/")[2]
        if f["resources"][0]["type"] == "AWS_ECR_REPOSITORY":
            finding["ecrrepositoryid"] = f["resources"][0]["id"]
        if f.get("networkReachabilityDetails"):
            finding["protocol"] = f["networkReachabilityDetails"]["protocol"]
            finding["portrangebegin"] = f["networkReachabilityDetails"][
                "openPortRange"
            ]["begin"]
            finding["portrangeend"] = f["networkReachabilityDetails"]["openPortRange"][
                "end"
            ]
            finding["portrange"] = _port_range_string(f["networkReachabilityDetails"])
        details = f.get("packageVulnerabilityDetails")
        if details:
            vulnerability_id = details["vulnerabilityId"]
            finding["vulnerabilityid"] = vulnerability_id
            finding["cve_id"] = canonical_cve_id(vulnerability_id)
            finding["vendorseverity"] = details.get("vendorSeverity")
            _add_vulnerability(vulnerabilities, f, details)

            packages = transform_inspector_packages(details, resource_platform(f))
            finding["vulnerablepackageids"] = list(packages.keys())
            packages_by_id.update(packages)
            for package_id, package in packages.items():
                finding_to_package_map.append(
                    {
                        "findingarn": finding["id"],
                        "packageid": package_id,
                        **_package_link_fields(package),
                    }
                )
        else:
            # Only package vulnerability findings share a description across
            # resources; a network or code finding describes its own resource.
            finding["description"] = f["description"]
        findings_list.append(finding)
    return (
        findings_list,
        list(packages_by_id.values()),
        finding_to_package_map,
        list(vulnerabilities.values()),
    )


def transform_ec2_package_findings(
    results: List[Dict[str, Any]],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Tuple[Dict[str, Any], str]],
]:
    """Transform package vulnerability findings on EC2 instances into shared contents.

    Returns the contents, packages, content-to-package links, and vulnerabilities, plus
    each finding paired with its content ID for grouping into finding sets.
    """
    contents: Dict[str, Dict[str, Any]] = {}
    packages_by_id: Dict[str, Dict[str, Any]] = {}
    content_to_package_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    vulnerabilities: Dict[str, Dict[str, Any]] = {}
    finding_contents: List[Tuple[Dict[str, Any], str]] = []
    for f in results:
        details = f["packageVulnerabilityDetails"]
        packages = transform_inspector_packages(details, resource_platform(f))
        content = transform_finding_content(f, list(packages.keys()))
        contents[content["id"]] = content
        _add_vulnerability(vulnerabilities, f, details)
        packages_by_id.update(packages)
        for package_id, package in packages.items():
            content_to_package_map[(content["id"], package_id)] = {
                "contentid": content["id"],
                "packageid": package_id,
                **_package_link_fields(package),
            }
        finding_contents.append((f, content["id"]))
    return (
        list(contents.values()),
        list(packages_by_id.values()),
        list(content_to_package_map.values()),
        list(vulnerabilities.values()),
        finding_contents,
    )


def _vulnerability_record(
    finding: Dict[str, Any],
    details: Dict[str, Any],
) -> Dict[str, Any]:
    vulnerability_id = details["vulnerabilityId"]
    cve_id = canonical_cve_id(vulnerability_id)
    return {
        "id": vulnerability_id,
        "vulnerabilityid": vulnerability_id,
        "cve_id": cve_id,
        "has_cve": "true" if cve_id else "false",
        "description": finding["description"],
        "referenceurls": sorted(set(details.get("referenceUrls") or [])),
        "relatedvulnerabilities": details.get("relatedVulnerabilities"),
        # packageVulnerabilityDetails.cvss is a list of per-source (vendor/NVD)
        # CVSS entries.
        "vendorcvssvectors": [c["scoringVector"] for c in details.get("cvss", [])],
        "vendorcvssscores": [c["baseScore"] for c in details.get("cvss", [])],
        "source": details.get("source"),
        "sourceurl": details.get("sourceUrl"),
        "vendorcreatedat": details.get("vendorCreatedAt"),
        "vendorupdatedat": details.get("vendorUpdatedAt"),
    }


def _add_vulnerability(
    vulnerabilities: Dict[str, Dict[str, Any]],
    finding: Dict[str, Any],
    details: Dict[str, Any],
) -> None:
    _merge_vulnerability(vulnerabilities, _vulnerability_record(finding, details))


def _merge_vulnerability(
    vulnerabilities: Dict[str, Dict[str, Any]],
    candidate: Dict[str, Any],
) -> bool:
    """Merge one finding's view of a vulnerability in; return whether it changed."""
    vulnerability = vulnerabilities.get(candidate["id"])
    if vulnerability is None:
        vulnerabilities[candidate["id"]] = dict(candidate)
        return True
    # Each finding lists the advisories of its own distribution, so the
    # vulnerability gets every reference URL that any of its findings report.
    urls = sorted(set(vulnerability["referenceurls"]) | set(candidate["referenceurls"]))
    changed = urls != vulnerability["referenceurls"]
    if _advisory_order(candidate) < _advisory_order(vulnerability):
        vulnerability.update(candidate)
        changed = True
    vulnerability["referenceurls"] = urls
    return changed


def _advisory_order(vulnerability: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(
        str(vulnerability[key])
        for key in (
            "source",
            "sourceurl",
            "description",
            "vendorcvssvectors",
            "vendorcvssscores",
            "vendorcreatedat",
            "vendorupdatedat",
            "relatedvulnerabilities",
        )
    )


def transform_inspector_packages(
    package_details: Dict[str, Any],
    platform: str | None,
) -> Dict[str, Any]:
    packages: Dict[str, Any] = {}
    for package in package_details["vulnerablePackages"]:
        derived = _package_identity(
            platform,
            package.get("packageManager"),
            package["name"],
            package.get("epoch"),
            package["version"],
            package.get("release"),
            package.get("arch"),
        )
        packages[derived["id"]] = {**package, **derived}
    return packages


# Instances launched from one image report the same packages, so a fleet repeats each
# package thousands of times; its ID and package URL are computed once.
@lru_cache(maxsize=65536)
def _package_identity(
    platform: str | None,
    manager: str | None,
    name: str,
    epoch: Any,
    version: str,
    release: str | None,
    arch: str | None,
) -> Dict[str, Any]:
    # Following RPM package naming convention for consistency
    evra = f"{f'{epoch}:' if epoch not in (None, '') else ''}{version}"
    evra += f"-{release}" if release else ""
    evra += f".{arch}" if arch else ""
    # pip and npm can both have a requests 2.28.0, and Debian and Ubuntu the same
    # curl build, so the manager and an operating system's distribution are part of
    # the ID.
    prefix = f"{manager}|" if manager else ""
    if manager == "OS":
        distribution = os_distribution(platform)
        # An unrecognized platform gets its own key, so a package without a package
        # URL never shares a node with one that has it.
        prefix += (
            f"{distribution[1]}|"
            if distribution
            else f"platform:{platform or 'unknown'}|"
        )
    purl = package_url(
        {
            "packageManager": manager,
            "name": name,
            "epoch": epoch,
            "version": version,
            "release": release,
            "arch": arch,
        },
        platform,
    )
    parsed = parse_purl(purl) or {}
    return {
        "id": f"{prefix}{name}|{evra}",
        "purl": purl,
        "type": parsed.get("type"),
        "purl_version": parsed.get("version"),
        "normalized_id": make_normalized_package_id(purl=purl),
    }


def _package_link_fields(package: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "remediation": package.get("remediation"),
        "fixedInVersion": package.get("fixedInVersion"),
        "filePath": package.get("filePath"),
        "sourceLayerHash": package.get("sourceLayerHash"),
        "sourceLambdaLayerArn": package.get("sourceLambdaLayerArn"),
    }


def _port_range_string(details: Dict[str, Any]) -> str:
    begin = details["openPortRange"]["begin"]
    end = details["openPortRange"]["end"]
    return f"{begin}-{end}"


@timeit
def load_inspector_findings(
    neo4j_session: neo4j.Session,
    findings: List[Dict[str, Any]],
    region: str,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorFindingSchema(),
        findings,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_vulnerabilities(
    neo4j_session: neo4j.Session,
    vulnerabilities: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorVulnerabilitySchema(),
        vulnerabilities,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_finding_contents(
    neo4j_session: neo4j.Session,
    contents: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorFindingContentSchema(),
        contents,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_finding_content_to_package_match_links(
    neo4j_session: neo4j.Session,
    content_to_package_map: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load_matchlinks(
        neo4j_session,
        InspectorFindingContentToPackageMatchLink(),
        content_to_package_map,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )


@timeit
def load_inspector_finding_sets(
    neo4j_session: neo4j.Session,
    finding_sets: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorFindingSetSchema(),
        finding_sets,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_finding_set_contents(
    neo4j_session: neo4j.Session,
    finding_set_slots: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load_matchlinks(
        neo4j_session,
        InspectorFindingSetToContentMatchLink(),
        finding_set_slots,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )


@timeit
def load_inspector_instance_findings(
    neo4j_session: neo4j.Session,
    instance_findings: List[Dict[str, Any]],
    region: str,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorInstanceFindingsSchema(),
        instance_findings,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_packages(
    neo4j_session: neo4j.Session,
    packages: List[Dict[str, Any]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorPackageSchema(),
        packages,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_inspector_finding_to_package_match_links(
    neo4j_session: neo4j.Session,
    finding_to_package_map: List[Dict[str, str]],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load_matchlinks(
        neo4j_session,
        InspectorFindingToPackageMatchLink(),
        finding_to_package_map,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )


# DEPRECATED: migrates graphs synced by earlier versions; will be removed in v1.0.0.
@timeit
def migrate_legacy_cve_labels(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    run_scoped_analysis_job(
        "aws_inspector_cve_migration.json",
        neo4j_session,
        {**common_job_parameters, "AWS_ID": current_aws_account_id},
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    batch_size: int = BATCH_SIZE,
) -> None:
    logger.info("Running AWS Inspector cleanup")
    # Stale findings go first: deleting them also deletes their HAS rels, which
    # leaves the matchlink cleanup only the rels of findings that are still current.
    GraphJob.from_node_schema(
        AWSInspectorFindingSchema(), common_job_parameters, iterationsize=batch_size
    ).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        InspectorFindingToPackageMatchLink(),
        "AWSAccount",
        common_job_parameters["ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
        iterationsize=batch_size,
    ).run(
        neo4j_session,
    )
    # An instance that Inspector stopped reporting takes only its own node with it; its
    # set and contents go once no instance reports them.
    for schema in (
        AWSInspectorInstanceFindingsSchema(),
        AWSInspectorFindingSetSchema(),
        AWSInspectorFindingContentSchema(),
    ):
        GraphJob.from_node_schema(
            schema, common_job_parameters, iterationsize=batch_size
        ).run(
            neo4j_session,
        )
    GraphJob.from_matchlink(
        InspectorFindingSetToContentMatchLink(),
        "AWSAccount",
        common_job_parameters["ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
        iterationsize=batch_size,
    ).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        InspectorFindingContentToPackageMatchLink(),
        "AWSAccount",
        common_job_parameters["ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
        iterationsize=batch_size,
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AWSInspectorPackageSchema(), common_job_parameters, iterationsize=batch_size
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AWSInspectorVulnerabilitySchema(),
        common_job_parameters,
        iterationsize=batch_size,
    ).run(
        neo4j_session,
    )


def _load_inspector_findings_batch(
    neo4j_session: neo4j.Session,
    findings: List[Dict[str, Any]],
    region: str,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
    state: _SyncState,
) -> None:
    ec2_package_findings = [f for f in findings if is_ec2_package_finding(f)]
    other_findings = [f for f in findings if not is_ec2_package_finding(f)]
    finding_data, package_data, finding_to_package_map, vulnerability_data = (
        transform_inspector_findings(other_findings)
    )
    (
        content_data,
        content_package_data,
        content_to_package_map,
        content_vulnerability_data,
        finding_contents,
    ) = transform_ec2_package_findings(ec2_package_findings)

    changed_vulnerability_ids = {
        vulnerability["id"]
        for vulnerability in vulnerability_data + content_vulnerability_data
        if _merge_vulnerability(state.vulnerabilities, vulnerability)
    }
    # A package node holds only what its ID encodes, so it needs one write per sync.
    new_packages = {
        p["id"]: p
        for p in package_data + content_package_data
        if p["id"] not in state.loaded_package_ids
    }
    new_contents = [c for c in content_data if c["id"] not in state.loaded_content_ids]
    new_content_ids = {c["id"] for c in new_contents}

    # Findings and contents link to their vulnerability and packages on load, so those
    # must exist first.
    load_inspector_vulnerabilities(
        neo4j_session,
        [dict(state.vulnerabilities[id]) for id in changed_vulnerability_ids],
        update_tag,
        current_aws_account_id,
    )
    load_inspector_packages(
        neo4j_session,
        list(new_packages.values()),
        update_tag,
        current_aws_account_id,
    )
    state.loaded_package_ids.update(new_packages)
    logger.info(f"Loading {len(finding_data)} findings from account {account_id}")
    load_inspector_findings(
        neo4j_session,
        finding_data,
        region,
        update_tag,
        current_aws_account_id,
    )
    logger.info(
        f"Loading {len(finding_to_package_map)} finding to package relationships"
    )
    load_inspector_finding_to_package_match_links(
        neo4j_session,
        finding_to_package_map,
        update_tag,
        current_aws_account_id,
    )
    logger.info(
        f"Loading {len(new_contents)} new finding contents for "
        f"{len(ec2_package_findings)} EC2 package findings from account {account_id}"
    )
    load_inspector_finding_contents(
        neo4j_session,
        new_contents,
        update_tag,
        current_aws_account_id,
    )
    load_inspector_finding_content_to_package_match_links(
        neo4j_session,
        [m for m in content_to_package_map if m["contentid"] in new_content_ids],
        update_tag,
        current_aws_account_id,
    )
    state.loaded_content_ids.update(new_content_ids)
    for finding, content_id in finding_contents:
        state.finding_sets.add(finding, content_id)


def _load_inspector_finding_sets(
    neo4j_session: neo4j.Session,
    region: str,
    update_tag: int,
    current_aws_account_id: str,
    state: _SyncState,
) -> None:
    finding_sets, finding_set_slots, instance_findings = state.finding_sets.build()
    logger.info(
        f"Loading {len(finding_sets)} finding sets for {len(instance_findings)} "
        f"EC2 instances in region {region}"
    )
    # Sets carry their content IDs and instances their findings' IDs and times, so
    # writes are bounded by findings, not rows: a fleet of large instances would
    # otherwise send millions of findings in one transaction.
    for batch in _batches_of_findings(finding_sets, "content_ids"):
        load_inspector_finding_sets(
            neo4j_session, batch, update_tag, current_aws_account_id
        )
    load_inspector_finding_set_contents(
        neo4j_session,
        finding_set_slots,
        update_tag,
        current_aws_account_id,
    )
    for batch in _batches_of_findings(instance_findings, "finding_ids"):
        load_inspector_instance_findings(
            neo4j_session, batch, region, update_tag, current_aws_account_id
        )


def _batches_of_findings(
    rows: List[Dict[str, Any]],
    findings_key: str,
) -> Iterator[List[Dict[str, Any]]]:
    batch: List[Dict[str, Any]] = []
    batch_findings = 0
    for row in rows:
        if batch and batch_findings + len(row[findings_key]) > FINDINGS_PER_WRITE:
            yield batch
            batch, batch_findings = [], 0
        batch.append(row)
        batch_findings += len(row[findings_key])
    if batch:
        yield batch


async def _load_inspector_findings(
    neo4j_session: neo4j.Session,
    client: Any,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
    batch_size: int,
    state: _SyncState,
) -> None:
    region = client.meta.region_name
    pages: asyncio.Queue[List[Dict[str, Any]] | None] = asyncio.Queue(
        maxsize=MAX_BUFFERED_PAGES,
    )
    last_load: Future[None] | None = None
    # Loads run in a worker thread so a slow write does not stall the shards: a
    # request botocore has signed waits for the event loop to send it, and AWS
    # rejects a signature older than five minutes. Leaving the executor waits for a
    # load still running when a shard fails, so the next account's load never
    # shares the Neo4j session with it.
    try:
        with ThreadPoolExecutor(max_workers=1) as loader:
            async with asyncio.TaskGroup() as shards:
                for shard in FINDING_ID_SHARDS:
                    shards.create_task(
                        _get_inspector_findings_shard(
                            client, account_id, shard, pages, state
                        ),
                    )

                async def load(batch: List[Dict[str, Any]]) -> None:
                    nonlocal last_load
                    last_load = loader.submit(
                        _load_inspector_findings_batch,
                        neo4j_session,
                        batch,
                        region,
                        account_id,
                        update_tag,
                        current_aws_account_id,
                        state,
                    )
                    await asyncio.wrap_future(last_load)

                findings: List[Dict[str, Any]] = []
                unfinished_shards = len(FINDING_ID_SHARDS)
                while unfinished_shards:
                    page = await pages.get()
                    if page is None:
                        unfinished_shards -= 1
                        continue
                    findings.extend(page)
                    while len(findings) >= batch_size:
                        await load(findings[:batch_size])
                        del findings[:batch_size]
                if findings:
                    await load(findings)
    except ExceptionGroup as errors:
        # Raising one failure keeps the error types callers handle. Requests from
        # every shard are in flight at once, so more than one can fail before the
        # task group cancels the rest; raise the most severe so a skippable error
        # never hides one that must stop cleanup or the sync.
        failures: List[BaseException] = list(errors.exceptions)
        # A shard failure cancels the wait for a load but not the load, so a write
        # that failed meanwhile is missing from the group.
        if last_load is not None and not last_load.cancelled():
            load_error = last_load.exception()
            if load_error is not None:
                failures.append(load_error)
        raise max(failures, key=_shard_failure_severity)


def _is_skippable_findings_error(error: BaseException) -> bool:
    return (
        isinstance(error, botocore.exceptions.ClientError)
        and error.response.get("Error", {}).get("Code")
        in _SKIPPABLE_FINDINGS_ERROR_CODES
    )


def _shard_failure_severity(error: BaseException) -> int:
    if _is_skippable_findings_error(error):
        return 0
    if isinstance(error, _INSPECTOR_TRANSIENT_CONNECTION_ERRORS):
        return 1
    return 2


async def _sync_findings_for_account(
    neo4j_session: neo4j.Session,
    client: Any,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
    state: _SyncState,
    batch_size: int = BATCH_SIZE,
) -> bool:
    """
    Syncs the findings for a given account in the client's region.

    Returns True if the sync completed (including the cases where the region was
    skipped due to a ClientError such as AccessDenied or "Inspector not enabled",
    which are expected and safe to treat as "no findings"). Returns False if the
    region was skipped due to a transient connection-level failure to the regional
    inspector2 endpoint, or due to a skippable ClientError after some of the
    account's findings had loaded. The caller must then not run cleanup for this
    account, so that last-known-good findings are preserved.
    """
    region = client.meta.region_name
    state.responses_received = 0
    logger.info(
        f"Getting findings in batches of {batch_size} for account {account_id} in region {region}"
    )
    try:
        await _load_inspector_findings(
            neo4j_session,
            client,
            account_id,
            update_tag,
            current_aws_account_id,
            batch_size,
            state,
        )
    except _INSPECTOR_TRANSIENT_CONNECTION_ERRORS:
        state.finding_sets.discard_account(account_id)
        logger.warning(
            "Transient connection failure to Inspector endpoint for account %s "
            "in region %s. Skipping region.",
            account_id,
            region,
        )
        return False
    except botocore.exceptions.ClientError as e:
        if not _is_skippable_findings_error(e):
            raise
        # A skippable error after some findings loaded leaves the read incomplete.
        state.finding_sets.discard_account(account_id)
        partial = state.responses_received > 0
        logger.warning(
            "Skipping Inspector findings for account %s in region %s: %s",
            account_id,
            region,
            e,
        )
        return not partial
    return True


async def _sync_findings(
    neo4j_session: neo4j.Session,
    aioboto3_session: aioboto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    batch_size: int,
) -> bool:
    """
    Syncs the findings delegated to the current account in every region.

    Returns whether every regional endpoint was reached, which makes cleanup safe.
    """
    cleanup_safe = True
    state = _SyncState()
    for region in regions:
        logger.info(
            f"Syncing AWS Inspector findings delegated to account {current_aws_account_id} and region {region}",
        )
        async with create_aioboto3_client(
            aioboto3_session,
            "inspector2",
            region_name=region,
            config=get_botocore_config(max_pool_connections=len(FINDING_ID_SHARDS)),
        ) as client:
            try:
                member_accounts = await get_member_accounts(client)
            except _INSPECTOR_TRANSIENT_CONNECTION_ERRORS:
                # Reaching the regional inspector2 endpoint failed at the connection
                # level (e.g. an opt-in region listed in AWS_INSPECTOR_REGIONS that
                # is not enabled on this account). Skip the whole region.
                logger.warning(
                    "Transient connection failure to Inspector endpoint for account %s "
                    "in region %s while listing member accounts. Skipping region.",
                    current_aws_account_id,
                    region,
                )
                cleanup_safe = False
                continue
            # the current host account may not be considered a "member", but we still fetch its findings
            member_accounts.append(current_aws_account_id)
            logger.info(f"Member accounts to be synced: {member_accounts}")
            for account_id in member_accounts:
                synced = await _sync_findings_for_account(
                    neo4j_session,
                    client,
                    account_id,
                    update_tag,
                    current_aws_account_id,
                    state,
                    batch_size,
                )
                if not synced:
                    cleanup_safe = False
            # An instance's finding set is known only once all of the region's findings
            # have loaded.
            _load_inspector_finding_sets(
                neo4j_session,
                region,
                update_tag,
                current_aws_account_id,
                state,
            )
    return cleanup_safe


@timeit
def sync(
    neo4j_session: neo4j.Session,
    aioboto3_session: aioboto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    batch_size = common_job_parameters.get(
        "experimental_aws_inspector_batch", BATCH_SIZE
    )
    if batch_size < 1:
        raise ValueError(
            f"experimental_aws_inspector_batch must be at least 1, got {batch_size}",
        )

    inspector_regions = [
        region for region in regions if region in AWS_INSPECTOR_REGIONS
    ]

    # If any region is skipped because of a transient connection-level failure to
    # its inspector2 endpoint, we must not run cleanup: deleting findings for a
    # region we couldn't reach would wipe out last-known-good data.
    cleanup_safe = asyncio.run(
        _sync_findings(
            neo4j_session,
            aioboto3_session,
            inspector_regions,
            current_aws_account_id,
            update_tag,
            batch_size,
        ),
    )

    if cleanup_safe:
        common_job_parameters["ACCOUNT_ID"] = current_aws_account_id
        common_job_parameters["UPDATE_TAG"] = update_tag
        cleanup(neo4j_session, common_job_parameters, batch_size)
        # Only after a complete read, so every surviving finding already links to
        # the vulnerability that now carries :CVE, and only after cleanup, so the
        # findings it deletes are not migrated first.
        migrate_legacy_cve_labels(
            neo4j_session, current_aws_account_id, common_job_parameters
        )
    else:
        logger.warning(
            "Skipping AWS Inspector cleanup for account %s because one or more regions "
            "were transiently skipped. Preserving last-known-good data.",
            current_aws_account_id,
        )
