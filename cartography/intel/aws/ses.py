import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ses.configuration_set import SESConfigurationSetSchema
from cartography.models.aws.ses.identity import SESIdentitySchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_ses_identities(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get all SES identities (email addresses and domains) for a region.
    """
    client = boto3_session.client("ses", region_name=region)
    response = client.list_identities()
    return response.get("Identities", [])


@timeit
@aws_handle_regions
def get_identity_attributes(
    boto3_session: boto3.session.Session, identities: List[str], region: str
) -> Dict[str, Dict]:
    """
    Get verification and notification attributes for SES identities.
    """
    client = boto3_session.client("ses", region_name=region)
    identity_attributes: Dict[str, Dict] = {}

    if not identities:
        return identity_attributes

    # Get verification attributes
    verification_attrs = client.get_identity_verification_attributes(
        Identities=identities
    )

    # Get notification attributes
    notification_attrs = client.get_identity_notification_attributes(
        Identities=identities
    )

    # Get DKIM attributes
    dkim_attrs = client.get_identity_dkim_attributes(Identities=identities)

    # Combine all attributes
    for identity in identities:
        identity_attributes[identity] = {
            "verification": verification_attrs.get("VerificationAttributes", {}).get(
                identity, {}
            ),
            "notification": notification_attrs.get("NotificationAttributes", {}).get(
                identity, {}
            ),
            "dkim": dkim_attrs.get("DkimAttributes", {}).get(identity, {}),
        }

    return identity_attributes


@timeit
@aws_handle_regions
def get_ses_configuration_sets(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict]:
    """
    Get all SES configuration sets for a region.
    """
    client = boto3_session.client("ses", region_name=region)
    response = client.list_configuration_sets()
    return response.get("ConfigurationSets", [])


def transform_ses_identities(
    identities: List[str],
    identity_attributes: Dict[str, Dict],
    region: str,
    account_id: str,
) -> List[Dict]:
    """
    Transform SES identity data for ingestion
    """
    transformed_identities = []

    for identity in identities:
        attrs = identity_attributes.get(identity, {})
        verification_attrs = attrs.get("verification", {})
        notification_attrs = attrs.get("notification", {})
        dkim_attrs = attrs.get("dkim", {})

        # Determine identity type (email or domain)
        identity_type = "EmailAddress" if "@" in identity else "Domain"

        # Create ARN-like identifier for the identity
        identity_arn = f"carto:ses:identity:{region}:{account_id}:{identity}"

        transformed_identity = {
            "IdentityArn": identity_arn,
            "Identity": identity,
            "IdentityType": identity_type,
            "VerificationStatus": verification_attrs.get("VerificationStatus"),
            # DKIM fields intentionally omitted to avoid storing sensitive tokens
            "BounceTopic": notification_attrs.get("BounceTopic"),
            "ComplaintTopic": notification_attrs.get("ComplaintTopic"),
            "DeliveryTopic": notification_attrs.get("DeliveryTopic"),
            "ForwardingEnabled": notification_attrs.get("ForwardingEnabled"),
            "HeadersInBounceNotificationsEnabled": notification_attrs.get(
                "HeadersInBounceNotificationsEnabled"
            ),
            "HeadersInComplaintNotificationsEnabled": notification_attrs.get(
                "HeadersInComplaintNotificationsEnabled"
            ),
            "HeadersInDeliveryNotificationsEnabled": notification_attrs.get(
                "HeadersInDeliveryNotificationsEnabled"
            ),
        }

        transformed_identities.append(transformed_identity)

    return transformed_identities


def transform_ses_configuration_sets(
    configuration_sets: List[Dict], region: str, account_id: str
) -> List[Dict]:
    """
    Transform SES configuration set data for ingestion
    """
    transformed_sets = []

    for config_set in configuration_sets:
        # Create a non-ARN unique identifier for the configuration set
        config_set_name = config_set.get("Name")
        config_set_id = f"carto:ses:configset:{region}:{account_id}:{config_set_name}"

        transformed_set = {
            "ConfigurationSetId": config_set_id,
            "Name": config_set_name,
        }

        transformed_sets.append(transformed_set)

    return transformed_sets


@timeit
def load_ses_identities(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load SES identities into the graph
    """
    logger.info(f"Loading {len(data)} SES identities for region {region} into graph.")

    load(
        neo4j_session,
        SESIdentitySchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_ses_configuration_sets(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load SES configuration sets into the graph
    """
    logger.info(
        f"Loading {len(data)} SES configuration sets for region {region} into graph."
    )

    load(
        neo4j_session,
        SESConfigurationSetSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_ses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Run SES cleanup job
    """
    logger.debug("Running SES cleanup job.")

    cleanup_job = GraphJob.from_node_schema(SESIdentitySchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        SESConfigurationSetSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


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
    Sync SES identities and configuration sets for all regions
    """
    for region in regions:
        logger.info(f"Syncing SES for {region} in account {current_aws_account_id}")

        # Get and process identities
        identities = get_ses_identities(boto3_session, region)
        identity_attributes = get_identity_attributes(boto3_session, identities, region)
        transformed_identities = transform_ses_identities(
            identities, identity_attributes, region, current_aws_account_id
        )

        load_ses_identities(
            neo4j_session,
            transformed_identities,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Get and process configuration sets
        configuration_sets = get_ses_configuration_sets(boto3_session, region)
        transformed_configuration_sets = transform_ses_configuration_sets(
            configuration_sets, region, current_aws_account_id
        )

        load_ses_configuration_sets(
            neo4j_session,
            transformed_configuration_sets,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Cleanup (outside region loop)
    cleanup_ses(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="SESIdentity",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
