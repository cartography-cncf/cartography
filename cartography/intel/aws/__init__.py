import datetime
import logging
import os
import traceback
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping

import aioboto3
import boto3
import botocore.exceptions
import neo4j

from cartography.analysis.aws.analysis import AWS_EC2_ASSET_EXPOSURE_JOBS
from cartography.analysis.aws.analysis import AWS_EC2_IAM_INSTANCE_PROFILE
from cartography.analysis.aws.analysis import AWS_EC2_KEYPAIR_ANALYSIS_JOBS
from cartography.analysis.aws.analysis import AWS_ECS_ASSET_EXPOSURE
from cartography.analysis.aws.analysis import AWS_EKS_ASSET_EXPOSURE
from cartography.analysis.aws.analysis import AWS_FOREIGN_ACCOUNTS
from cartography.analysis.aws.analysis import AWS_LAMBDA_ECR
from cartography.analysis.aws.analysis import AWS_LB_CONTAINER_EXPOSURE
from cartography.analysis.aws.analysis import AWS_LB_NACL_DIRECT
from cartography.config import Config
from cartography.intel.aws.label_migrations import migrate_legacy_aws_labels
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.common import parse_and_validate_aws_account_ids
from cartography.intel.aws.util.common import parse_and_validate_aws_regions
from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_analysis_and_ensure_deps
from cartography.util import run_cleanup_job
from cartography.util import run_typed_analysis_and_ensure_deps
from cartography.util import run_typed_analysis_job
from cartography.util import timeit

from . import ec2
from . import organizations
from . import ssm as ssm_intel
from .resources import RESOURCE_FUNCTIONS

stat_handler = get_stats_client(__name__)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AWSOrganizationDiscoveryCandidate:
    profile_name: str
    account_id: str
    organization_id: str | None = None
    management_account_id: str | None = None
    result: organizations.AWSOrganizationSyncResult | None = None


# DEPRECATED: this is for backward compatibility, will be removed in v1.0.0
def _normalize_requested_syncs(aws_requested_syncs: Iterable[str]) -> list[str]:
    """
    Auto-include dependent sync phases for backward compatibility.
    E.g., requesting 'ec2:load_balancer_v2' alone will auto-include 'ec2:load_balancer_v2:expose'.
    """
    # Preserve order + dedupe
    requested_syncs = list(dict.fromkeys(aws_requested_syncs))
    requested_syncs_set = set(requested_syncs)

    if (
        "ec2:load_balancer_v2" in requested_syncs_set
        and "ec2:load_balancer_v2:expose" not in requested_syncs_set
    ):
        requested_syncs.append("ec2:load_balancer_v2:expose")
        logger.info(
            "Auto-including 'ec2:load_balancer_v2:expose' because "
            "'ec2:load_balancer_v2' was requested.",
        )

    return requested_syncs


def _build_aws_sync_kwargs(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "neo4j_session": neo4j_session,
        "boto3_session": boto3_session,
        "regions": regions,
        "current_aws_account_id": current_aws_account_id,
        "update_tag": sync_tag,
        "common_job_parameters": common_job_parameters,
    }


def _sync_one_account(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: list[str] | None = None,
    aws_requested_syncs: Iterable[str] = RESOURCE_FUNCTIONS.keys(),
    aioboto3_session: aioboto3.Session | None = None,
) -> None:
    if aioboto3_session is None:
        aioboto3_session = aioboto3.Session()

    migrate_legacy_aws_labels(neo4j_session, current_aws_account_id)

    # Autodiscover the regions supported by the account unless the user has specified the regions to sync.
    if not regions:
        regions = _autodiscover_account_regions(boto3_session, current_aws_account_id)

    sync_args = _build_aws_sync_kwargs(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    aws_requested_syncs = _normalize_requested_syncs(aws_requested_syncs)

    # Validate that all requested syncs exist
    requested_syncs_set = set(aws_requested_syncs)
    invalid_syncs = requested_syncs_set - set(RESOURCE_FUNCTIONS.keys())
    if invalid_syncs:
        raise ValueError(
            f"AWS sync function(s) {invalid_syncs} were specified but do not exist. Did you misspell them?",
        )

    # Warn if modules are requested without their dependencies
    # Dependencies: {module: [required_dependencies]}
    module_dependencies = {
        "ssm": ["ec2:instance"],
        "ec2:images": ["ec2:instance"],
        "ec2:load_balancer": ["ec2:subnet", "ec2:instance"],
        "ec2:load_balancer_v2": ["ec2:subnet", "ec2:instance"],
        "ec2:load_balancer_v2:expose": [
            "ec2:load_balancer_v2",
            "ec2:network_interface",
        ],
        "ec2:route_table": ["ec2:vpc_endpoint"],
        # `ecs` creates IS_INSTANCE rels (AWSECSContainerInstance→AWSEC2Instance) and
        # TARGETS matchlinks (AWSELBV2TargetGroup→AWSECSService)
        "ecs": ["ec2:instance", "ec2:load_balancer_v2"],
        "dynamodb": ["kms"],
        # s3/rds/efs create canonical (:...)-[:ENCRYPTED_BY]->(:AWSKMSKey) edges by
        # matching existing AWSKMSKey nodes on their ARN, so kms must sync first.
        "s3": ["kms"],
        "rds": ["kms"],
        "efs": ["kms"],
    }
    for module, dependencies in module_dependencies.items():
        if module in requested_syncs_set:
            missing_deps = [
                dep for dep in dependencies if dep not in requested_syncs_set
            ]
            if missing_deps:
                logger.warning(
                    f"Module '{module}' is requested without its dependencies {missing_deps}. "
                    f"Some relationships may not be created if the dependency data doesn't exist in Neo4j.",
                )

    # Iterate over RESOURCE_FUNCTIONS to preserve defined sync order (dependencies)
    # Skip modules not in the user's requested list
    for func_name in RESOURCE_FUNCTIONS:
        if func_name not in requested_syncs_set:
            continue
        # Skip permission relationships and tags for now because they rely on data already being in the graph
        if func_name == "ecr:image_layers":
            # has a different signature than the other functions (aioboto3_session replaces boto3_session)
            RESOURCE_FUNCTIONS[func_name](
                neo4j_session,
                aioboto3_session,
                regions,
                current_aws_account_id,
                update_tag,
                common_job_parameters,
            )
        elif func_name in ["permission_relationships", "resourcegroupstaggingapi"]:
            continue
        else:
            RESOURCE_FUNCTIONS[func_name](**sync_args)

    # MAP IAM permissions
    if "permission_relationships" in aws_requested_syncs:
        RESOURCE_FUNCTIONS["permission_relationships"](**sync_args)

    # AWS Tags - Must always be last.
    if "resourcegroupstaggingapi" in aws_requested_syncs:
        RESOURCE_FUNCTIONS["resourcegroupstaggingapi"](**sync_args)

    run_typed_analysis_job(
        AWS_EC2_IAM_INSTANCE_PROFILE,
        neo4j_session,
        common_job_parameters,
    )

    run_typed_analysis_job(
        AWS_LAMBDA_ECR,
        neo4j_session,
        common_job_parameters,
    )

    if {"ecs", "ec2:load_balancer_v2", "ec2:load_balancer_v2:expose"}.issubset(
        requested_syncs_set
    ):
        run_typed_analysis_job(
            AWS_LB_CONTAINER_EXPOSURE,
            neo4j_session,
            common_job_parameters,
        )

    if {"ec2:network_acls", "ec2:load_balancer_v2"}.issubset(requested_syncs_set):
        run_typed_analysis_job(
            AWS_LB_NACL_DIRECT,
            neo4j_session,
            common_job_parameters,
        )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="AWSAccount",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )


def _autodiscover_account_regions(
    boto3_session: boto3.Session,
    account_id: str,
) -> List[str]:
    regions: List[str] = []
    try:
        regions = ec2.get_ec2_regions(boto3_session)
    except botocore.exceptions.ClientError as e:
        logger.debug("Error occurred getting EC2 regions.", exc_info=True)
        logger.error(
            (
                "Failed to retrieve AWS region list, an error occurred: %s. Could not get regions for account %s."
            ),
            e,
            account_id,
        )
        raise
    return regions


def _resolve_aws_ssm_public_parameter_prefix_allowlist(
    config_value: str | None,
    env_value: str | None,
) -> str:
    if config_value is not None:
        return config_value
    if env_value is not None:
        return env_value
    return ssm_intel.DEFAULT_PUBLIC_PARAMETER_PREFIX_ALLOWLIST


def _get_boto3_session_for_profile(
    default_boto3_session: boto3.Session,
    profile_name: str | None,
) -> boto3.Session:
    if profile_name in {None, "default"}:
        return default_boto3_session
    return boto3.Session(profile_name=profile_name)


def _sync_shared_public_ssm_parameters(
    neo4j_session: neo4j.Session,
    default_boto3_session: boto3.Session,
    aws_accounts: Mapping[str, str],
    requested_syncs: List[str],
    common_job_parameters: Dict[str, Any],
    configured_regions: list[str] | None,
    aws_best_effort_mode: bool,
) -> None:
    if "ssm" not in requested_syncs:
        return

    region_session_candidates: dict[str, list[boto3.Session]] = {}
    all_profiles_prepared = True
    for profile_name, account_id in aws_accounts.items():
        try:
            boto3_session = _get_boto3_session_for_profile(
                default_boto3_session,
                profile_name,
            )
            profile_regions = configured_regions or _autodiscover_account_regions(
                boto3_session,
                account_id,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError):
            if not aws_best_effort_mode:
                raise
            logger.warning(
                "Unable to prepare an AWS profile for shared public SSM parameter sync; continuing because aws-best-effort-mode is on.",
                exc_info=True,
            )
            all_profiles_prepared = False
            continue

        for region in profile_regions:
            region_session_candidates.setdefault(region, []).append(boto3_session)

    ssm_intel.sync_public_parameters(
        neo4j_session,
        region_session_candidates,
        common_job_parameters["UPDATE_TAG"],
        common_job_parameters,
        cleanup_allowed=all_profiles_prepared,
    )


def _sync_aws_organization_for_account(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    account_id: str,
    sync_tag: int,
    common_job_parameters: Dict,
) -> organizations.AWSOrganizationSyncResult:
    logger.info("Trying to sync AWS Organizations hierarchy.")
    try:
        client = create_boto3_client(boto3_session, "organizations")
        return organizations.sync_aws_organization(
            neo4j_session,
            client,
            account_id,
            sync_tag,
            common_job_parameters,
        )
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "AWSOrganizationsNotInUseException":
            logger.info(
                "The current account (%s) is not a member of an AWS Organization.",
                account_id,
            )
            return organizations.AWSOrganizationSyncResult(
                account_id,
                organizations.AWSOrganizationSyncStatus.NOT_IN_ORG,
                error_code=error_code,
            )
        logger.warning(
            "The current account (%s) doesn't have enough permissions to sync AWS Organizations hierarchy. "
            "AWS Organizations error code: %s.",
            account_id,
            error_code,
            exc_info=True,
        )
        status = (
            organizations.AWSOrganizationSyncStatus.ACCESS_DENIED
            if error_code in {"AccessDenied", "AccessDeniedException"}
            else organizations.AWSOrganizationSyncStatus.INCOMPLETE
        )
        return organizations.AWSOrganizationSyncResult(
            account_id,
            status,
            error_code=error_code,
        )


def _discover_aws_organization_candidate(
    profile_name: str,
    account_id: str,
    use_explicit_profile: bool,
) -> AWSOrganizationDiscoveryCandidate:
    session_kwargs = {"profile_name": profile_name} if use_explicit_profile else {}
    boto3_session = boto3.Session(**session_kwargs)
    try:
        client = create_boto3_client(boto3_session, "organizations")
        response = client.describe_organization()
        organization = response["Organization"]
    except botocore.exceptions.ClientError as e:
        result = organizations.get_aws_organization_sync_result_from_client_error(
            account_id,
            e,
        )
        if result.status == organizations.AWSOrganizationSyncStatus.NOT_IN_ORG:
            logger.info(
                "The current account (%s) is not a member of an AWS Organization.",
                account_id,
            )
        elif result.status == organizations.AWSOrganizationSyncStatus.ACCESS_DENIED:
            logger.warning(
                "The current account (%s) doesn't have enough permissions to describe AWS Organizations. "
                "AWS Organizations error code: %s.",
                account_id,
                result.error_code,
                exc_info=True,
            )
        else:
            logger.warning(
                "Unable to describe AWS Organization for account %s. AWS Organizations error code: %s.",
                account_id,
                result.error_code,
                exc_info=True,
            )
        return AWSOrganizationDiscoveryCandidate(
            profile_name,
            account_id,
            result=result,
        )
    return AWSOrganizationDiscoveryCandidate(
        profile_name,
        account_id,
        organization_id=organization["Id"],
        management_account_id=organization.get("MasterAccountId"),
    )


def _discover_aws_organization_candidates(
    accounts: Dict[str, str],
    use_explicit_profile: bool,
) -> list[AWSOrganizationDiscoveryCandidate]:
    account_items = list(accounts.items())
    if not use_explicit_profile and len(account_items) > 1:
        logger.warning(
            "AWS Organizations discovery is using the default AWS session, so only the first configured AWS account "
            "(%s) will be probed. Use --aws-sync-all-profiles to probe multiple configured profiles.",
            account_items[0][1],
        )
    if not use_explicit_profile:
        account_items = account_items[:1]
    if not account_items:
        return []

    return [
        _discover_aws_organization_candidate(
            profile_name,
            account_id,
            use_explicit_profile,
        )
        for profile_name, account_id in account_items
    ]


def _group_aws_organization_candidates(
    candidates: Iterable[AWSOrganizationDiscoveryCandidate],
) -> tuple[
    list[organizations.AWSOrganizationSyncResult],
    dict[str, list[AWSOrganizationDiscoveryCandidate]],
]:
    results: list[organizations.AWSOrganizationSyncResult] = []
    candidates_by_organization: dict[str, list[AWSOrganizationDiscoveryCandidate]] = {}
    for candidate in candidates:
        if candidate.result is not None:
            results.append(candidate.result)
            continue
        if candidate.organization_id is None:
            continue
        candidates_by_organization.setdefault(candidate.organization_id, []).append(
            candidate,
        )
    return results, candidates_by_organization


def _sync_aws_organization_candidate_groups(
    neo4j_session: neo4j.Session,
    candidates_by_organization: dict[str, list[AWSOrganizationDiscoveryCandidate]],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
    use_explicit_profile: bool,
) -> list[organizations.AWSOrganizationSyncResult]:
    results: list[organizations.AWSOrganizationSyncResult] = []
    for organization_id, organization_candidates in candidates_by_organization.items():
        organization_candidates.sort(
            key=lambda candidate: (
                candidate.account_id != candidate.management_account_id,
            ),
        )
        for candidate in organization_candidates:
            session_kwargs = (
                {"profile_name": candidate.profile_name} if use_explicit_profile else {}
            )
            boto3_session = boto3.Session(**session_kwargs)
            result = _sync_aws_organization_for_account(
                neo4j_session,
                boto3_session,
                candidate.account_id,
                sync_tag,
                common_job_parameters,
            )
            results.append(result)
            if result.status in {
                organizations.AWSOrganizationSyncStatus.SYNCED,
                organizations.AWSOrganizationSyncStatus.ALREADY_SYNCED,
            }:
                break
        else:
            logger.warning(
                "Unable to find an account with access to enumerate AWS Organization %s.",
                organization_id,
            )
    return results


def _sync_explicit_aws_organization_accounts(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, str],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
    organization_account_ids: Iterable[str],
    use_explicit_profile: bool = False,
) -> list[organizations.AWSOrganizationSyncResult]:
    account_ids = set(organization_account_ids)
    candidate_accounts = {
        profile_name: account_id
        for profile_name, account_id in accounts.items()
        if account_id in account_ids
    }
    candidates = _discover_aws_organization_candidates(
        candidate_accounts,
        use_explicit_profile,
    )
    results, candidates_by_organization = _group_aws_organization_candidates(
        candidates,
    )
    results.extend(
        _sync_aws_organization_candidate_groups(
            neo4j_session,
            candidates_by_organization,
            sync_tag,
            common_job_parameters,
            use_explicit_profile,
        )
    )

    missing_account_ids = account_ids - set(accounts.values())
    if missing_account_ids:
        logger.warning(
            "AWS Organizations sync candidate account IDs are not in the AWS sync account list: %s.",
            ", ".join(sorted(missing_account_ids)),
        )

    return results


def _sync_aws_organizations_for_accounts(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, str],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
    organization_account_ids: Iterable[str] | None = None,
    use_explicit_profile: bool = False,
) -> list[organizations.AWSOrganizationSyncResult]:
    """
    Discover AWS Organizations before per-account resource sync.

    This keeps standard Cartography's sequential CLI/library flow compatible while
    giving external orchestrators a single phase they can call before parallel
    account fanout.
    """
    if organization_account_ids is not None:
        return _sync_explicit_aws_organization_accounts(
            neo4j_session,
            accounts,
            sync_tag,
            common_job_parameters,
            organization_account_ids,
            use_explicit_profile=use_explicit_profile,
        )

    results: list[organizations.AWSOrganizationSyncResult] = []
    candidates = _discover_aws_organization_candidates(accounts, use_explicit_profile)
    discovery_results, candidates_by_organization = _group_aws_organization_candidates(
        candidates,
    )
    results.extend(discovery_results)
    results.extend(
        _sync_aws_organization_candidate_groups(
            neo4j_session,
            candidates_by_organization,
            sync_tag,
            common_job_parameters,
            use_explicit_profile,
        )
    )

    return results


def _sync_multiple_accounts(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, str],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
    aws_best_effort_mode: bool,
    aws_requested_syncs: List[str] = [],
    regions: list[str] | None = None,
    organization_account_ids: Iterable[str] | None = None,
    use_explicit_profile: bool = False,
) -> bool:
    logger.info("Syncing AWS accounts: %s", ", ".join(accounts.values()))
    organizations.sync(neo4j_session, accounts, sync_tag, common_job_parameters)
    _sync_aws_organizations_for_accounts(
        neo4j_session,
        accounts,
        sync_tag,
        common_job_parameters,
        organization_account_ids=organization_account_ids,
        use_explicit_profile=use_explicit_profile,
    )

    failed_account_ids = []
    exception_tracebacks = []

    for profile_name, account_id in accounts.items():
        logger.info(
            "Syncing AWS account with ID '%s' using configured profile '%s'.",
            account_id,
            profile_name,
        )
        common_job_parameters["AWS_ID"] = account_id
        # When use_explicit_profile is set, honor configured profiles (hub/spoke STS assume-role configs, #1142/#1185).
        # Otherwise fall back to the default session so env-var-only credentials keep working when ~/.aws/config is absent (#1042).
        session_kwargs = {"profile_name": profile_name} if use_explicit_profile else {}
        boto3_session = boto3.Session(**session_kwargs)
        aioboto3_session = aioboto3.Session(**session_kwargs)

        try:
            _sync_one_account(
                neo4j_session,
                boto3_session,
                account_id,
                sync_tag,
                common_job_parameters,
                regions=regions,
                aws_requested_syncs=aws_requested_syncs,  # Could be replaced later with per-account requested syncs
                aioboto3_session=aioboto3_session,
            )
        except Exception as e:
            if aws_best_effort_mode:
                timestamp = datetime.datetime.now()
                failed_account_ids.append(account_id)
                exception_traceback = traceback.TracebackException.from_exception(e)
                traceback_string = "".join(exception_traceback.format())
                exception_tracebacks.append(
                    f"{timestamp} - Exception for account ID: {account_id}\n{traceback_string}",
                )
                logger.warning(
                    f"Caught exception syncing account {account_id}. aws-best-effort-mode is on so we are continuing "
                    f"on to the next AWS account. All exceptions will be aggregated and re-logged at the end of the "
                    f"sync.",
                    exc_info=True,
                )
                continue
            else:
                raise

    if failed_account_ids:
        logger.error(f"AWS sync failed for accounts {failed_account_ids}")
        raise Exception("\n".join(exception_tracebacks))

    del common_job_parameters["AWS_ID"]

    # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # up those nodes after all AWS accounts have been synced.
    if not failed_account_ids:
        run_cleanup_job(
            "aws_post_ingestion_principals_cleanup.json",
            neo4j_session,
            common_job_parameters,
        )
        return True
    return False


@timeit
def _perform_aws_analysis(
    requested_syncs: List[str],
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs AWS analysis jobs that span multiple accounts.
    """
    requested_syncs_as_set = set(requested_syncs)

    run_analysis_and_ensure_deps(
        "aws_ip_node_label_migration.json",
        {"ec2:security_group"},
        requested_syncs_as_set,
        common_job_parameters,
        neo4j_session,
    )

    for job in AWS_EC2_ASSET_EXPOSURE_JOBS:
        run_typed_analysis_and_ensure_deps(
            job,
            {
                "ec2:instance",
                "ec2:security_group",
                "ec2:load_balancer",
                "ec2:load_balancer_v2",
            },
            requested_syncs_as_set,
            common_job_parameters,
            neo4j_session,
        )

    for job in AWS_EC2_KEYPAIR_ANALYSIS_JOBS:
        run_typed_analysis_and_ensure_deps(
            job,
            {"ec2:keypair"},
            requested_syncs_as_set,
            common_job_parameters,
            neo4j_session,
        )

    run_typed_analysis_and_ensure_deps(
        AWS_EKS_ASSET_EXPOSURE,
        {"eks"},
        requested_syncs_as_set,
        common_job_parameters,
        neo4j_session,
    )

    run_typed_analysis_and_ensure_deps(
        AWS_FOREIGN_ACCOUNTS,
        set(),  # This job has no requirements
        requested_syncs_as_set,
        common_job_parameters,
        neo4j_session,
    )

    run_typed_analysis_and_ensure_deps(
        AWS_ECS_ASSET_EXPOSURE,
        {"ecs", "ec2:load_balancer_v2", "ec2:load_balancer_v2:expose"},
        requested_syncs_as_set,
        common_job_parameters,
        neo4j_session,
    )


@timeit
def start_aws_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    aws_ssm_public_parameter_prefix_allowlist = (
        _resolve_aws_ssm_public_parameter_prefix_allowlist(
            config.aws_ssm_public_parameter_prefix_allowlist,
            os.getenv("AWS_SSM_PUBLIC_PARAMETER_PREFIX_ALLOWLIST"),
        )
    )
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
        "aws_guardduty_severity_threshold": config.aws_guardduty_severity_threshold,
        "aws_cloudtrail_management_events_lookback_hours": config.aws_cloudtrail_management_events_lookback_hours,
        "experimental_aws_inspector_batch": config.experimental_aws_inspector_batch,
        "aws_tagging_api_cleanup_batch": config.aws_tagging_api_cleanup_batch,
        "aws_ssm_public_parameter_prefix_allowlist": aws_ssm_public_parameter_prefix_allowlist,
    }
    try:
        boto3_session = boto3.Session()
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug("Error occurred calling boto3.Session().", exc_info=True)
        logger.error(
            (
                "Unable to initialize the default AWS session, an error occurred: %s. Make sure your AWS credentials "
                "are configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return

    if config.aws_sync_all_profiles:
        aws_accounts = organizations.get_aws_accounts_from_botocore_config(
            boto3_session,
        )
    else:
        aws_accounts = organizations.get_aws_account_default(boto3_session)

    if not aws_accounts:
        logger.warning(
            "No valid AWS credentials could be found. No AWS accounts can be synced. Exiting AWS sync stage.",
        )
        return
    if len(list(aws_accounts.values())) != len(set(aws_accounts.values())):
        logger.warning(
            (
                "There are duplicate AWS accounts in your AWS configuration. It is strongly recommended that you run "
                "cartography with an AWS configuration which has exactly one profile for each AWS account you want to "
                f"sync. Doing otherwise will result in undefined and untested behavior. Account list: {aws_accounts}"
            ),
        )

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.aws_requested_syncs:
        requested_syncs = parse_and_validate_aws_requested_syncs(
            config.aws_requested_syncs,
        )
    requested_syncs = _normalize_requested_syncs(requested_syncs)

    if config.aws_regions:
        regions = parse_and_validate_aws_regions(config.aws_regions)
    else:
        regions = None
    if config.aws_organization_account_ids:
        organization_account_ids = parse_and_validate_aws_account_ids(
            config.aws_organization_account_ids,
        )
    else:
        organization_account_ids = None

    sync_successful = _sync_multiple_accounts(
        neo4j_session,
        aws_accounts,
        config.update_tag,
        common_job_parameters,
        config.aws_best_effort_mode,
        requested_syncs,
        regions=regions,
        organization_account_ids=organization_account_ids,
        # Today this flag mirrors aws_sync_all_profiles 1:1; it's named separately so _sync_multiple_accounts
        # stays decoupled from the CLI option should the two ever diverge.
        use_explicit_profile=config.aws_sync_all_profiles,
    )

    if sync_successful:
        _sync_shared_public_ssm_parameters(
            neo4j_session,
            boto3_session,
            aws_accounts,
            requested_syncs,
            common_job_parameters,
            regions,
            config.aws_best_effort_mode,
        )
        _perform_aws_analysis(requested_syncs, neo4j_session, common_job_parameters)
