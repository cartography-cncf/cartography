import logging

import neo4j
import requests

from cartography.config import Config
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
boto3 = lazy_import("boto3")
get_spacelift_token = lazy_callable(
    "cartography.intel.spacelift.util", "get_spacelift_token"
)
sync_account = lazy_callable("cartography.intel.spacelift.account", "sync_account")
sync_ec2_ownership = lazy_callable(
    "cartography.intel.spacelift.ec2_ownership", "sync_ec2_ownership"
)
sync_runs = lazy_callable("cartography.intel.spacelift.runs", "sync_runs")
sync_spaces = lazy_callable("cartography.intel.spacelift.spaces", "sync_spaces")
sync_stacks = lazy_callable("cartography.intel.spacelift.stacks", "sync_stacks")
sync_worker_pools = lazy_callable(
    "cartography.intel.spacelift.workerpools", "sync_worker_pools"
)
sync_workers = lazy_callable("cartography.intel.spacelift.workers", "sync_workers")

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_spacelift_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of Spacelift data.
    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    # Validate configuration
    if not config.spacelift_api_endpoint:
        logger.info("Spacelift API endpoint not configured - skipping this module.")
        return

    # Determine authentication method and obtain token
    token = None
    if config.spacelift_api_token:
        # Method 1: Use provided token directly
        logger.info("Using provided Spacelift API token for authentication")
        token = config.spacelift_api_token
    elif config.spacelift_api_key_id and config.spacelift_api_key_secret:
        # Method 2: Exchange API key ID and secret for a token
        logger.info("Exchanging Spacelift API key for authentication token")
        try:
            token = get_spacelift_token(
                config.spacelift_api_endpoint,
                config.spacelift_api_key_id,
                config.spacelift_api_key_secret,
            )
        except Exception as e:
            logger.error(f"Failed to obtain Spacelift authentication token: {e}")
            logger.info("Skipping Spacelift module due to authentication failure.")
            return
    else:
        logger.info(
            "Spacelift authentication not configured. "
            "Provide either --spacelift-api-token-env-var or both "
            "--spacelift-api-key-id-env-var and --spacelift-api-key-secret-env-var. "
            "Skipping this module."
        )
        return

    logger.info("Starting Spacelift ingestion")

    # Set up common job parameters
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Create authenticated session for Spacelift API
    spacelift_session = requests.Session()
    spacelift_session.headers.update(
        {
            "Authorization": f"Bearer {token}",
        }
    )

    account_id = sync_account(
        neo4j_session,
        config.spacelift_api_endpoint,
        common_job_parameters,
    )

    common_job_parameters["spacelift_account_id"] = account_id

    sync_spaces(
        neo4j_session,
        spacelift_session,
        config.spacelift_api_endpoint,
        account_id,
        common_job_parameters,
    )

    sync_stacks(
        neo4j_session,
        spacelift_session,
        config.spacelift_api_endpoint,
        account_id,
        common_job_parameters,
    )

    sync_worker_pools(
        neo4j_session,
        spacelift_session,
        config.spacelift_api_endpoint,
        account_id,
        common_job_parameters,
    )

    sync_workers(
        neo4j_session,
        spacelift_session,
        config.spacelift_api_endpoint,
        account_id,
        common_job_parameters,
    )

    # Note: Users are synced as part of runs sync (derived from run.triggeredBy)
    sync_runs(
        neo4j_session,
        spacelift_session,
        config.spacelift_api_endpoint,
        account_id,
        common_job_parameters,
    )

    # Sync EC2 ownership relationships from CloudTrail data (optional)
    if all(
        hasattr(config, attr)
        for attr in [
            "spacelift_ec2_ownership_s3_bucket",
            "spacelift_ec2_ownership_s3_prefix",
        ]
    ):
        if hasattr(config, "spacelift_ec2_ownership_aws_profile"):
            aws_session = boto3.Session(
                profile_name=config.spacelift_ec2_ownership_aws_profile
            )
        else:
            aws_session = boto3.Session()
        sync_ec2_ownership(
            neo4j_session,
            aws_session,
            config.spacelift_ec2_ownership_s3_bucket,
            config.spacelift_ec2_ownership_s3_prefix,
            config.update_tag,
            account_id,
        )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="Spacelift",
        group_id=account_id,
        synced_type="SpaceliftData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

    logger.info("Completed Spacelift ingestion")
