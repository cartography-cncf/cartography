import logging

import neo4j

from cartography.config import Config
from cartography.intel.tencentcloud import account
from cartography.intel.tencentcloud import cam
from cartography.intel.tencentcloud import cbs
from cartography.intel.tencentcloud import clb
from cartography.intel.tencentcloud import cos
from cartography.intel.tencentcloud import cvm
from cartography.intel.tencentcloud import vpc
from cartography.intel.tencentcloud.util import build_credential
from cartography.intel.tencentcloud.util import get_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_tencentcloud_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Ingest the Tencent Cloud account that owns the configured API key."""
    if not config.tencentcloud_secret_id or not config.tencentcloud_secret_key:
        logger.info(
            "Tencent Cloud import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    credential = build_credential(
        config.tencentcloud_secret_id,
        config.tencentcloud_secret_key,
    )

    tencent_account = account.sync(neo4j_session, credential, config.update_tag)
    account_id = tencent_account["id"]
    regions = config.tencentcloud_regions or get_regions(credential)
    logger.info(
        "Syncing Tencent Cloud account %s across %d regions.",
        account_id,
        len(regions),
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ACCOUNT_ID": account_id,
    }

    # CAM first: CVM instances link to the CAM roles bound to them.
    cam.sync(
        neo4j_session,
        credential,
        account_id,
        config.update_tag,
        common_job_parameters,
    )
    # Networks before compute so instances and load balancers find their VPC, subnet,
    # and security groups.
    vpc.sync(
        neo4j_session,
        credential,
        account_id,
        regions,
        config.update_tag,
        common_job_parameters,
    )
    cvm.sync(
        neo4j_session,
        credential,
        account_id,
        regions,
        config.update_tag,
        common_job_parameters,
    )
    # Disks and load balancers after instances so ATTACHED_TO and EXPOSE edges resolve.
    cbs.sync(
        neo4j_session,
        credential,
        account_id,
        regions,
        config.update_tag,
        common_job_parameters,
    )
    clb.sync(
        neo4j_session,
        credential,
        account_id,
        regions,
        config.update_tag,
        common_job_parameters,
    )
    cos.sync(
        neo4j_session,
        credential,
        account_id,
        config.update_tag,
        common_job_parameters,
    )
