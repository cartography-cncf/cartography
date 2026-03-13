import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ses import SESEmailIdentitySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ses_email_identities(
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "sesv2",
        region_name=region,
        config=get_botocore_config(),
    )
    identities: List[Dict[str, Any]] = []
    paginator = client.get_paginator("list_email_identities")
    for page in paginator.paginate():
        for identity_info in page.get("EmailIdentities", []):
            identity_name = identity_info["IdentityName"]
            identity_type = identity_info["IdentityType"]
            sending_enabled = identity_info.get("SendingEnabled", False)
            identity_detail = _get_ses_email_identity_detail(
                client,
                identity_name,
            )
            if identity_detail is None:
                continue
            dkim_attrs = identity_detail.get("DkimAttributes", {})
            arn = (
                f"arn:aws:ses:{region}:{current_aws_account_id}"
                f":identity/{identity_name}"
            )
            identities.append(
                {
                    "Arn": arn,
                    "IdentityName": identity_name,
                    "IdentityType": identity_type,
                    "SendingEnabled": sending_enabled,
                    "VerificationStatus": identity_detail.get(
                        "VerificationStatus",
                    ),
                    "DkimSigningEnabled": dkim_attrs.get(
                        "SigningEnabled",
                        False,
                    ),
                    "DkimStatus": dkim_attrs.get("Status"),
                }
            )
    return identities


def _get_ses_email_identity_detail(
    client: Any,
    identity_name: str,
) -> Optional[Dict[str, Any]]:
    try:
        return client.get_email_identity(EmailIdentity=identity_name)
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NotFoundException":
            logger.warning(
                "SESv2 get_email_identity returned NotFoundException. "
                "The identity may have been deleted after listing. Skipping.",
            )
            return None
        raise


@timeit
def load_ses_email_identities(
    neo4j_session: neo4j.Session,
    identity_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d SES email identities for region '%s' into graph.",
        len(identity_data),
        region,
    )
    load(
        neo4j_session,
        SESEmailIdentitySchema(),
        identity_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running SES cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        SESEmailIdentitySchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing SES for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        identities = get_ses_email_identities(
            boto3_session,
            region,
            current_aws_account_id,
        )
        load_ses_email_identities(
            neo4j_session,
            identities,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
