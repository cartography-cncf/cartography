# Define test data for Opal AWS resources

RESOURCE_DATA = [
    {
        'resource_id': 'test_resource_1',
        'name': 'Test Resource 1',
        'type': 'OpalResourceType',
        # Add other necessary fields
    },
    {
        'resource_id': 'test_resource_2',
        'name': 'Test Resource 2',
        'type': 'OpalResourceType',
        # Add other necessary fields
    },
]
# Define test data for parse_opal_resource_access_configuration

OPAL_RESOURCES = [
    {
        'resource_id': 'resource_1',
        'request_configurations': [
            {
                'auto_approval': True,
                'condition': {
                    'group_ids': ['group_1', 'group_2'],
                },
            },
            {
                'auto_approval': False,
                'reviewer_stages': [
                    {'owner_ids': ['owner_1', 'owner_2']},
                ],
            },
        ],
    },
    {
        'resource_id': 'resource_2',
        'request_configurations': [
            {
                'auto_approval': True,
                'condition': {
                    'group_ids': ['group_3'],
                },
            },
            {
                'auto_approval': False,
                'reviewer_stages': [
                    {'owner_ids': ['owner_1']},
                    {'owner_ids': ['owner_4']},
                ],
            },
        ],
    },
]

OPAL_TO_OKTA_MAP = {
    'group_1': 'okta_group_1',
    'group_2': 'okta_group_2',
    'group_3': 'okta_group_3',
}

OPAL_ADMIN_TO_OKTA_MAP = {
    'owner_1': 'okta_group_4',
    'owner_2': 'okta_group_5',
    'owner_4': 'okta_group_6',
}
# Define test data for AWS permission set resources
AWS_PERMISSION_SET_RESOURCES = [
    {
        'resource_id': 'resource_1',
        'remote_id': 'arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-12345678901234567',
        'remote_account_id': '123456789012',
    },
    {
        'resource_id': 'resource_2',
        'remote_id': 'arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-23456789012345678',
        'remote_account_id': '234567890123',
    },
]
