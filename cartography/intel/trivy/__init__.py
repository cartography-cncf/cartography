import logging
import subprocess
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

import cartography.config
from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.intel.trivy.scanner import _call_trivy_update_db
from cartography.intel.trivy.scanner import cleanup
from cartography.intel.trivy.scanner import sync_single_image
from cartography.stats import get_stats_client
from cartography.util import timeit


logger = logging.getLogger(__name__)
stat_handler = get_stats_client('trivy.scanner')


# If we have >= this percentage of Trivy fatal failures, crash the sync. 10 == 10%, 20 == 20%, etc.
TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT = 10


@timeit
def get_scan_targets(neo4j_session: neo4j.Session) -> List[Tuple[str, str, str, str, str]]:
    aws_accounts = list_accounts(neo4j_session)
    ecr_images: List[Tuple[str, str, str, str, str]] = []
    for account_id in aws_accounts:
        ecr_images.extend(get_ecr_images(neo4j_session, account_id))
    return ecr_images


@timeit
def sync_trivy_aws_ecr(
        neo4j_session: neo4j.Session,
        trivy_path: str,
        trivy_opa_policy_file_path: str,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
) -> None:
    trivy_scan_failure_count = 0

    ecr_images = get_scan_targets(neo4j_session)
    num_images = len(ecr_images)
    logger.info(f"Scanning {num_images} ECR images with Trivy")

    for region, image_tag, image_uri, repo_name, image_digest in ecr_images:
        try:
            sync_single_image(
                neo4j_session,
                image_tag,
                image_uri,
                repo_name,
                image_digest,
                update_tag,
                True,
                trivy_path,
                trivy_opa_policy_file_path,
            )
        except subprocess.CalledProcessError as exc:
            trivy_error_msg = exc.output.decode('utf-8') if type(exc.output) == bytes else exc.output
            if 'rego_parse_error' in trivy_error_msg:
                logger.error(
                    'Trivy image scan failed due to rego_parse_error - please check rego syntax! '
                    f"image_uri = {image_uri}, "
                    f"trivy_error_msg = {trivy_error_msg}.",
                )
                raise
            else:
                trivy_scan_failure_count += 1
                logger.warning(
                    "Trivy image scan failed - please investigate. trivy_scan_failure_count++."
                    f"image_uri = {image_uri}"
                    f"trivy_error_msg = {trivy_error_msg}.",
                )
                if (trivy_scan_failure_count / num_images) * 100 >= TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT:
                    logger.error('Trivy scan fatal failure circuit breaker hit, crashing.')
                    raise
                # Else if circuit breaker is not hit, then keep going.
        except KeyError:
            trivy_scan_failure_count += 1
            logger.warning(
                'Trivy image scan failed because it returned unexpectedly incomplete data. '
                'Please repro locally. trivy_scan_failure_count++. '
                f"image_uri = {image_uri}.",
            )
            if (trivy_scan_failure_count / num_images) * 100 >= TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT:
                logger.error('Trivy scan fatal failure circuit breaker hit, crashing.')
                raise
            # Else if circuit breaker is not hit, then keep going.
    cleanup(neo4j_session, common_job_parameters)


@timeit
def start_trivy_scans(neo4j_session: neo4j.Session, config: cartography.config.Config) -> None:
    if not config.trivy_path:
        logger.info("Trivy module not configured. Skipping.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        # TODO we will need to infer the sub resource id based on what resource is being processed
        "AWS_ID": 'id goes here',
    }
    _call_trivy_update_db(config.trivy_path)
    if config.trivy_resource_type == 'aws.ecr':
        sync_trivy_aws_ecr(
            neo4j_session,
            config.trivy_path,
            config.trivy_opa_policy_file_path,
            config.update_tag,
            common_job_parameters,
        )

    # Support other Trivy resource types here e.g. if Google Cloud has images.
