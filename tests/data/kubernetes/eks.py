# Mock data for EKS integration tests

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

# Test constants
TEST_CLUSTER_NAME = "test-cluster"
TEST_CLUSTER_ID = "test-cluster-id-12345"
TEST_UPDATE_TAG = 123456789
TEST_ACCOUNT_ID = "123456789012"
