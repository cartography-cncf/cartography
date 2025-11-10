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

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from policyuniverse.policy import Policy

from cartography.client.core.tx import run_write_query
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
            if _is_common_exception(e, bucket):
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
) -> Generator[Tuple[str, Dict, Dict, Dict, Dict, Dict, Dict], None, None]:
    """
    Iterates over all S3 buckets. Yields bucket name (string), S3 bucket policies (JSON), ACLs (JSON),
    default encryption policy (JSON), Versioning (JSON), and Public Access Block (JSON)
    """
    # a local store for s3 clients so that we may re-use clients for an AWS region
    s3_regional_clients: Dict[Any, Any] = {}

    BucketDetail = Tuple[
        str,
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
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
def get_policy(bucket: Dict, client: botocore.client.BaseClient) -> Optional[Dict]:
    """
    Gets the S3 bucket policy.
    """
    policy = None
    try:
        policy = client.get_bucket_policy(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket policy for {bucket['Name']} - Could not connect to the endpoint URL",
        )
    return policy


@timeit
def get_acl(bucket: Dict, client: botocore.client.BaseClient) -> Optional[Dict]:
    """
    Gets the S3 bucket ACL.
    """
    acl = None
    try:
        acl = client.get_bucket_acl(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket ACL for {bucket['Name']} - Could not connect to the endpoint URL",
        )
    return acl


@timeit
def get_encryption(bucket: Dict, client: botocore.client.BaseClient) -> Optional[Dict]:
    """
    Gets the S3 bucket default encryption configuration.
    """
    encryption = None
    try:
        encryption = client.get_bucket_encryption(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket encryption for {bucket['Name']} - Could not connect to the endpoint URL",
        )
    return encryption


@timeit
def get_versioning(bucket: Dict, client: botocore.client.BaseClient) -> Optional[Dict]:
    """
    Gets the S3 bucket versioning configuration.
    """
    versioning = None
    try:
        versioning = client.get_bucket_versioning(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket versioning for {bucket['Name']} - Could not connect to the endpoint URL",
        )
    return versioning


@timeit
def get_public_access_block(
    bucket: Dict,
    client: botocore.client.BaseClient,
) -> Optional[Dict]:
    """
    Gets the S3 bucket public access block configuration.
    """
    public_access_block = None
    try:
        public_access_block = client.get_public_access_block(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket public access block for {bucket['Name']}"
            " - Could not connect to the endpoint URL",
        )
    return public_access_block


@timeit
def get_bucket_ownership_controls(
    bucket: Dict, client: botocore.client.BaseClient
) -> Optional[Dict]:
    """
    Gets the S3 object ownership controls configuration.
    """
    bucket_ownership_controls = None
    try:
        bucket_ownership_controls = client.get_bucket_ownership_controls(
            Bucket=bucket["Name"]
        )
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket ownership controls for {bucket['Name']}"
            " - Could not connect to the endpoint URL",
        )
    return bucket_ownership_controls


@timeit
@aws_handle_regions
def get_bucket_logging(
    bucket: Dict, client: botocore.client.BaseClient
) -> Optional[Dict]:
    """
    Gets the S3 bucket logging status configuration.
    """
    bucket_logging = None
    try:
        bucket_logging = client.get_bucket_logging(Bucket=bucket["Name"])
    except ClientError as e:
        if _is_common_exception(e, bucket):
            pass
        else:
            raise
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 bucket logging status for {bucket['Name']} - Could not connect to the endpoint URL",
        )
    return bucket_logging


@timeit
def _is_common_exception(e: Exception, bucket: Dict) -> bool:
    error_msg = "Failed to retrieve S3 bucket detail"
    if "AccessDenied" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - Access Denied")
        return True
    elif "NoSuchBucketPolicy" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - NoSuchBucketPolicy")
        return True
    elif "NoSuchBucket" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - No Such Bucket")
        return True
    elif "AllAccessDisabled" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - Bucket is disabled")
        return True
    elif "EndpointConnectionError" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - EndpointConnectionError")
        return True
    elif "ServerSideEncryptionConfigurationNotFoundError" in e.args[0]:
        logger.warning(
            f"{error_msg} for {bucket['Name']} - ServerSideEncryptionConfigurationNotFoundError",
        )
        return True
    elif "InvalidToken" in e.args[0]:
        logger.warning(f"{error_msg} for {bucket['Name']} - InvalidToken")
        return True
    elif "NoSuchPublicAccessBlockConfiguration" in e.args[0]:
        logger.warning(
            f"{error_msg} for {bucket['Name']} - NoSuchPublicAccessBlockConfiguration",
        )
        return True
    elif "IllegalLocationConstraintException" in e.args[0]:
        logger.warning(
            f"{error_msg} for {bucket['Name']} - IllegalLocationConstraintException",
        )
        return True
    elif "OwnershipControlsNotFoundError" in e.args[0]:
        logger.warning(
            f"{error_msg} for {bucket['Name']} - OwnershipControlsNotFoundError"
        )
        return True
    return False


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
    ingest_acls = """
    UNWIND $acls AS acl
    MERGE (a:S3Acl{id: acl.id})
    ON CREATE SET a.firstseen = timestamp(), a.owner = acl.owner, a.ownerid = acl.ownerid, a.type = acl.type,
    a.displayname = acl.displayname, a.granteeid = acl.granteeid, a.uri = acl.uri, a.permission = acl.permission
    SET a.lastupdated = $UpdateTag
    WITH a,acl MATCH (s3:S3Bucket{id: acl.bucket})
    MERGE (a)-[r:APPLIES_TO]->(s3)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_acls,
        acls=acls,
        UpdateTag=update_tag,
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
def _load_s3_policies(
    neo4j_session: neo4j.Session,
    policies: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 policy results into neo4j.
    """
    # NOTE we use the coalesce function so appending works when the value is null initially
    ingest_policies = """
    UNWIND $policies AS policy
    MATCH (s:S3Bucket) where s.name = policy.bucket
    SET s.anonymous_access = (coalesce(s.anonymous_access, false) OR policy.internet_accessible),
    s.anonymous_actions = coalesce(s.anonymous_actions, []) + policy.accessible_actions,
    s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_policies,
        policies=policies,
        UpdateTag=update_tag,
    )


@timeit
def _load_s3_policy_statements(
    neo4j_session: neo4j.Session,
    statements: List[Dict],
    update_tag: int,
) -> None:
    ingest_policy_statement = """
        UNWIND $Statements as statement_data
        MERGE (statement:S3PolicyStatement{id: statement_data.statement_id})
        ON CREATE SET statement.firstseen = timestamp()
        SET
        statement.policy_id = statement_data.policy_id,
        statement.policy_version = statement_data.policy_version,
        statement.bucket = statement_data.bucket,
        statement.sid = statement_data.Sid,
        statement.effect = statement_data.Effect,
        statement.action = statement_data.Action,
        statement.resource = statement_data.Resource,
        statement.principal = statement_data.Principal,
        statement.condition = statement_data.Condition,
        statement.lastupdated = $UpdateTag
        WITH statement
        MATCH (bucket:S3Bucket) where bucket.name = statement.bucket
        MERGE (bucket)-[r:POLICY_STATEMENT]->(statement)
        SET r.lastupdated = $UpdateTag
        """
    run_write_query(
        neo4j_session,
        ingest_policy_statement,
        Statements=statements,
        UpdateTag=update_tag,
    )


@timeit
def _load_s3_encryption(
    neo4j_session: neo4j.Session,
    encryption_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 default encryption results into neo4j.
    """
    # NOTE we use the coalesce function so appending works when the value is null initially
    ingest_encryption = """
    UNWIND $encryption_configs AS encryption
    MATCH (s:S3Bucket) where s.name = encryption.bucket
    SET s.default_encryption = (coalesce(s.default_encryption, false) OR encryption.default_encryption),
    s.encryption_algorithm = encryption.encryption_algorithm,
    s.encryption_key_id = encryption.encryption_key_id, s.bucket_key_enabled = encryption.bucket_key_enabled,
    s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_encryption,
        encryption_configs=encryption_configs,
        UpdateTag=update_tag,
    )


@timeit
def _load_s3_versioning(
    neo4j_session: neo4j.Session,
    versioning_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 versioning results into neo4j.
    """
    ingest_versioning = """
    UNWIND $versioning_configs AS versioning
    MATCH (s:S3Bucket) where s.name = versioning.bucket
    SET s.versioning_status = versioning.status,
        s.mfa_delete = versioning.mfa_delete,
        s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_versioning,
        versioning_configs=versioning_configs,
        UpdateTag=update_tag,
    )


@timeit
def _load_s3_public_access_block(
    neo4j_session: neo4j.Session,
    public_access_block_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 public access block results into neo4j.
    """
    ingest_public_access_block = """
    UNWIND $public_access_block_configs AS public_access_block
    MATCH (s:S3Bucket) where s.name = public_access_block.bucket
    SET s.block_public_acls = public_access_block.block_public_acls,
        s.ignore_public_acls = public_access_block.ignore_public_acls,
        s.block_public_policy = public_access_block.block_public_policy,
        s.restrict_public_buckets = public_access_block.restrict_public_buckets,
        s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_public_access_block,
        public_access_block_configs=public_access_block_configs,
        UpdateTag=update_tag,
    )


@timeit
def _load_bucket_ownership_controls(
    neo4j_session: neo4j.Session,
    bucket_ownership_controls_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 BucketOwnershipControls results into neo4j.
    """
    ingest_bucket_ownership_controls = """
    UNWIND $bucket_ownership_controls_configs AS bucket_ownership_controls
    MATCH (s:S3Bucket) where s.name = bucket_ownership_controls.bucket
    SET s.object_ownership = bucket_ownership_controls.object_ownership,
        s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        ingest_bucket_ownership_controls,
        bucket_ownership_controls_configs=bucket_ownership_controls_configs,
        UpdateTag=update_tag,
    )


@timeit
def _load_bucket_logging(
    neo4j_session: neo4j.Session,
    bucket_logging_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 bucket logging status configuration into neo4j.
    """
    # Load basic logging status
    ingest_bucket_logging = """
    UNWIND $bucket_logging_configs AS bucket_logging
    MATCH (bucket:S3Bucket{name: bucket_logging.bucket})
    SET bucket.logging_enabled = bucket_logging.logging_enabled,
        bucket.logging_target_bucket = bucket_logging.target_bucket,
        bucket.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        ingest_bucket_logging,
        bucket_logging_configs=bucket_logging_configs,
        update_tag=update_tag,
    )


def _set_default_values(neo4j_session: neo4j.Session, aws_account_id: str) -> None:
    set_defaults = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(s:S3Bucket) where s.anonymous_actions IS NULL
    SET s.anonymous_access = false, s.anonymous_actions = []
    """
    run_write_query(
        neo4j_session,
        set_defaults,
        AWS_ID=aws_account_id,
    )

    set_encryption_defaults = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(s:S3Bucket) where s.default_encryption IS NULL
    SET s.default_encryption = false
    """
    run_write_query(
        neo4j_session,
        set_encryption_defaults,
        AWS_ID=aws_account_id,
    )


@timeit
def load_s3_details(
    neo4j_session: neo4j.Session,
    s3_details_iter: Generator[Any, Any, Any],
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionaries for all bucket ACLs and all bucket policies so we can import them in a single query for each
    """
    acls: List[Dict] = []
    policies: List[Dict] = []
    statements = []
    encryption_configs: List[Dict] = []
    versioning_configs: List[Dict] = []
    public_access_block_configs: List[Dict] = []
    bucket_ownership_controls_configs: List[Dict] = []
    bucket_logging_configs: List[Dict] = []
    for (
        bucket,
        acl,
        policy,
        encryption,
        versioning,
        public_access_block,
        bucket_ownership_controls,
        bucket_logging,
    ) in s3_details_iter:
        parsed_acls = parse_acl(acl, bucket, aws_account_id)
        if parsed_acls is not None:
            acls.extend(parsed_acls)
        parsed_policy = parse_policy(bucket, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)
        parsed_statements = parse_policy_statements(bucket, policy)
        if parsed_statements is not None:
            statements.extend(parsed_statements)
        parsed_encryption = parse_encryption(bucket, encryption)
        if parsed_encryption is not None:
            encryption_configs.append(parsed_encryption)
        parsed_versioning = parse_versioning(bucket, versioning)
        if parsed_versioning is not None:
            versioning_configs.append(parsed_versioning)
        parsed_public_access_block = parse_public_access_block(
            bucket,
            public_access_block,
        )
        if parsed_public_access_block is not None:
            public_access_block_configs.append(parsed_public_access_block)
        parsed_bucket_ownership_controls = parse_bucket_ownership_controls(
            bucket, bucket_ownership_controls
        )
        if parsed_bucket_ownership_controls is not None:
            bucket_ownership_controls_configs.append(parsed_bucket_ownership_controls)
        parsed_bucket_logging = parse_bucket_logging(bucket, bucket_logging)
        if parsed_bucket_logging is not None:
            bucket_logging_configs.append(parsed_bucket_logging)

    # cleanup existing policy properties set on S3 Buckets
    run_cleanup_job(
        "aws_s3_details.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id},
    )

    _load_s3_acls(neo4j_session, acls, aws_account_id, update_tag)

    _load_s3_policies(neo4j_session, policies, update_tag)
    _load_s3_policy_statements(neo4j_session, statements, update_tag)
    _load_s3_encryption(neo4j_session, encryption_configs, update_tag)
    _load_s3_versioning(neo4j_session, versioning_configs, update_tag)
    _load_s3_public_access_block(neo4j_session, public_access_block_configs, update_tag)
    _load_bucket_ownership_controls(
        neo4j_session, bucket_ownership_controls_configs, update_tag
    )
    _load_bucket_logging(neo4j_session, bucket_logging_configs, update_tag)
    _set_default_values(neo4j_session, aws_account_id)


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


@timeit
def load_s3_buckets(
    neo4j_session: neo4j.Session,
    data: Dict,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_bucket = """
    MERGE (bucket:S3Bucket{id:$BucketName})
    ON CREATE SET bucket.firstseen = timestamp(), bucket.creationdate = $CreationDate
    SET bucket.name = $BucketName, bucket.region = $BucketRegion, bucket.arn = $Arn,
    bucket.lastupdated = $aws_update_tag
    WITH bucket
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    # The owner data returned by the API maps to the aws account nickname and not the IAM user
    # there doesn't seem to be a way to retreive the mapping but we can get the current context account
    # so we map to that directly

    for bucket in data["Buckets"]:
        arn = "arn:aws:s3:::" + bucket["Name"]
        run_write_query(
            neo4j_session,
            ingest_bucket,
            BucketName=bucket["Name"],
            BucketRegion=bucket["Region"],
            Arn=arn,
            CreationDate=str(bucket["CreationDate"]),
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_s3_buckets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_s3_buckets_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_s3_bucket_acl_and_policy(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_s3_acl_cleanup.json",
        neo4j_session,
        common_job_parameters,
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
    1. Basic bucket information
    2. ACLs and policies
    3. Notification configurations
    """
    logger.info("Syncing S3 for account '%s'", current_aws_account_id)

    bucket_data = get_s3_bucket_list(boto3_session)
    load_s3_buckets(neo4j_session, bucket_data, current_aws_account_id, update_tag)
    cleanup_s3_buckets(neo4j_session, common_job_parameters)

    acl_and_policy_data_iter = get_s3_bucket_details(boto3_session, bucket_data)
    load_s3_details(
        neo4j_session,
        acl_and_policy_data_iter,
        current_aws_account_id,
        update_tag,
    )
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
