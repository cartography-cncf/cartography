import asyncio
import logging
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
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
from cartography.intel.aws.util.botocore_config import create_aioboto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.inspector.findings import AWSInspectorFindingSchema
from cartography.models.aws.inspector.findings import InspectorFindingToPackageMatchLink
from cartography.models.aws.inspector.packages import AWSInspectorPackageSchema
from cartography.util import AWS_REGION_ACCESS_DENIED_ERROR_CODES
from cartography.util import is_aws_region_skippable_client_error
from cartography.util import is_throttling_exception
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


def transform_inspector_findings(
    results: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, str]]]:
    findings_list: List[Dict] = []
    packages_set: Set[frozenset] = set()
    finding_to_package_map: List[Dict[str, str]] = []

    for f in results:
        finding: Dict = {}

        finding["id"] = f["findingArn"]
        finding["arn"] = f["findingArn"]
        finding["severity"] = f["severity"]
        finding["name"] = f["title"]
        finding["firstobservedat"] = f["firstObservedAt"]
        finding["updatedat"] = f["updatedAt"]
        finding["awsaccount"] = f["awsAccountId"]
        finding["description"] = f["description"]
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
        if f.get("packageVulnerabilityDetails"):
            finding["vulnerabilityid"] = f["packageVulnerabilityDetails"][
                "vulnerabilityId"
            ]
            # Package-vulnerability findings are CVE-backed; expose the id under a
            # normalized cve_id so it feeds the :CVE ontology label's _ont_cve_id.
            # Network/code findings never enter this block, so their cve_id stays null.
            finding["cve_id"] = f["packageVulnerabilityDetails"]["vulnerabilityId"]
            finding["referenceurls"] = f["packageVulnerabilityDetails"].get(
                "referenceUrls",
            )
            finding["relatedvulnerabilities"] = f["packageVulnerabilityDetails"].get(
                "relatedVulnerabilities",
            )
            # packageVulnerabilityDetails.cvss is a list of per-source (vendor/NVD)
            # CVSS entries.
            finding["vendorcvssvectors"] = []
            finding["vendorcvssscores"] = []
            for cvss in f["packageVulnerabilityDetails"].get("cvss", []):
                finding["vendorcvssvectors"].append(cvss["scoringVector"])
                finding["vendorcvssscores"].append(cvss["baseScore"])
            finding["source"] = f["packageVulnerabilityDetails"].get("source")
            finding["sourceurl"] = f["packageVulnerabilityDetails"].get("sourceUrl")
            finding["vendorcreatedat"] = f["packageVulnerabilityDetails"].get(
                "vendorCreatedAt",
            )
            finding["vendorseverity"] = f["packageVulnerabilityDetails"].get(
                "vendorSeverity",
            )
            finding["vendorupdatedat"] = f["packageVulnerabilityDetails"].get(
                "vendorUpdatedAt",
            )

            packages = transform_inspector_packages(f["packageVulnerabilityDetails"])
            finding["vulnerablepackageids"] = list(packages.keys())
            for package_id, package in packages.items():
                finding_to_package_map.append(
                    {
                        "findingarn": finding["id"],
                        "packageid": package_id,
                        "remediation": package.get("remediation"),
                        "fixedInVersion": package.get("fixedInVersion"),
                        "filePath": package.get("filePath"),
                        "sourceLayerHash": package.get("sourceLayerHash"),
                        "sourceLambdaLayerArn": package.get("sourceLambdaLayerArn"),
                    }
                )
                packages_set.add(frozenset(package.items()))
        findings_list.append(finding)
    packages_list = [dict(p) for p in packages_set]
    return findings_list, packages_list, finding_to_package_map


def transform_inspector_packages(
    package_details: Dict[str, Any],
) -> Dict[str, Any]:
    packages: Dict[str, Any] = {}
    for package in package_details["vulnerablePackages"]:
        # Following RPM package naming convention for consistency
        name = package["name"]  # Mandatory field
        epoch = str(package.get("epoch", ""))
        if epoch:
            epoch = f"{epoch}:"
        version = package["version"]  # Mandatory field
        release = package.get("release", "")
        if release:
            release = f"-{release}"
        arch = package.get("arch", "")
        if arch:
            arch = f".{arch}"
        id = f"{name}|{epoch}{version}{release}{arch}"
        packages[id] = {**package, "id": id}

    return packages


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
    GraphJob.from_node_schema(
        AWSInspectorPackageSchema(), common_job_parameters, iterationsize=batch_size
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
) -> None:
    finding_data, package_data, finding_to_package_map = transform_inspector_findings(
        findings
    )
    logger.info(f"Loading {len(finding_data)} findings from account {account_id}")
    load_inspector_findings(
        neo4j_session,
        finding_data,
        region,
        update_tag,
        current_aws_account_id,
    )
    load_inspector_packages(
        neo4j_session,
        package_data,
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


async def _load_inspector_findings(
    neo4j_session: neo4j.Session,
    client: Any,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
    batch_size: int,
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
                        _get_inspector_findings_shard(client, account_id, shard, pages),
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
    batch_size: int = BATCH_SIZE,
) -> bool:
    """
    Syncs the findings for a given account in the client's region.

    Returns True if the sync completed (including the cases where the region was
    skipped due to a ClientError such as AccessDenied or "Inspector not enabled",
    which are expected and safe to treat as "no findings"). Returns False if the
    region was skipped due to a transient connection-level failure to the regional
    inspector2 endpoint, in which case the caller must not run cleanup for this
    account so that last-known-good findings are preserved.
    """
    region = client.meta.region_name
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
        )
    except _INSPECTOR_TRANSIENT_CONNECTION_ERRORS:
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
        logger.warning(
            "Skipping Inspector findings for account %s in region %s: %s",
            account_id,
            region,
            e,
        )
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
                    batch_size,
                )
                if not synced:
                    cleanup_safe = False
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
    else:
        logger.warning(
            "Skipping AWS Inspector cleanup for account %s because one or more regions "
            "were transiently skipped. Preserving last-known-good data.",
            current_aws_account_id,
        )
