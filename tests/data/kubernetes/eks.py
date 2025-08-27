# Mock data for EKS integration tests

# Test constants (defined first since they're used in other mock data)
TEST_CLUSTER_NAME = "test-cluster"
TEST_CLUSTER_ID = "test-cluster-id-12345"
TEST_UPDATE_TAG = 123456789
TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-west-2"

# Sample aws-auth ConfigMap data that would be found in an EKS cluster
AWS_AUTH_CONFIGMAP_DATA = {
    "mapRoles": """
- rolearn: arn:aws:iam::123456789012:role/EKSNodeRole
  username: system:node:{{EC2PrivateDNSName}}
  groups:
  - system:bootstrappers
  - system:nodes
- rolearn: arn:aws:iam::123456789012:role/EKSDevRole
  username: dev-user
  groups:
  - developers
  - staging-access
- rolearn: arn:aws:iam::123456789012:role/EKSAdminRole
  username: admin-user
  groups:
  - system:masters
- rolearn: arn:aws:iam::123456789012:role/EKSViewerRole
  username: viewer-user
  groups:
  - view-only
  - read-access
- rolearn: arn:aws:iam::123456789012:role/EKSGroupOnlyRole
  groups:
  - ci-cd
  - automation
- rolearn: arn:aws:iam::123456789012:role/EKSTemplatedRole
  username: templated-user-{{AccountID}}
  groups:
  - templated-group-{{AccountID}}
  - system:authenticated
- rolearn: arn:aws:iam::123456789012:role/EKSSessionNameRawRole
  username: admin:{{SessionNameRaw}}
  groups:
  - system:masters
  - session-group:{{SessionNameRaw}}
- rolearn: arn:aws:iam::123456789012:role/EKSPureSessionNameRawRole
  username: "{{SessionNameRaw}}"
  groups:
  - federated-users
- rolearn: arn:aws:iam::123456789012:role/EKSMixedTemplateRole
  username: user-{{AccountID}}-{{SessionNameRaw}}
  groups:
  - mixed-group-{{AccountID}}-{{SessionNameRaw}}
  - system:authenticated
- rolearn: arn:aws:iam::123456789012:role/EKSSessionNameRole
  username: admin:{{SessionName}}
  groups:
  - system:masters
  - session-group:{{SessionName}}
- rolearn: arn:aws:iam::123456789012:role/EKSPureSessionNameRole
  username: "{{SessionName}}"
  groups:
  - federated-users
- rolearn: arn:aws:iam::123456789012:role/EKSMixedSessionNameRole
  username: user-{{AccountID}}-{{SessionName}}
  groups:
  - mixed-group-{{AccountID}}-{{SessionName}}
  - system:authenticated
""",
    "mapUsers": """
- userarn: arn:aws:iam::123456789012:user/alice
  username: alice-user
  groups:
  - developers
  - qa-access
- userarn: arn:aws:iam::123456789012:user/bob
  username: bob-user
  groups:
  - system:masters
- userarn: arn:aws:iam::123456789012:user/charlie
  groups:
  - read-only
  - monitoring
- userarn: arn:aws:iam::123456789012:user/templated-user
  username: service-{{AccountID}}
  groups:
  - templated-access-{{AccountID}}
- userarn: arn:aws:iam::123456789012:user/session-user
  username: svc:{{SessionNameRaw}}
  groups:
  - service-accounts
- userarn: arn:aws:iam::123456789012:user/session-name-user
  username: svc:{{SessionName}}
  groups:
  - service-accounts
""",
    "mapAccounts": """
- "123456789012"
- "999888777666"
""",
}


# Mock AWS Role data that should exist in the graph before EKS sync
MOCK_AWS_ROLES = [
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSDevRole",
        "RoleName": "EKSDevRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI789",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSAdminRole",
        "RoleName": "EKSAdminRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI790",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSViewerRole",
        "RoleName": "EKSViewerRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI791",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSGroupOnlyRole",
        "RoleName": "EKSGroupOnlyRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI792",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSTemplatedRole",
        "RoleName": "EKSTemplatedRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI793",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
        "RoleName": "EKSSessionNameRawRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI794",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSPureSessionNameRawRole",
        "RoleName": "EKSPureSessionNameRawRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI795",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
        "RoleName": "EKSMixedTemplateRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI796",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSSessionNameRole",
        "RoleName": "EKSSessionNameRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI797",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSPureSessionNameRole",
        "RoleName": "EKSPureSessionNameRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI798",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
        "RoleName": "EKSMixedSessionNameRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI799",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
]

# Mock AWS User data that should exist in the graph before EKS sync
MOCK_AWS_USERS = [
    {
        "Arn": "arn:aws:iam::123456789012:user/alice",
        "UserName": "alice",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI789",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
    {
        "Arn": "arn:aws:iam::123456789012:user/bob",
        "UserName": "bob",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI790",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
    {
        "Arn": "arn:aws:iam::123456789012:user/charlie",
        "UserName": "charlie",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI791",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
    {
        "Arn": "arn:aws:iam::123456789012:user/templated-user",
        "UserName": "templated-user",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI792",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
    {
        "Arn": "arn:aws:iam::123456789012:user/session-user",
        "UserName": "session-user",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI789",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
    {
        "Arn": "arn:aws:iam::123456789012:user/session-name-user",
        "UserName": "session-name-user",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI790",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
]

# Mock OIDC provider data (raw AWS API responses)
MOCK_OIDC_PROVIDERS = [
    {
        "identityProviderConfigName": "auth0-provider",
        "issuerUrl": "https://company.auth0.com/",
        "clientId": "abc123def456",
        "usernamePrefix": "auth0:",
        "groupsPrefix": "auth0:",
        "status": "ACTIVE",
        "identityProviderConfigArn": "arn:aws:eks:us-west-2:123456789012:identityproviderconfig/test-cluster/oidc/auth0-provider/12345",
    },
    {
        "identityProviderConfigName": "okta-provider",
        "issuerUrl": "https://company.okta.com/oauth2/default",
        "clientId": "xyz789ghi012",
        "usernamePrefix": "okta:",
        "groupsPrefix": "okta:",
        "status": "ACTIVE",
        "identityProviderConfigArn": "arn:aws:eks:us-west-2:123456789012:identityproviderconfig/test-cluster/oidc/okta-provider/67890",
    },
]


# Mock cluster data for testing
MOCK_CLUSTER_DATA = [
    {
        "id": TEST_CLUSTER_ID,
        "name": TEST_CLUSTER_NAME,
        "external_id": f"arn:aws:eks:{TEST_REGION}:{TEST_ACCOUNT_ID}:cluster/{TEST_CLUSTER_NAME}",
        "git_version": "v1.24.0",
        "version_major": "1",
        "version_minor": "24",
        "go_version": "go1.19.0",
        "compiler": "gc",
        "platform": "linux/amd64",
        "creation_timestamp": 1234567890,
    }
]

# Mock Kubernetes Users that would be discovered from role bindings (for mapAccounts testing)
# These represent users whose names are ARNs from the allowed accounts
MOCK_KUBERNETES_USERS_FROM_RBAC = [
    {
        "id": "test-cluster/arn:aws:iam::123456789012:role/ProductionRole",
        "name": "arn:aws:iam::123456789012:role/ProductionRole",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/arn:aws:iam::123456789012:user/service-account-user",
        "name": "arn:aws:iam::123456789012:user/service-account-user",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/arn:aws:iam::999888777666:role/CrossAccountRole",
        "name": "arn:aws:iam::999888777666:role/CrossAccountRole",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/regular-user@company.com",  # This should NOT match (not an ARN)
        "name": "regular-user@company.com",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/arn:aws:iam::111222333444:role/DisallowedAccountRole",  # This should NOT match (wrong account)
        "name": "arn:aws:iam::111222333444:role/DisallowedAccountRole",
        "cluster_name": "test-cluster",
    },
    # SessionNameRaw template test users - these should match our templates
    {
        "id": "test-cluster/admin:alice",  # Should match admin:{{SessionNameRaw}}
        "name": "admin:alice",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/admin:bob@company.com",  # Should match admin:{{SessionNameRaw}}
        "name": "admin:bob@company.com",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/charlie",  # Should match {{SessionNameRaw}} (pure template)
        "name": "charlie",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/dave.smith",  # Should match {{SessionNameRaw}} (pure template)
        "name": "dave.smith",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/svc:automation",  # Should match svc:{{SessionNameRaw}}
        "name": "svc:automation",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/svc:monitoring@company.com",  # Should match svc:{{SessionNameRaw}}
        "name": "svc:monitoring@company.com",
        "cluster_name": "test-cluster",
    },
    # Mixed template test users - should match user-{{AccountID}}-{{SessionNameRaw}}
    {
        "id": "test-cluster/user-123456789012-alice",  # Should match user-{{AccountID}}-{{SessionNameRaw}}
        "name": "user-123456789012-alice",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/user-123456789012-bob@company.com",  # Should match user-{{AccountID}}-{{SessionNameRaw}}
        "name": "user-123456789012-bob@company.com",
        "cluster_name": "test-cluster",
    },
    # SessionName template test users - should match transliterated names
    {
        "id": "test-cluster/admin:alice-company-com",  # Should match admin:{{SessionName}} (transliterated)
        "name": "admin:alice-company-com",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/admin:bob-example-org",  # Should match admin:{{SessionName}} (transliterated)
        "name": "admin:bob-example-org",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/charlie-smith",  # Should match {{SessionName}} (transliterated)
        "name": "charlie-smith",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/dave-jones",  # Should match {{SessionName}} (transliterated)
        "name": "dave-jones",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/svc:automation-service",  # Should match svc:{{SessionName}} (transliterated)
        "name": "svc:automation-service",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/svc:monitoring-prod",  # Should match svc:{{SessionName}} (transliterated)
        "name": "svc:monitoring-prod",
        "cluster_name": "test-cluster",
    },
    # Mixed SessionName template test users - should match user-{{AccountID}}-{{SessionName}}
    {
        "id": "test-cluster/user-123456789012-alice-company-com",  # Should match user-{{AccountID}}-{{SessionName}}
        "name": "user-123456789012-alice-company-com",
        "cluster_name": "test-cluster",
    },
    {
        "id": "test-cluster/user-123456789012-bob-example-org",  # Should match user-{{AccountID}}-{{SessionName}}
        "name": "user-123456789012-bob-example-org",
        "cluster_name": "test-cluster",
    },
]

# Additional AWS roles/users for mapAccounts testing (should exist in graph)
MOCK_ADDITIONAL_AWS_ROLES = [
    {
        "Arn": "arn:aws:iam::123456789012:role/ProductionRole",
        "RoleName": "ProductionRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI800",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
    {
        "Arn": "arn:aws:iam::999888777666:role/CrossAccountRole",
        "RoleName": "CrossAccountRole",
        "Path": "/",
        "RoleId": "AROABC123DEF456GHI801",
        "CreateDate": "2023-01-01T00:00:00Z",
        "MaxSessionDuration": 3600,
        "AssumeRolePolicyDocument": {"Statement": []},
    },
]

MOCK_ADDITIONAL_AWS_USERS = [
    {
        "Arn": "arn:aws:iam::123456789012:user/service-account-user",
        "UserName": "service-account-user",
        "Path": "/",
        "UserId": "AIDABC123DEF456GHI800",
        "CreateDate": "2023-01-01T00:00:00Z",
    },
]
