import datetime
import json

LIST_BUCKETS = {
    'Buckets': [
        {
            'Name': 'bucket-1',
            'CreationDate': datetime.datetime(2014, 4, 16, 18, 14, 49),
            'Region': 'eu-west-1',
        }, {
            'Name': 'bucket-2',
            'CreationDate': datetime.datetime(2015, 7, 24, 4, 8, 29),
            'Region': 'me-south-1',
        }, {
            'Name': 'bucket-3',
            'CreationDate': datetime.datetime(2019, 9, 17, 1, 16, 19),
            'Region': None,
        },
    ],
    'Owner': {
        'DisplayName': 'OWNER_NAME',
        'ID': 'OWNER_ID',
    },
}

OPEN_BUCKET_ACLS = {
    "bucket-1": {
        "Owner": {
            "DisplayName": "my-display-name-1",
            "ID": "3cb8",
        },
        "Grants": [
            {
                "Grantee": {
                    "DisplayName": "my-display-name-1",
                    "ID": "3cb8",
                    "Type": "CanonicalUser",
                },
                "Permission": "FULL_CONTROL",
            },
        ],
    },
    "bucket-2": {
        "Owner": {
            "DisplayName": "my-display-name-2",
            "ID": "828a",
        },
        "Grants": [
            {
                "Grantee": {
                    "Type": "Group",
                    "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                },
                "Permission": "READ",
            },
            {
                "Grantee": {
                    "Type": "Group",
                    "URI": "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
                },
                "Permission": "READ_ACP",
            },
        ],
    },
    "bucket-3": {
        "Owner": {
            "DisplayName": "my-display-name-2",
            "ID": "828a",
        },
        "Grants": [
            {
                "Grantee": {
                    "Type": "Group",
                    "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                },
                "Permission": "WRITE_ACP",
            },
            {
                "Grantee": {
                    "Type": "Group",
                    "URI": "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
                },
                "Permission": "WRITE",
            },
        ],
    },
}

GET_ENCRYPTION = {
    'bucket': 'bucket-1',
    'default_encryption': True,
    'encryption_algorithm': 'aws:kms',
    'encryption_key_id': 'arn:aws:kms:eu-east-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d',
    'bucket_key_enabled': False,
}

LIST_STATEMENTS = {
    'Policy': json.dumps(
        {
            "Version": "2012-10-17",
            "Id": "S3PolicyId1",
            "Statement": [
                {
                    "Sid": "IPAllow",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": [
                        "arn:aws:s3:::DOC-EXAMPLE-BUCKET",
                        "arn:aws:s3:::DOC-EXAMPLE-BUCKET/*",
                    ],
                    "Condition": {
                        "NotIpAddress": {
                            "aws:SourceIp": "54.240.143.0/24",
                        },
                    },
                },
                {
                    "Sid": "S3PolicyId2",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": "arn:aws:s3:::DOC-EXAMPLE-BUCKET/taxdocuments/*",
                    "Condition": {"Null": {"aws:MultiFactorAuthAge": True}},
                },
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": "arn:aws:s3:::DOC-EXAMPLE-BUCKET/*",
                },
            ],
        },
    ),
}
