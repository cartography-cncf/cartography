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
"""
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
