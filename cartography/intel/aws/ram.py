import logging
from functools import wraps
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import backoff
import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ram.principal_association import (
    AWSAccountRAMPrincipalSchema,
)
from cartography.models.aws.ram.principal_association import (
    RAMPrincipalAssociationSchema,
)
from cartography.models.aws.ram.resource_association import RAMResourceAssociationSchema
from cartography.models.aws.ram.resource_share import RAMResourceShareSchema
from cartography.util import AWSGetFunc
from cartography.util import is_aws_region_skippable_client_error
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Only shares owned by the account being synced. Shares owned by others are discovered
# from the owner's own sync, which avoids ingesting the same share once per consumer.
RESOURCE_OWNER = "SELF"


class RAMRegionUnreadable(Exception):
    """Raised when a region's RAM data could not be read at all."""


def ram_handle_regions(func: AWSGetFunc) -> AWSGetFunc:
    """
    Like `aws_handle_regions`, but signals an unreadable region with an exception instead of
    an empty list, so callers can tell "nothing shared here" from "could not look".

    Classification of what counts as a regional failure is delegated to
    `is_aws_region_skippable_client_error`, so this stays in step with the rest of the AWS
    intel modules. Anything else — including credential failures, which are not specific to
    one region — propagates and fails the account sync rather than being downgraded to a
    per-region warning.
    """

    @wraps(func)
    @backoff.on_exception(
        backoff.expo,
        botocore.exceptions.ClientError,
        max_time=600,
    )
    def inner_function(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")
            if error_code == "InvalidToken":
                raise RuntimeError(
                    "AWS returned an InvalidToken error. Configure regional STS endpoints by "
                    "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
                    "'sts_regional_endpoints = regional' to your AWS config file."
                ) from error
            if is_aws_region_skippable_client_error(error):
                raise RAMRegionUnreadable(
                    f"Could not read RAM data: {error_code}"
                ) from error
            raise

    return cast(AWSGetFunc, inner_function)


@timeit
@ram_handle_regions
def get_ram_resource_shares(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "ram", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("get_resource_shares")
    shares: List[Dict[str, Any]] = []
    for page in paginator.paginate(resourceOwner=RESOURCE_OWNER):
        shares.extend(page.get("resourceShares", []))
    return shares


@timeit
@ram_handle_regions
def get_ram_principals(
    boto3_session: boto3.Session, region: str, shares: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    ListPrincipals is scoped to one resource share at a time, so this issues one paginated
    call per share. Accounts with many shares will see a proportional number of API calls.
    """
    client = create_boto3_client(
        boto3_session, "ram", region_name=region, config=get_botocore_config()
    )
    principals: List[Dict[str, Any]] = []
    for share in shares:
        share_arn = share["resourceShareArn"]
        paginator = client.get_paginator("list_principals")
        for page in paginator.paginate(
            resourceOwner=RESOURCE_OWNER, resourceShareArns=[share_arn]
        ):
            for principal in page.get("principals", []):
                principal["resourceShareArn"] = share_arn
                principals.append(principal)
    return principals


@timeit
@ram_handle_regions
def get_ram_resources(
    boto3_session: boto3.Session, region: str, shares: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "ram", region_name=region, config=get_botocore_config()
    )
    resources: List[Dict[str, Any]] = []
    for share in shares:
        share_arn = share["resourceShareArn"]
        paginator = client.get_paginator("list_resources")
        for page in paginator.paginate(
            resourceOwner=RESOURCE_OWNER, resourceShareArns=[share_arn]
        ):
            for resource in page.get("resources", []):
                resource["resourceShareArn"] = share_arn
                resources.append(resource)
    return resources


def transform_ram_principals(
    principals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build a stable synthetic ID per (share, principal) and, when the principal is a bare
    12-digit AWS account ID, expose it separately so it can be matched to an AWSAccount
    node. A principal may instead be an ARN of an organization, OU, IAM role or IAM user,
    in which case no account is matched.
    """
    transformed: List[Dict[str, Any]] = []
    for principal in principals:
        principal_id = principal["id"]
        transformed_principal = dict(principal)
        transformed_principal["Id"] = f"{principal['resourceShareArn']}|{principal_id}"
        transformed_principal["PrincipalAccountId"] = (
            principal_id if principal_id.isdigit() and len(principal_id) == 12 else None
        )
        transformed.append(transformed_principal)
    return transformed


def transform_ram_resources(
    resources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for resource in resources:
        resource_arn = resource["arn"]
        transformed_resource = dict(resource)
        transformed_resource["Id"] = f"{resource['resourceShareArn']}|{resource_arn}"
        transformed.append(transformed_resource)
    return transformed


def get_principal_accounts(
    principals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Principals can be accounts outside the organization, which have no AWSAccount node of
    their own. Emit them so the SHARED_WITH relationship has something to attach to.
    """
    account_ids = {
        principal["PrincipalAccountId"]
        for principal in principals
        if principal["PrincipalAccountId"]
    }
    return [{"id": account_id} for account_id in sorted(account_ids)]


@timeit
def load_ram_resource_shares(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d RAM resource shares for region '%s' into graph.", len(data), region
    )
    load(
        neo4j_session,
        RAMResourceShareSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_ram_principal_accounts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    aws_update_tag: int,
) -> None:
    logger.debug("Loading %d RAM principal AWS accounts into graph.", len(data))
    load(
        neo4j_session,
        AWSAccountRAMPrincipalSchema(),
        data,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ram_principal_associations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d RAM principal associations for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        RAMPrincipalAssociationSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_ram_resource_associations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d RAM resource associations for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        RAMResourceAssociationSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running RAM cleanup job.")
    GraphJob.from_node_schema(
        RAMPrincipalAssociationSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        RAMResourceAssociationSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(RAMResourceShareSchema(), common_job_parameters).run(
        neo4j_session
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
    cleanup_safe = True
    unreadable_regions: List[str] = []

    for region in regions:
        logger.info(
            "Syncing RAM for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        try:
            shares = get_ram_resource_shares(boto3_session, region)
            principals = get_ram_principals(boto3_session, region, shares)
            resources = get_ram_resources(boto3_session, region, shares)
        except RAMRegionUnreadable as error:
            # Keep whatever this region held on a previous run rather than deleting it
            # below because we could not look.
            cleanup_safe = False
            unreadable_regions.append(region)
            logger.warning(
                "Skipping RAM region '%s' for account '%s': %s",
                region,
                current_aws_account_id,
                error,
            )
            continue

        load_ram_resource_shares(
            neo4j_session,
            shares,
            region,
            current_aws_account_id,
            update_tag,
        )

        transformed_principals = transform_ram_principals(principals)
        load_ram_principal_accounts(
            neo4j_session,
            get_principal_accounts(transformed_principals),
            update_tag,
        )
        load_ram_principal_associations(
            neo4j_session,
            transformed_principals,
            region,
            current_aws_account_id,
            update_tag,
        )

        load_ram_resource_associations(
            neo4j_session,
            transform_ram_resources(resources),
            region,
            current_aws_account_id,
            update_tag,
        )

    # Every region failing is not a regional problem: it points at the credentials or at
    # RAM access for the whole account. Fail rather than report an account-wide outage as a
    # series of per-region warnings.
    if regions and len(unreadable_regions) == len(regions):
        raise RuntimeError(
            f"Could not read RAM data in any of the {len(regions)} requested regions for "
            f"account {current_aws_account_id}. This usually means the credentials are "
            f"invalid or lack RAM permissions account-wide."
        )

    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping RAM cleanup for account '%s' because regions %s could not be read. "
            "Preserving last-known-good data.",
            current_aws_account_id,
            ", ".join(unreadable_regions),
        )
