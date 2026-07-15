# AWS Configuration

## Prerequisites

Configure `~/.aws/credentials` and `~/.aws/config` for the AWS identities that
Cartography should use. Cartography follows the standard boto3 credential
resolution order.

For AWS Organizations hierarchy data, include credentials for the management
account or a delegated administrator account.

## Authentication

### Single Account

Configure credentials for an AWS user or role. A single-account sync uses
boto3's normal credential resolution behavior.

### Multiple Accounts

The recommended setup is one named AWS profile for each account and
`--aws-sync-all-profiles`.

For a hub-and-spoke deployment on EC2:

1. Create a `cartography-read-only` role in every account.
2. Allow the hub account to assume that role in each spoke account.
3. Create a `cartography-service` role in the hub account that can call
   `sts:AssumeRole` on `arn:aws:iam::*:role/cartography-read-only` and
   `ec2:DescribeRegions`.
4. Attach `cartography-service` to the EC2 instance running Cartography.
5. Add a profile for each account to the AWS config file:

   ```ini
   [profile accountname1]
   role_arn = arn:aws:iam::<AccountId#1>:role/cartography-read-only
   region = us-east-1
   output = json
   credential_source = Ec2InstanceMetadata

   [profile accountname2]
   role_arn = arn:aws:iam::<AccountId#2>:role/cartography-read-only
   region = us-west-1
   output = json
   credential_source = Ec2InstanceMetadata
   ```

The spoke role trust relationship should allow the hub account to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<HubAccountId>:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Required Permissions

Attach the AWS managed
[SecurityAudit policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor)
(`arn:aws:iam::aws:policy/SecurityAudit`) to every identity or
`cartography-read-only` role used by Cartography.

Full AWS Organizations hierarchy enumeration requires credentials from the
management account or a delegated administrator account. Grant
`organizations:Describe*` and `organizations:List*` permissions. The managed
`SecurityAudit` policy includes these actions, but member accounts cannot call
hierarchy APIs such as `ListRoots`, `ListAccountsForParent`, and
`ListOrganizationalUnitsForParent`.

## Optional Permissions

- Inspector ingestion requires the
  [AmazonInspector2ReadOnlyAccess policy](https://docs.aws.amazon.com/inspector/latest/user/security-iam-awsmanpol.html#security-iam-awsmanpol-AmazonInspector2ReadOnlyAccess).
- Allowlisted AWS-managed public SSM parameters require
  `ssm:GetParametersByPath` for the applicable `/aws/service/...` paths.
- The `ecr:pull_through_cache_rules` requested sync requires
  `ecr:DescribePullThroughCacheRules`.

## Configure Cartography

For a single account, no AWS-specific selection flag is required after
configuring credentials.

For multiple accounts, use `--aws-sync-all-profiles`. To make Organizations
discovery predictable at scale, pass the management or delegated
administrator account ID with `--aws-organization-account-ids`.

## Run Cartography

Run a single-account sync:

```bash
cartography --selected-modules aws
```

Run all configured profiles and use a specific Organizations account:

```bash
cartography \
  --selected-modules aws \
  --aws-sync-all-profiles \
  --aws-organization-account-ids 123456789012
```

## Advanced Configuration

### Selective Syncing

Use `--aws-requested-syncs` with a comma-separated list of resource
identifiers to limit the resource types that Cartography syncs. Cartography
handles resource dependencies and sync order.

```bash
cartography \
  --selected-modules aws \
  --aws-requested-syncs "ec2:instance,s3,iam"
```

Additional examples:

```bash
cartography --selected-modules aws --aws-requested-syncs "ecr,lambda_function"
cartography --selected-modules aws --aws-requested-syncs "ecr:pull_through_cache_rules"
```

For the current identifier list, see the `RESOURCE_FUNCTIONS` dictionary in
`cartography/intel/aws/resources.py`.

### Retry and Timeout Settings

Cartography-managed AWS clients use these environment variables:

- `CARTOGRAPHY_AWS_RETRY_MODE`: `standard`, `adaptive`, or `legacy`. The
  default is `standard`.
- `CARTOGRAPHY_AWS_MAX_ATTEMPTS`: Maximum retry attempts. The default is `3`.
- `CARTOGRAPHY_AWS_READ_TIMEOUT`: Read timeout in seconds. The default is
  `120`.

Lambda regional calls use a 30-second read timeout and two attempts while
inheriting the shared retry mode. These settings take precedence over ambient
AWS retry environment variables for clients configured by Cartography.

### Regional STS Endpoints

To avoid `InvalidToken` errors when assuming roles across regions, add
`sts_regional_endpoints = regional` to the AWS config file or set
`AWS_STS_REGIONAL_ENDPOINTS=regional`.

## Troubleshooting

If hierarchy APIs are unavailable, Cartography skips AWS Organizations cleanup
and continues account resource sync. Verify that the selected Organizations
account is the management account or a delegated administrator and can
enumerate the complete hierarchy.

## References

- [AWS shared configuration files](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html)
- [AWS CLI environment variables](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html)
- [boto3 credential resolution](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)
- [AWS regional STS endpoints](https://docs.aws.amazon.com/sdkref/latest/guide/feature-sts-regionalized-endpoints.html)
