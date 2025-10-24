import logging
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Set
from typing import Tuple

import boto3
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.aws.inspector.findings import AWSInspectorFindingSchema
from cartography.models.aws.inspector.findings import InspectorFindingToPackageMatchLink
from cartography.models.aws.inspector.packages import AWSInspectorPackageSchema
from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import AWS_REGION_ACCESS_DENIED_ERROR_CODES
from cartography.util import batch
from cartography.util import is_service_control_policy_explicit_deny
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


@aws_handle_regions
def get_member_accounts(
    session: boto3.session.Session,
    region: str,
) -> List[str]:
    """
    List all the accounts that have delegated access to the account specified by current_aws_account_id.
    """
    client = session.client("inspector2", region_name=region)
    members = list(aws_paginate(client, "list_members", "members"))
    accounts = [m["accountId"] for m in members]
    return accounts


@timeit
def get_inspector_findings(
    session: boto3.session.Session,
    region: str,
    account_id: str,
    batch_size: int,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Query inspector2.list_findings by filtering the request, otherwise the request could timeout.
    First, we filter by account_id. And since there may be millions of CLOSED findings that may never go away,
    only fetch those in ACTIVE or SUPPRESSED statuses.
    Run the query in batches and return an iterator to fetch the results.
    """
    # Note: We can't use @aws_handle_regions decorator here because this function returns a generator.
    # The decorator would only catch exceptions during function call, not during iteration.
    # Instead, we rely on aws_handle_regions being applied at get_member_accounts level,
    # and the paginate operation itself will raise errors that bubble up naturally.
    client = session.client("inspector2", region_name=region)
    logger.info(
        f"Getting findings in batches of {batch_size} for account {account_id} in region {region}"
    )
    aws_args: Dict[str, Any] = {
        "filterCriteria": {
            "awsAccountId": [
                {
                    "comparison": "EQUALS",
                    "value": account_id,
                },
            ],
            "findingStatus": [
                {
                    "comparison": "NOT_EQUALS",
                    "value": "CLOSED",
                },
            ],
        }
    }
    findings_batches = batch(
        aws_paginate(client, "list_findings", "findings", None, **aws_args), batch_size
    )
    yield from findings_batches


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
        if f.get("inspectorScoreDetails"):
            finding["cvssscore"] = f["inspectorScoreDetails"]["adjustedCvss"]["score"]
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
            finding["referenceurls"] = f["packageVulnerabilityDetails"].get(
                "referenceUrls",
            )
            finding["relatedvulnerabilities"] = f["packageVulnerabilityDetails"].get(
                "relatedVulnerabilities",
            )
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
    GraphJob.from_node_schema(
        AWSInspectorFindingSchema(), common_job_parameters, iterationsize=batch_size
    ).run(
        neo4j_session,
    )


def _sync_findings_for_account(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Syncs the findings for a given account in a given region.
    """
    try:
        findings = get_inspector_findings(boto3_session, region, account_id, batch_size)
        if not findings:
            logger.info(
                f"No findings to sync for account {account_id} in region {region}"
            )
            return
        for f_batch in findings:
            finding_data, package_data, finding_to_package_map = (
                transform_inspector_findings(f_batch)
            )
            logger.info(
                f"Loading {len(finding_data)} findings from account {account_id}"
            )
            load_inspector_findings(
                neo4j_session,
                finding_data,
                region,
                update_tag,
                current_aws_account_id,
            )
            logger.info(f"Loading {len(package_data)} packages")
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
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        # Handle the same error codes as aws_handle_regions decorator
        if error_code in AWS_REGION_ACCESS_DENIED_ERROR_CODES:
            error_message = e.response.get("Error", {}).get("Message")
            if is_service_control_policy_explicit_deny(e):
                logger.warning(
                    "Service control policy denied access to Inspector findings for account %s in region %s: %s",
                    account_id,
                    region,
                    error_message,
                )
            else:
                logger.warning(
                    "Access denied to Inspector findings for account %s in region %s. Skipping...",
                    account_id,
                    region,
                )
            return
        else:
            raise


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    batch_size = common_job_parameters.get(
        "experimental_aws_inspector_batch", BATCH_SIZE
    )

    inspector_regions = [
        region for region in regions if region in AWS_INSPECTOR_REGIONS
    ]

    for region in inspector_regions:
        logger.info(
            f"Syncing AWS Inspector findings delegated to account {current_aws_account_id} and region {region}",
        )
        member_accounts = get_member_accounts(boto3_session, region)
        # the current host account may not be considered a "member", but we still fetch its findings
        member_accounts.append(current_aws_account_id)
        logger.info(f"Member accounts to be synced: {member_accounts}")
        for account_id in member_accounts:
            _sync_findings_for_account(
                neo4j_session,
                boto3_session,
                region,
                account_id,
                update_tag,
                current_aws_account_id,
                batch_size,
            )
    common_job_parameters["ACCOUNT_ID"] = current_aws_account_id
    common_job_parameters["UPDATE_TAG"] = update_tag
    cleanup(neo4j_session, common_job_parameters, batch_size)
