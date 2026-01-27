import asyncio
import hashlib
import json
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.aws.s3.acl import S3AclSchema
from cartography.models.aws.s3.bucket import S3BucketEncryptionSchema
from cartography.models.aws.s3.bucket import S3BucketLoggingSchema
from cartography.models.aws.s3.bucket import S3BucketOwnershipSchema
from cartography.models.aws.s3.bucket import S3BucketPolicySchema
from cartography.models.aws.s3.bucket import S3BucketPublicAccessBlockSchema
from cartography.models.aws.s3.bucket import S3BucketSchema
from cartography.models.aws.s3.bucket import S3BucketVersioningSchema
from cartography.models.aws.s3.policy_statement import S3PolicyStatementSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


# Sentinel value to indicate a fetch operation failed (vs None for "no configuration")
# When a fetch returns FETCH_FAILED, we skip loading that property group to preserve existing data.
class _FetchFailed:
    """Sentinel indicating fetch failure - preserves existing data in Neo4j."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "FETCH_FAILED"


FETCH_FAILED = _FetchFailed()

# Type alias for values that may be FETCH_FAILED
MaybeFailed = Union[Optional[Dict], _FetchFailed]


@timeit
def get_s3_bucket_list(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3_session.client("s3")
    # NOTE no paginator available for this operation
    buckets = client.list_buckets()
    for bucket in buckets["Buckets"]:
        try:
            bucket["Region"] = client.get_bucket_location(Bucket=bucket["Name"])[
                "LocationConstraint"
            ]
        except ClientError as e:
            should_handle, _ = _is_common_exception(e, bucket["Name"])
            if should_handle:
                bucket["Region"] = None
                logger.warning(
                    "skipping bucket='{}' due to exception.".format(bucket["Name"]),
                )
                continue
            else:
                raise
    return buckets


@timeit
def get_s3_bucket_details(
    boto3_session: boto3.session.Session,
    bucket_data: Dict,
) -> Generator[
    Tuple[
        str,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
    ],
    None,
    None,
]:
    """
    Iterates over all S3 buckets. Yields bucket name (string), S3 bucket policies (JSON), ACLs (JSON),
    default encryption policy (JSON), Versioning (JSON), Public Access Block (JSON), Ownership Controls (JSON),
    and Logging (JSON).

    Each value can be:
    - A dict with the configuration data
    - None indicating no configuration exists (valid state)
    - FETCH_FAILED indicating the fetch failed and existing data should be preserved
    """
    # a local store for s3 clients so that we may re-use clients for an AWS region
    s3_regional_clients: Dict[Any, Any] = {}

    BucketDetail = Tuple[
        str,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
        MaybeFailed,
    ]

    async def _get_bucket_detail(bucket: Dict[str, Any]) -> BucketDetail:
        # Note: bucket['Region'] is sometimes None because
        # client.get_bucket_location() does not return a location constraint for buckets
        # in us-east-1 region
        client = s3_regional_clients.get(bucket["Region"])
        if not client:
            client = boto3_session.client("s3", bucket["Region"])
            s3_regional_clients[bucket["Region"]] = client
        (
            acl,
            policy,
            encryption,
            versioning,
            public_access_block,
            bucket_ownership_controls,
            bucket_logging,
        ) = await asyncio.gather(
            to_asynchronous(get_acl, bucket, client),
            to_asynchronous(get_policy, bucket, client),
            to_asynchronous(get_encryption, bucket, client),
            to_asynchronous(get_versioning, bucket, client),
            to_asynchronous(get_public_access_block, bucket, client),
            to_asynchronous(get_bucket_ownership_controls, bucket, client),
            to_asynchronous(get_bucket_logging, bucket, client),
        )
        return (
            bucket["Name"],
            acl,
            policy,
            encryption,
            versioning,
            public_access_block,
            bucket_ownership_controls,
            bucket_logging,
        )

    bucket_details = to_synchronous(
        *[_get_bucket_detail(bucket) for bucket in bucket_data["Buckets"]],
    )
    yield from bucket_details


@timeit
def get_policy(bucket: Dict, client: botocore.client.BaseClient) -> MaybeFailed:
    """
    Gets the S3 bucket policy. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_policy(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket policy for {bucket['Name']} - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_acl(bucket: Dict, client: botocore.client.BaseClient) -> MaybeFailed:
    """
    Gets the S3 bucket ACL. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_acl(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket ACL for {bucket['Name']} - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_encryption(bucket: Dict, client: botocore.client.BaseClient) -> MaybeFailed:
    """
    Gets the S3 bucket default encryption configuration. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_encryption(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket encryption for {bucket['Name']} - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_versioning(bucket: Dict, client: botocore.client.BaseClient) -> MaybeFailed:
    """
    Gets the S3 bucket versioning configuration. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_versioning(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket versioning for {bucket['Name']} - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_public_access_block(
    bucket: Dict,
    client: botocore.client.BaseClient,
) -> MaybeFailed:
    """
    Gets the S3 bucket public access block configuration. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_public_access_block(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket public access block for {bucket['Name']}"
            " - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_bucket_ownership_controls(
    bucket: Dict, client: botocore.client.BaseClient
) -> MaybeFailed:
    """
    Gets the S3 object ownership controls configuration. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_ownership_controls(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket ownership controls for {bucket['Name']}"
            " - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def get_bucket_logging(bucket: Dict, client: botocore.client.BaseClient) -> MaybeFailed:
    """
    Gets the S3 bucket logging status configuration. Returns FETCH_FAILED if fetch failed.
    """
    try:
        return client.get_bucket_logging(Bucket=bucket["Name"])
    except ClientError as e:
        should_handle, is_failure = _is_common_exception(e, bucket["Name"])
        if should_handle:
            return FETCH_FAILED if is_failure else None
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket logging status for {bucket['Name']} - Could not connect to the endpoint URL",
        )
        return FETCH_FAILED


@timeit
def _is_common_exception(e: Exception, bucket_name: str) -> Tuple[bool, bool]:
    """
    Check if an exception is a known/expected S3 exception that should be handled.

    Returns:
        Tuple of (should_handle, is_fetch_failure):
        - should_handle: True if exception should be handled (not re-raised)
        - is_fetch_failure: True if this is a fetch failure (vs "no configuration" which is valid)
    """
    error_msg = "Failed to retrieve S3 bucket detail"
    error_str = str(e.args[0]) if e.args else ""

    # "No configuration" errors - valid states where no config exists
    # These return (True, False) - handle but not a failure
    if "NoSuchBucketPolicy" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - NoSuchBucketPolicy")
        return (True, False)
    elif "ServerSideEncryptionConfigurationNotFoundError" in error_str:
        logger.warning(
            f"{error_msg} for {bucket_name} - ServerSideEncryptionConfigurationNotFoundError",
        )
        return (True, False)
    elif "NoSuchPublicAccessBlockConfiguration" in error_str:
        logger.warning(
            f"{error_msg} for {bucket_name} - NoSuchPublicAccessBlockConfiguration",
        )
        return (True, False)
    elif "OwnershipControlsNotFoundError" in error_str:
        logger.warning(
            f"{error_msg} for {bucket_name} - OwnershipControlsNotFoundError"
        )
        return (True, False)

    # Fetch failures - should preserve existing data
    # These return (True, True) - handle and is a failure
    elif "AccessDenied" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - Access Denied")
        return (True, True)
    elif "NoSuchBucket" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - No Such Bucket")
        return (True, True)
    elif "AllAccessDisabled" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - Bucket is disabled")
        return (True, True)
    elif "EndpointConnectionError" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - EndpointConnectionError")
        return (True, True)
    elif "InvalidToken" in error_str:
        logger.warning(f"{error_msg} for {bucket_name} - InvalidToken")
        return (True, True)
    elif "IllegalLocationConstraintException" in error_str:
        logger.warning(
            f"{error_msg} for {bucket_name} - IllegalLocationConstraintException",
        )
        return (True, True)

    return (False, False)


@timeit
def _load_s3_acls(
    neo4j_session: neo4j.Session,
    acls: List[Dict[str, Any]],
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Ingest S3 ACL into neo4j.
    """
    load(
        neo4j_session,
        S3AclSchema(),
        acls,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )

    # implement the acl permission
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#permissions
    run_analysis_job(
        "aws_s3acl_analysis.json",
        neo4j_session,
        {"AWS_ID": aws_account_id},
        package="cartography.data.jobs.scoped_analysis",
    )


@timeit
def _load_s3_policy_statements(
    neo4j_session: neo4j.Session,
    statements: List[Dict],
    update_tag: int,
    aws_account_id: str = "",
) -> None:
    load(
        neo4j_session,
        S3PolicyStatementSchema(),
        statements,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )


def _merge_bucket_details(
    bucket_data: Dict,
    s3_details_iter: Generator[Any, Any, Any],
    aws_account_id: str,
) -> Dict[str, Any]:
    """
    Merge basic bucket data with details (policy, encryption, versioning, etc.)
    into separate data structures for each composite schema.

    Uses the Composite Node Pattern: returns separate lists for each property group,
    allowing us to skip loading a group when its fetch failed (preserving existing data).

    Returns a dict with:
        - base_buckets: List of bucket dicts with base properties (always populated)
        - policy_buckets: List of bucket dicts with policy properties
        - encryption_buckets: List of bucket dicts with encryption properties
        - versioning_buckets: List of bucket dicts with versioning properties
        - public_access_block_buckets: List of bucket dicts with public access block properties
        - ownership_buckets: List of bucket dicts with ownership properties
        - logging_buckets: List of bucket dicts with logging properties
        - acls: List of parsed ACL dicts
        - statements: List of parsed policy statement dicts
    """
    # Create a dict for quick lookup by bucket name
    buckets_by_name: Dict[str, Dict] = {}
    for bucket in bucket_data["Buckets"]:
        buckets_by_name[bucket["Name"]] = {
            "Name": bucket["Name"],
            "Region": bucket["Region"],
            "Arn": "arn:aws:s3:::" + bucket["Name"],
            "CreationDate": str(bucket["CreationDate"]),
        }

    # Lists for composite schema data
    policy_buckets: List[Dict] = []
    encryption_buckets: List[Dict] = []
    versioning_buckets: List[Dict] = []
    public_access_block_buckets: List[Dict] = []
    ownership_buckets: List[Dict] = []
    logging_buckets: List[Dict] = []
    acls: List[Dict] = []
    statements: List[Dict] = []

    for (
        bucket_name,
        acl,
        policy,
        encryption,
        versioning,
        public_access_block,
        bucket_ownership_controls,
        bucket_logging,
    ) in s3_details_iter:
        bucket_dict = buckets_by_name.get(bucket_name)
        if not bucket_dict:
            continue

        # Parse and collect ACLs (skip if fetch failed)
        if acl is not FETCH_FAILED:
            parsed_acls = parse_acl(acl, bucket_name, aws_account_id)
            if parsed_acls is not None:
                acls.extend(parsed_acls)

        # Parse policy for anonymous access and policy statements (skip if fetch failed)
        if policy is not FETCH_FAILED:
            parsed_policy = parse_policy(bucket_name, policy)
            policy_data = {
                "Name": bucket_name,
                "anonymous_access": False,
                "anonymous_actions": [],
            }
            if parsed_policy is not None:
                policy_data["anonymous_access"] = parsed_policy["internet_accessible"]
                policy_data["anonymous_actions"] = parsed_policy["accessible_actions"]
            policy_buckets.append(policy_data)

            # Parse and collect policy statements
            parsed_statements = parse_policy_statements(bucket_name, policy)
            if parsed_statements is not None:
                statements.extend(parsed_statements)

        # Parse encryption (skip if fetch failed)
        if encryption is not FETCH_FAILED:
            parsed_encryption = parse_encryption(bucket_name, encryption)
            encryption_data = {
                "Name": bucket_name,
                "default_encryption": False,
                "encryption_algorithm": None,
                "encryption_key_id": None,
                "bucket_key_enabled": None,
            }
            if parsed_encryption is not None:
                encryption_data["default_encryption"] = parsed_encryption[
                    "default_encryption"
                ]
                encryption_data["encryption_algorithm"] = parsed_encryption[
                    "encryption_algorithm"
                ]
                encryption_data["encryption_key_id"] = parsed_encryption.get(
                    "encryption_key_id"
                )
                encryption_data["bucket_key_enabled"] = parsed_encryption.get(
                    "bucket_key_enabled"
                )
            encryption_buckets.append(encryption_data)

        # Parse versioning (skip if fetch failed)
        if versioning is not FETCH_FAILED:
            parsed_versioning = parse_versioning(bucket_name, versioning)
            versioning_data = {
                "Name": bucket_name,
                "versioning_status": None,
                "mfa_delete": None,
            }
            if parsed_versioning is not None:
                versioning_data["versioning_status"] = parsed_versioning["status"]
                versioning_data["mfa_delete"] = parsed_versioning["mfa_delete"]
            versioning_buckets.append(versioning_data)

        # Parse public access block (skip if fetch failed)
        if public_access_block is not FETCH_FAILED:
            parsed_public_access_block = parse_public_access_block(
                bucket_name,
                public_access_block,
            )
            public_access_block_data = {
                "Name": bucket_name,
                "block_public_acls": None,
                "ignore_public_acls": None,
                "block_public_policy": None,
                "restrict_public_buckets": None,
            }
            if parsed_public_access_block is not None:
                public_access_block_data["block_public_acls"] = (
                    parsed_public_access_block["block_public_acls"]
                )
                public_access_block_data["ignore_public_acls"] = (
                    parsed_public_access_block["ignore_public_acls"]
                )
                public_access_block_data["block_public_policy"] = (
                    parsed_public_access_block["block_public_policy"]
                )
                public_access_block_data["restrict_public_buckets"] = (
                    parsed_public_access_block["restrict_public_buckets"]
                )
            public_access_block_buckets.append(public_access_block_data)

        # Parse bucket ownership controls (skip if fetch failed)
        if bucket_ownership_controls is not FETCH_FAILED:
            parsed_bucket_ownership_controls = parse_bucket_ownership_controls(
                bucket_name, bucket_ownership_controls
            )
            ownership_data = {
                "Name": bucket_name,
                "object_ownership": None,
            }
            if parsed_bucket_ownership_controls is not None:
                ownership_data["object_ownership"] = parsed_bucket_ownership_controls[
                    "object_ownership"
                ]
            ownership_buckets.append(ownership_data)

        # Parse bucket logging (skip if fetch failed)
        if bucket_logging is not FETCH_FAILED:
            parsed_bucket_logging = parse_bucket_logging(bucket_name, bucket_logging)
            logging_data = {
                "Name": bucket_name,
                "logging_enabled": None,
                "logging_target_bucket": None,
            }
            if parsed_bucket_logging is not None:
                logging_data["logging_enabled"] = parsed_bucket_logging[
                    "logging_enabled"
                ]
                logging_data["logging_target_bucket"] = parsed_bucket_logging[
                    "target_bucket"
                ]
            logging_buckets.append(logging_data)

    return {
        "base_buckets": list(buckets_by_name.values()),
        "policy_buckets": policy_buckets,
        "encryption_buckets": encryption_buckets,
        "versioning_buckets": versioning_buckets,
        "public_access_block_buckets": public_access_block_buckets,
        "ownership_buckets": ownership_buckets,
        "logging_buckets": logging_buckets,
        "acls": acls,
        "statements": statements,
    }


@timeit
def load_s3_details(
    neo4j_session: neo4j.Session,
    s3_details_iter: Generator[Any, Any, Any],
    bucket_data: Dict,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Merge bucket details with basic bucket data and load using composite schemas.

    Uses the Composite Node Pattern: each property group is loaded separately,
    so if a fetch fails for one group, we skip loading that group and preserve
    existing data in Neo4j.
    """
    # Merge all bucket data into separate lists per property group
    merged_data = _merge_bucket_details(bucket_data, s3_details_iter, aws_account_id)

    # cleanup existing policy properties set on S3 Buckets
    run_cleanup_job(
        "aws_s3_details.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id},
    )

    # Load base bucket properties (always done for all buckets)
    load(
        neo4j_session,
        S3BucketSchema(),
        merged_data["base_buckets"],
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )

    # Load composite schema properties (only for buckets where fetch succeeded)
    # Policy properties
    if merged_data["policy_buckets"]:
        load(
            neo4j_session,
            S3BucketPolicySchema(),
            merged_data["policy_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Encryption properties
    if merged_data["encryption_buckets"]:
        load(
            neo4j_session,
            S3BucketEncryptionSchema(),
            merged_data["encryption_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Versioning properties
    if merged_data["versioning_buckets"]:
        load(
            neo4j_session,
            S3BucketVersioningSchema(),
            merged_data["versioning_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Public access block properties
    if merged_data["public_access_block_buckets"]:
        load(
            neo4j_session,
            S3BucketPublicAccessBlockSchema(),
            merged_data["public_access_block_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Ownership properties
    if merged_data["ownership_buckets"]:
        load(
            neo4j_session,
            S3BucketOwnershipSchema(),
            merged_data["ownership_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Logging properties
    if merged_data["logging_buckets"]:
        load(
            neo4j_session,
            S3BucketLoggingSchema(),
            merged_data["logging_buckets"],
            lastupdated=update_tag,
            AWS_ID=aws_account_id,
        )

    # Load ACLs
    _load_s3_acls(neo4j_session, merged_data["acls"], aws_account_id, update_tag)

    # Load policy statements
    _load_s3_policy_statements(
        neo4j_session, merged_data["statements"], update_tag, aws_account_id
    )


@timeit
def parse_policy(bucket: str, policyDict: Optional[Dict]) -> Optional[Dict]:
    """
    Uses PolicyUniverse to parse S3 policies and returns the internet accessibility results
    """
    # policy is not required, so may be None
    # policy JSON format. Note condition can be any JSON statement so will need to import as-is
    # policy is a very complex format, so the policyuniverse library will be used for parsing out important data
    # ...metadata...
    # "Policy" :
    # {
    #     "Version": "2012-10-17",
    #     {
    #         "Statement": [
    #             {
    #                 "Effect": "Allow",
    #                 "Principal": "*",
    #                 "Action": "s3:GetObject",
    #                 "Resource": "arn:aws:s3:::MyBucket/*"
    #             },
    #             {
    #                 "Effect": "Deny",
    #                 "Principal": "*",
    #                 "Action": "s3:GetObject",
    #                 "Resource": "arn:aws:s3:::MyBucket/MySecretFolder/*"
    #             },
    #             {
    #                 "Effect": "Allow",
    #                 "Principal": {
    #                     "AWS": "arn:aws:iam::123456789012:root"
    #                 },
    #                 "Action": [
    #                     "s3:DeleteObject",
    #                     "s3:PutObject"
    #                 ],
    #                 "Resource": "arn:aws:s3:::MyBucket/*"
    #             }
    #         ]
    #     }
    # }
    if policyDict is None:
        return None
    # get just the policy element and convert to JSON because boto3 returns this as string
    policy = Policy(json.loads(policyDict["Policy"]))
    if policy.is_internet_accessible():
        return {
            "bucket": bucket,
            "internet_accessible": True,
            "accessible_actions": list(policy.internet_accessible_actions()),
        }
    else:
        return {
            "bucket": bucket,
            "internet_accessible": False,
            "accessible_actions": [],
        }


@timeit
def parse_policy_statements(bucket: str, policyDict: Policy) -> List[Dict]:
    if policyDict is None:
        return None

    policy = json.loads(policyDict["Policy"])
    statements = []
    stmt_index = 1
    for s in policy["Statement"]:
        stmt = dict()
        stmt["bucket"] = bucket
        stmt["statement_id"] = bucket + "/policy_statement/" + str(stmt_index)
        stmt_index += 1
        if "Id" in policy:
            stmt["policy_id"] = policy["Id"]
        if "Version" in policy:
            stmt["policy_version"] = policy["Version"]
        if "Sid" in s:
            stmt["Sid"] = s["Sid"]
            stmt["statement_id"] += "/" + s["Sid"]
        if "Effect" in s:
            stmt["Effect"] = s["Effect"]
        if "Resource" in s:
            stmt["Resource"] = s["Resource"]
        if "Action" in s:
            stmt["Action"] = s["Action"]
        if "Condition" in s:
            stmt["Condition"] = json.dumps(s["Condition"])
        if "Principal" in s:
            stmt["Principal"] = json.dumps(s["Principal"])

        statements.append(stmt)

    return statements


@timeit
def parse_acl(
    acl: Optional[Dict],
    bucket: str,
    aws_account_id: str,
) -> Optional[List[Dict]]:
    """Parses the AWS ACL object and returns a dict of the relevant data"""
    # ACL JSON looks like
    # ...metadata...
    # {
    #     "Grants": [
    #         {
    #             "Grantee": {
    #                 "DisplayName": "string",
    #                 "EmailAddress": "string",
    #                 "ID": "string",
    #                 "Type": "CanonicalUser" | "AmazonCustomerByEmail" | "Group",
    #                 "URI": "string"
    #             },
    #             "Permission": "FULL_CONTROL" | "WRITE" | "WRITE_ACP" | "READ" | "READ_ACP"
    #         }
    #              ...
    #     ],
    #     "Owner": {
    #         "DisplayName": "string",
    #         "ID": "string"
    #     }
    # }
    if acl is None:
        return None
    acl_list: List[Dict] = []
    for grant in acl["Grants"]:
        parsed_acl = None
        if grant["Grantee"]["Type"] == "CanonicalUser":
            parsed_acl = {
                "bucket": bucket,
                "owner": acl["Owner"].get("DisplayName"),
                "ownerid": acl["Owner"].get("ID"),
                "type": grant["Grantee"]["Type"],
                "displayname": grant["Grantee"].get("DisplayName"),
                "granteeid": grant["Grantee"].get("ID"),
                "uri": None,
                "permission": grant.get("Permission"),
            }
        elif grant["Grantee"]["Type"] == "Group":
            parsed_acl = {
                "bucket": bucket,
                "owner": acl["Owner"].get("DisplayName"),
                "ownerid": acl["Owner"].get("ID"),
                "type": grant["Grantee"]["Type"],
                "displayname": None,
                "granteeid": None,
                "uri": grant["Grantee"].get("URI"),
                "permission": grant.get("Permission"),
            }
        else:
            logger.warning("Unexpected grant type: %s", grant["Grantee"]["Type"])
            continue

        # TODO this can be replaced with a string join
        id_data = "{}:{}:{}:{}:{}:{}:{}:{}".format(
            aws_account_id,
            parsed_acl["owner"],
            parsed_acl["ownerid"],
            parsed_acl["type"],
            parsed_acl["displayname"],
            parsed_acl["granteeid"],
            parsed_acl["uri"],
            parsed_acl["permission"],
        )

        parsed_acl["id"] = hashlib.sha256(id_data.encode("utf8")).hexdigest()
        acl_list.append(parsed_acl)

    return acl_list


@timeit
def parse_encryption(bucket: str, encryption: Optional[Dict]) -> Optional[Dict]:
    """Parses the S3 default encryption object and returns a dict of the relevant data"""
    # Encryption object JSON looks like:
    # {
    #     'ServerSideEncryptionConfiguration': {
    #         'Rules': [
    #             {
    #                 'ApplyServerSideEncryptionByDefault': {
    #                     'SSEAlgorithm': 'AES256'|'aws:kms',
    #                     'KMSMasterKeyID': 'string'
    #                 },
    #                 'BucketKeyEnabled': True|False
    #             },
    #         ]
    #     }
    # }
    if encryption is None:
        return None
    _ssec = encryption.get("ServerSideEncryptionConfiguration", {})
    # Rules is a list, but only one rule ever exists
    try:
        rule = _ssec.get("Rules", []).pop()
    except IndexError:
        return None
    algorithm = rule.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm")
    if not algorithm:
        return None
    return {
        "bucket": bucket,
        "default_encryption": True,
        "encryption_algorithm": algorithm,
        "encryption_key_id": rule.get("ApplyServerSideEncryptionByDefault", {}).get(
            "KMSMasterKeyID",
        ),
        "bucket_key_enabled": rule.get("BucketKeyEnabled"),
    }


@timeit
def parse_versioning(bucket: str, versioning: Optional[Dict]) -> Optional[Dict]:
    """Parses the S3 versioning object and returns a dict of the relevant data"""
    # Versioning object JSON looks like:
    # {
    #     'Status': 'Enabled'|'Suspended',
    #     'MFADelete': 'Enabled'|'Disabled'
    # }
    if versioning is None:
        return None
    return {
        "bucket": bucket,
        "status": versioning.get("Status"),
        "mfa_delete": versioning.get("MFADelete"),
    }


@timeit
def parse_public_access_block(
    bucket: str,
    public_access_block: Optional[Dict],
) -> Optional[Dict]:
    """Parses the S3 public access block object and returns a dict of the relevant data"""
    # Versioning object JSON looks like:
    # {
    #     'PublicAccessBlockConfiguration': {
    #         'BlockPublicAcls': True|False,
    #         'IgnorePublicAcls': True|False,
    #         'BlockPublicPolicy': True|False,
    #         'RestrictPublicBuckets': True|False
    #     }
    # }
    if public_access_block is None:
        return None
    pab = public_access_block["PublicAccessBlockConfiguration"]
    return {
        "bucket": bucket,
        "block_public_acls": pab.get("BlockPublicAcls"),
        "ignore_public_acls": pab.get("IgnorePublicAcls"),
        "block_public_policy": pab.get("BlockPublicPolicy"),
        "restrict_public_buckets": pab.get("RestrictPublicBuckets"),
    }


@timeit
def parse_bucket_ownership_controls(
    bucket: str, bucket_ownership_controls: Optional[Dict]
) -> Optional[Dict]:
    """Parses the S3 bucket ownership controls object and returns a dict of the relevant data"""
    # Versioning object JSON looks like:
    # {
    #     'OwnershipControls': {
    #         'Rules': [
    #             {
    #                 'ObjectOwnership': 'BucketOwnerPreferred'|'ObjectWriter'|'BucketOwnerEnforced'
    #             },
    #         ]
    #     }
    # }
    if bucket_ownership_controls is None:
        return None
    return {
        "bucket": bucket,
        "object_ownership": bucket_ownership_controls.get("OwnershipControls", {})
        .get("Rules", [{}])[0]
        .get("ObjectOwnership"),
    }


def parse_bucket_logging(bucket: str, bucket_logging: Optional[Dict]) -> Optional[Dict]:
    """Parses the S3 bucket logging status configuration and returns a dict of the relevant data"""
    # Logging status object JSON looks like:
    # {
    #     'LoggingEnabled': {
    #         'TargetBucket': 'string',
    #         'TargetGrants': [
    #             {
    #                 'Grantee': {
    #                     'DisplayName': 'string',
    #                     'EmailAddress': 'string',
    #                     'ID': 'string',
    #                     'Type': 'CanonicalUser'|'AmazonCustomerByEmail'|'Group',
    #                     'URI': 'string'
    #                 },
    #                 'Permission': 'FULL_CONTROL'|'READ'|'WRITE'
    #             },
    #         ],
    #         'TargetPrefix': 'string',
    #         'TargetObjectKeyFormat': {
    #             'SimplePrefix': {},
    #             'PartitionedPrefix': {
    #                 'PartitionDateSource': 'EventTime'|'DeliveryTime'
    #             }
    #         }
    #     }
    # }
    # Or empty dict {} if logging is not enabled
    if bucket_logging is None:
        return None

    logging_config = bucket_logging.get("LoggingEnabled", {})
    if not logging_config:
        return {
            "bucket": bucket,
            "logging_enabled": False,
            "target_bucket": None,
        }

    return {
        "bucket": bucket,
        "logging_enabled": True,
        "target_bucket": logging_config.get("TargetBucket"),
    }


@timeit
def parse_notification_configuration(
    bucket: str, notification_config: Optional[Dict]
) -> List[Dict]:
    """
    Parse S3 bucket notification configuration to extract SNS topic notifications.
    Returns a list of notification configurations.
    """
    if not notification_config or "TopicConfigurations" not in notification_config:
        return []

    notifications = []
    for topic_config in notification_config.get("TopicConfigurations", []):
        notification = {
            "bucket": bucket,
            "TopicArn": topic_config["TopicArn"],
        }
        notifications.append(notification)
    return notifications


@timeit
def _load_s3_notifications(
    neo4j_session: neo4j.Session,
    notifications: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 bucket to SNS topic notification relationships into neo4j.
    """
    ingest_notifications = """
    UNWIND $notifications AS notification
    MATCH (bucket:S3Bucket{name: notification.bucket})
    MATCH (topic:SNSTopic{arn: notification.TopicArn})
    MERGE (bucket)-[r:NOTIFIES]->(topic)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    run_write_query(
        neo4j_session,
        ingest_notifications,
        notifications=notifications,
        UpdateTag=update_tag,
    )


def _transform_bucket_data(data: Dict) -> List[Dict]:
    """Transform bucket data for loading with the schema (basic properties only)."""
    bucket_data = []
    for bucket in data["Buckets"]:
        bucket_data.append(
            {
                "Name": bucket["Name"],
                "Region": bucket["Region"],
                "Arn": "arn:aws:s3:::" + bucket["Name"],
                "CreationDate": str(bucket["CreationDate"]),
            }
        )
    return bucket_data


@timeit
def load_s3_buckets(
    neo4j_session: neo4j.Session,
    data: Dict,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """Load S3 buckets with basic properties via schema."""
    bucket_data = _transform_bucket_data(data)
    load(
        neo4j_session,
        S3BucketSchema(),
        bucket_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def _load_s3_encryption(
    neo4j_session: neo4j.Session,
    encryption_configs,
    update_tag: int,
) -> None:
    """
    Update S3 buckets with encryption properties.
    This is a wrapper for backward compatibility with tests.
    """
    # Handle both single dict and list of dicts
    if isinstance(encryption_configs, dict):
        encryption_configs = [encryption_configs]

    bucket_data = []
    for config in encryption_configs:
        bucket_data.append(
            {
                "Name": config["bucket"],
                "default_encryption": config.get("default_encryption", False),
                "encryption_algorithm": config.get("encryption_algorithm"),
                "encryption_key_id": config.get("encryption_key_id"),
                "bucket_key_enabled": config.get("bucket_key_enabled"),
            }
        )
    load(
        neo4j_session,
        S3BucketEncryptionSchema(),
        bucket_data,
        lastupdated=update_tag,
        AWS_ID="",
    )


@timeit
def _load_bucket_ownership_controls(
    neo4j_session: neo4j.Session,
    bucket_ownership_controls_configs,
    update_tag: int,
) -> None:
    """
    Update S3 buckets with ownership control properties.
    This is a wrapper for backward compatibility with tests.
    """
    # Handle both single dict and list of dicts
    if isinstance(bucket_ownership_controls_configs, dict):
        bucket_ownership_controls_configs = [bucket_ownership_controls_configs]

    bucket_data = []
    for config in bucket_ownership_controls_configs:
        bucket_data.append(
            {
                "Name": config["bucket"],
                "object_ownership": config.get("object_ownership"),
            }
        )
    load(
        neo4j_session,
        S3BucketOwnershipSchema(),
        bucket_data,
        lastupdated=update_tag,
        AWS_ID="",
    )


@timeit
def _load_bucket_logging(
    neo4j_session: neo4j.Session,
    bucket_logging_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Update S3 buckets with logging properties.
    This is a wrapper for backward compatibility with tests.
    """
    bucket_data = []
    for config in bucket_logging_configs:
        bucket_data.append(
            {
                "Name": config["bucket"],
                "logging_enabled": config.get("logging_enabled"),
                "logging_target_bucket": config.get("target_bucket"),
            }
        )
    load(
        neo4j_session,
        S3BucketLoggingSchema(),
        bucket_data,
        lastupdated=update_tag,
        AWS_ID="",
    )


@timeit
def cleanup_s3_buckets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(S3BucketSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_s3_bucket_acl_and_policy(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Clean up stale S3Acl and S3PolicyStatement nodes."""
    GraphJob.from_node_schema(S3AclSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(S3PolicyStatementSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
@aws_handle_regions
def _sync_s3_notifications(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    bucket_data: Dict,
    update_tag: int,
) -> None:
    """
    Sync S3 bucket notification configurations to Neo4j.
    """
    logger.info("Syncing S3 bucket notifications")
    s3_client = boto3_session.client("s3")
    notifications = []

    for bucket in bucket_data["Buckets"]:
        try:
            notification_config = s3_client.get_bucket_notification_configuration(
                Bucket=bucket["Name"]
            )
            parsed_notifications = parse_notification_configuration(
                bucket["Name"], notification_config
            )
            notifications.extend(parsed_notifications)
            logger.debug(
                f"Found {len(parsed_notifications)} notifications for bucket {bucket['Name']}"
            )
        except ClientError as e:
            logger.warning(
                f"Failed to retrieve notification configuration for bucket {bucket['Name']}: {e}"
            )
            continue

    logger.info(f"Loading {len(notifications)} S3 bucket notifications into Neo4j")
    _load_s3_notifications(neo4j_session, notifications, update_tag)


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
    Sync S3 buckets and their configurations to Neo4j.
    This includes:
    1. Basic bucket information with all properties (encryption, versioning, etc.)
    2. ACLs and policies
    3. Notification configurations
    """
    logger.info("Syncing S3 for account '%s'", current_aws_account_id)

    bucket_data = get_s3_bucket_list(boto3_session)
    bucket_details_iter = get_s3_bucket_details(boto3_session, bucket_data)

    # Load buckets with all details merged, plus ACLs and policy statements
    load_s3_details(
        neo4j_session,
        bucket_details_iter,
        bucket_data,
        current_aws_account_id,
        update_tag,
    )
    cleanup_s3_buckets(neo4j_session, common_job_parameters)
    cleanup_s3_bucket_acl_and_policy(neo4j_session, common_job_parameters)

    _sync_s3_notifications(neo4j_session, boto3_session, bucket_data, update_tag)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="S3Bucket",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
