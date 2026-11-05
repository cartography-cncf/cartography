# Tencent Cloud Configuration

Cartography reads one Tencent Cloud account with a read-only API key that belongs to
a CAM sub-user.

## Authentication

1. In the [CAM console](https://console.tencentcloud.com/cam), create a sub-user for
   Cartography with **Programmatic access** only.
1. Grant it the permissions below.
1. Under the sub-user's **API Keys** tab, create a key. Note the `SecretId` and store
   the `SecretKey` in an environment variable.

Cartography syncs the root account that owns the sub-user.

## Required Permissions

The simplest grant is the preset policy `ReadOnlyAccess`. For least privilege, attach
a custom policy with these actions instead:

```json
{
  "version": "2.0",
  "statement": [
    {
      "effect": "allow",
      "action": [
        "cam:GetUserAppId",
        "cam:ListUsers",
        "cam:ListAccessKeys",
        "cam:GetSecurityLastUsed",
        "cam:ListGroups",
        "cam:ListUsersForGroup",
        "cam:DescribeRoleList",
        "cam:ListPolicies",
        "cam:GetPolicy",
        "cam:ListAttachedUserPolicies",
        "cam:ListAttachedGroupPolicies",
        "cam:ListAttachedRolePolicies",
        "cvm:DescribeRegions",
        "cvm:DescribeInstances",
        "vpc:DescribeVpcs",
        "vpc:DescribeSubnets",
        "vpc:DescribeSecurityGroups",
        "vpc:DescribeSecurityGroupPolicies",
        "cbs:DescribeDisks",
        "clb:DescribeLoadBalancers",
        "clb:DescribeTargets",
        "cos:GetService",
        "cos:GetBucketACL"
      ],
      "resource": ["*"]
    }
  ]
}
```

| Service | Actions | Used for |
| --- | --- | --- |
| CAM | `cam:GetUserAppId` | Identifying the account that owns the key |
| CAM | `cam:ListUsers`, `cam:ListAccessKeys`, `cam:GetSecurityLastUsed` | Sub-users and their API keys |
| CAM | `cam:ListGroups`, `cam:ListUsersForGroup` | User groups and membership |
| CAM | `cam:DescribeRoleList` | Roles and their trust policies |
| CAM | `cam:ListPolicies`, `cam:GetPolicy`, `cam:ListAttached*Policies` | Policies and their attachments |
| CVM | `cvm:DescribeRegions`, `cvm:DescribeInstances` | Region discovery and instances |
| VPC | `vpc:DescribeVpcs`, `vpc:DescribeSubnets`, `vpc:DescribeSecurityGroups`, `vpc:DescribeSecurityGroupPolicies` | Networks and security groups |
| CBS | `cbs:DescribeDisks` | Cloud disks |
| CLB | `clb:DescribeLoadBalancers`, `clb:DescribeTargets` | Load balancers and their backends |
| COS | `cos:GetService` | Bucket inventory |

## Optional Permissions

| Action | Enables |
| --- | --- |
| `cos:GetBucketACL` | `anonymous_access` on COS buckets. When a bucket's ACL cannot be read, Cartography logs a warning and leaves the property unset. |

## Configure Cartography

| Option | Description |
| --- | --- |
| `--tencentcloud-secret-id` | `SecretId` of the API key. |
| `--tencentcloud-secret-key-env-var` | Name of the environment variable that holds the `SecretKey`. |
| `--tencentcloud-regions` | Optional comma-separated regions to sync, e.g. `ap-guangzhou,ap-singapore`. Defaults to every region `cvm:DescribeRegions` reports as available. CAM and COS are global and ignore this option. |

## Run Cartography

```bash
export TENCENTCLOUD_SECRET_KEY='<secret-key>'
cartography \
  --selected-modules tencentcloud \
  --tencentcloud-secret-id '<secret-id>' \
  --tencentcloud-secret-key-env-var TENCENTCLOUD_SECRET_KEY
```

## References

- [Cloud Access Management documentation](https://www.tencentcloud.com/document/product/598)
- [Tencent Cloud API documentation](https://www.tencentcloud.com/document/api)
