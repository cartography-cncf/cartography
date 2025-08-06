import datetime
from typing import Any
from typing import List
from typing import Tuple

DESCRIBE_KEYS = [
    {
        "AWSAccountId": "000000000000",
        "KeyId": "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "Arn": "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "CreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "Enabled": True,
        "Description": "Testing",
        "KeyUsage": "SIGN_VERIFY",
        "KeyState": "Enabled",
        "DeletionDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "ValidTo": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "Origin": "AWS_KMS",
        "CustomKeyStoreId": "test-cks-01",
        "CloudHsmClusterId": "test-cloud-hsm-id",
        "ExpirationModel": "KEY_MATERIAL_EXPIRES",
        "KeyManager": "CUSTOMER",
        "CustomerMasterKeySpec": "RSA_2048",
        "EncryptionAlgorithms": [
            "SYMMETRIC_DEFAULT",
        ],
        "SigningAlgorithms": [
            "RSASSA_PSS_SHA_512",
        ],
    },
    {
        "AWSAccountId": "000000000000",
        "KeyId": "9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        "Arn": "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        "CreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "Enabled": True,
        "Description": "string",
        "KeyUsage": "SIGN_VERIFY",
        "KeyState": "Disabled",
        "DeletionDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "ValidTo": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "Origin": "AWS_KMS",
        "ExpirationModel": "KEY_MATERIAL_EXPIRES",
        "KeyManager": "AWS",
        "CustomerMasterKeySpec": "RSA_2048",
        "EncryptionAlgorithms": [
            "SYMMETRIC_DEFAULT",
        ],
        "SigningAlgorithms": [
            "RSASSA_PSS_SHA_256",
        ],
    },
]

DESCRIBE_ALIASES = [
    {
        "AliasName": "Cartography-A",
        "AliasArn": "arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography",
        "TargetKeyId": "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "CreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "LastUpdatedDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
    },
    {
        "AliasName": "Prod-Testing",
        "AliasArn": "arn:aws:kms:eu-west-1:000000000000:alias/key2-testing",
        "TargetKeyId": "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "CreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "LastUpdatedDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
    },
]

DESCRIBE_GRANTS = [
    {
        "KeyId": "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "GrantId": "key-consolepolicy-3",
        "Name": "Console Policy",
        "CreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
        "GranteePrincipal": "user",
        "IssuingAccount": "000000000000",
        "Operations": [
            "Encrypt",
        ],
    },
]

# Mock KMS key details data with None policy (simulating AccessDenied error)
# This simulates the data structure returned by get_kms_key_details() when get_policy() returns None
ACCESS_DENIED_KMS_KEY_DETAILS: List[Tuple[str, None, List[Any], List[Any]]] = [
    (
        "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",  # key_id
        None,  # policy - None due to AccessDenied on get_key_policy
        [],  # aliases - empty for simplicity
        [],  # grants - empty for simplicity
    ),
    (
        "1b2cd345-7e8f-49ab-cdef-0123456789ab",  # key_id
        None,  # policy - None due to AccessDenied on get_key_policy
        [],  # aliases - empty for simplicity
        [],  # grants - empty for simplicity
    ),
]
