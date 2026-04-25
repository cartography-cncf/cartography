import logging
from typing import Dict
from typing import List
from typing import Set

import boto3
import neo4j

from cartography.intel.aws.sagemaker.domains import sync_domains
from cartography.intel.aws.sagemaker.endpoint_configs import sync_endpoint_configs
from cartography.intel.aws.sagemaker.endpoints import sync_endpoints
from cartography.intel.aws.sagemaker.model_package_groups import (
    sync_model_package_groups,
)
from cartography.intel.aws.sagemaker.model_packages import sync_model_packages
from cartography.intel.aws.sagemaker.models import sync_models
from cartography.intel.aws.sagemaker.notebook_instances import sync_notebook_instances
from cartography.intel.aws.sagemaker.training_jobs import sync_training_jobs
from cartography.intel.aws.sagemaker.transform_jobs import sync_transform_jobs
from cartography.intel.aws.sagemaker.user_profiles import sync_user_profiles
from cartography.intel.aws.util.service_regions import (
    filter_regions_to_supported_service_regions,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync all SageMaker resources for the given AWS account and regions.

    :param neo4j_session: Neo4j session
    :param boto3_session: boto3 session
    :param regions: List of AWS regions to sync
    :param current_aws_account_id: AWS account ID
    :param update_tag: Timestamp for tracking updates
    :param common_job_parameters: Common job parameters for cleanup
    """
    logger.info(
        "Syncing SageMaker for account '%s'.",
        current_aws_account_id,
    )

    sagemaker_regions, unsupported_regions = (
        filter_regions_to_supported_service_regions(
            boto3_session,
            "sagemaker",
            regions,
        )
    )
    if unsupported_regions:
        logger.info(
            "Skipping SageMaker sync for account '%s' in unsupported regions: %s",
            current_aws_account_id,
            ", ".join(unsupported_regions),
        )

    skip_regions: Set[str] = set()
    submodule_syncs = [
        sync_notebook_instances,
        sync_domains,
        sync_user_profiles,
        sync_training_jobs,
        sync_models,
        sync_endpoint_configs,
        sync_endpoints,
        sync_transform_jobs,
        sync_model_package_groups,
        sync_model_packages,
    ]

    for sync_submodule in submodule_syncs:
        newly_failed_regions = sync_submodule(
            neo4j_session,
            boto3_session,
            sagemaker_regions,
            current_aws_account_id,
            update_tag,
            common_job_parameters,
            skip_regions,
        )
        skip_regions.update(newly_failed_regions)
