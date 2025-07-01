import logging
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.inspector.findings import AWSInspectorFindingSchema
from cartography.models.aws.inspector.packages import AWSInspectorPackageSchema
from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import batch
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

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
@aws_handle_regions
def get_inspector_findings(
    session: boto3.session.Session,
    region: str,
    account_id: str,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Query inspector2.list_findings by filtering the request, otherwise the request could timeout.
    First, we filter by account_id. And since there may be millions of CLOSED findings that may never go away,
    only fetch those in ACTIVE or SUPPRESSED statuses.
    Run the query in batches of 1000 findings and return an iterator to fetch the results.
    """
    client = session.client("inspector2", region_name=region)
    logger.info(
        f"Getting findings in batches of {BATCH_SIZE} for account {account_id} in region {region}"
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
        aws_paginate(client, "list_findings", "findings", None, **aws_args), BATCH_SIZE
    )
    yield from findings_batches


def transform_inspector_findings(
    results: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    findings_list: List[Dict] = []
    packages: Dict[str, Any] = {}

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

            new_packages = _process_packages(
                f["packageVulnerabilityDetails"],
                f["awsAccountId"],
                f["findingArn"],
            )
            finding["vulnerablepackageids"] = list(new_packages.keys())
            packages = {**packages, **new_packages}

        findings_list.append(finding)
    packages_list = transform_inspector_packages(packages)
    return findings_list, packages_list


def transform_inspector_packages(packages: Dict[str, Any]) -> List[Dict[str, Any]]:
    packages_list: List[Dict] = []
    for package_id in packages.keys():
        packages_list.append(packages[package_id])

    return packages_list


def _process_packages(
    package_details: Dict[str, Any],
    aws_account_id: str,
    finding_arn: str,
) -> Dict[str, Any]:
    packages: Dict[str, Any] = {}
    for package in package_details["vulnerablePackages"]:
        new_package = {}
        new_package["id"] = (
            f"{package.get('name', '')}|"
            f"{package.get('arch', '')}|"
            f"{package.get('version', '')}|"
            f"{package.get('release', '')}|"
            f"{package.get('epoch', '')}"
        )
        new_package["name"] = package.get("name")
        new_package["arch"] = package.get("arch")
        new_package["version"] = package.get("version")
        new_package["release"] = package.get("release")
        new_package["epoch"] = package.get("epoch")
        new_package["manager"] = package.get("packageManager")
        new_package["filepath"] = package.get("filePath")
        new_package["fixedinversion"] = package.get("fixedInVersion")
        new_package["sourcelayerhash"] = package.get("sourceLayerHash")
        new_package["awsaccount"] = aws_account_id
        new_package["findingarn"] = finding_arn

        packages[new_package["id"]] = new_package

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
    region: str,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AWSInspectorPackageSchema(),
        packages,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running AWS Inspector cleanup")
    GraphJob.from_node_schema(AWSInspectorFindingSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AWSInspectorPackageSchema(), common_job_parameters).run(
        neo4j_session,
    )


def _sync_findings_for_account(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    account_id: str,
    update_tag: int,
    current_aws_account_id: str,
) -> None:
    """
    Syncs the findings for a given account in a given region.
    """
    findings = get_inspector_findings(boto3_session, region, account_id)
    if not findings:
        logger.info(f"No findings to sync for account {account_id} in region {region}")
        return
    for f_batch in findings:
        finding_data, package_data = transform_inspector_findings(f_batch)
        logger.info(f"Loading {len(finding_data)} findings from account {account_id}")
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
            region,
            update_tag,
            current_aws_account_id,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
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

        async def async_ingest_findings_for_account(account_id: str) -> None:
            await to_asynchronous(
                _sync_findings_for_account,
                neo4j_session,
                boto3_session,
                region,
                account_id,
                update_tag,
                current_aws_account_id,
            )

        to_synchronous(
            *[
                async_ingest_findings_for_account(account_id)
                for account_id in member_accounts
            ]
        )

    cleanup(neo4j_session, common_job_parameters)
