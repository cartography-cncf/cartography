"""
AWS GovCloud (US) copies of shared AWS fixtures.

AWS returns every ARN in GovCloud with the "aws-us-gov" partition. These copies keep the
commercial fixtures' structure and change only the partition and the region, so a GovCloud test
and its commercial counterpart cannot drift apart.
"""

import json
from typing import Any

from tests.data.aws import bedrock
from tests.data.aws import cloudtrail_management_events
from tests.data.aws import rds
from tests.data.aws import redshift

GOV_REGION = "us-gov-west-1"


def to_govcloud(data: Any) -> Any:
    """Return a copy of data with every commercial ARN and us-east-1 region moved to GovCloud."""
    if isinstance(data, str):
        return data.replace("arn:aws:", "arn:aws-us-gov:").replace(
            "us-east-1", GOV_REGION
        )
    if isinstance(data, dict):
        return {key: to_govcloud(value) for key, value in data.items()}
    if isinstance(data, list):
        return [to_govcloud(value) for value in data]
    return data


DESCRIBE_DBINSTANCES_RESPONSE = to_govcloud(rds.DESCRIBE_DBINSTANCES_RESPONSE)

REDSHIFT_CLUSTERS = to_govcloud(redshift.CLUSTERS)

# The ARNs that the GovCloud resource groups tagging API returns for the resources above.
GET_RESOURCES_RESPONSE = [
    {
        "ResourceARN": f"arn:aws-us-gov:rds:{GOV_REGION}:000000000000:subgrp:subnet-group-1",
        "Tags": [{"Key": "TestKey", "Value": "TestValue"}],
    },
    {
        "ResourceARN": f"arn:aws-us-gov:redshift:{GOV_REGION}:1111:cluster:my-cluster",
        "Tags": [{"Key": "TestKey", "Value": "TestValue"}],
    },
]

INTEGRATION_TEST_BASIC_IAM_USERS = to_govcloud(
    cloudtrail_management_events.INTEGRATION_TEST_BASIC_IAM_USERS,
)
INTEGRATION_TEST_BASIC_IAM_ROLES = to_govcloud(
    cloudtrail_management_events.INTEGRATION_TEST_BASIC_IAM_ROLES,
)
# A role session assumes a second role. CloudTrail names the caller by its STS
# assumed-role ARN, which the sync must map back to the IAM role in the same partition.
ROLE_CHAINING_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T10:30:15.123000",
        "UserIdentity": {
            "arn": "arn:aws-us-gov:sts::123456789012:assumed-role/ApplicationRole/session-1",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws-us-gov:iam::123456789012:role/SAMLRole",
                "AccountId": "123456789012",
            },
        ],
        "CloudTrailEvent": json.dumps(
            {
                "userIdentity": {
                    "arn": "arn:aws-us-gov:sts::123456789012:assumed-role/ApplicationRole/session-1",
                },
                "requestParameters": {
                    "roleArn": "arn:aws-us-gov:iam::123456789012:role/SAMLRole",
                },
            },
        ),
    },
]

BEDROCK_FOUNDATION_MODELS = to_govcloud(bedrock.FOUNDATION_MODELS)
BEDROCK_GUARDRAILS = to_govcloud(bedrock.GUARDRAILS)
BEDROCK_KNOWLEDGE_BASES = to_govcloud(bedrock.KNOWLEDGE_BASES)
# Agents name their foundation model by model id, and their guardrail and knowledge base by
# id. Cartography builds the ARNs of those targets itself, so the agent data needs no change.
BEDROCK_AGENTS = to_govcloud(bedrock.AGENTS)
