## AWS Configuration


Follow these steps to analyze AWS assets with Cartography.

In a nutshell, Cartography uses the [boto3](https://github.com/boto/boto3) library to retrieve assets from AWS and follows boto3's normal credential resolution behavior. For retry behavior, Cartography now constructs its own shared botocore config for AWS clients, so Cartography-specific retry environment variables take precedence over ambient AWS retry env vars. If you've used boto3 before, then you're already very familiar with setting up Cartography for AWS.

Cartography supports single-account AWS syncs and multi-account AWS syncs. For AWS Organizations hierarchy data, the recommended setup is a multi-account sync that includes the AWS Organizations management account or a delegated administrator account.

### Very helpful references
- Ensure your ~/.aws/credentials and ~/.aws/config files are set up correctly: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html
- Review the various AWS environment variables: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html
- Refer to boto3's standard order of precedence when retrieving credentials: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials

### Single AWS Account Setup

1. Set up an AWS identity (user, group, or role) for Cartography to use. Ensure that this identity has the built-in AWS [SecurityAudit policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) attached. This policy grants access to read security config metadata.
   1. If you want to use AWS Inspector, the SecurityAudit policy does not yet contain permissions for `inspector2`, so you will also need the [AmazonInspector2ReadOnlyAccess policy](https://docs.aws.amazon.com/inspector/latest/user/security-iam-awsmanpol.html#security-iam-awsmanpol-AmazonInspector2ReadOnlyAccess).
1. Set up AWS credentials to this identity on your server, using a `config` and `credential` file.  For details, see AWS' [official guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
1. [Optional] Configure Cartography's shared AWS client retry behavior with these environment variables:
   - `CARTOGRAPHY_AWS_RETRY_MODE`: Retry mode for Cartography-managed AWS clients. Valid values are `standard`, `adaptive`, and `legacy`. Default: `standard`.
   - `CARTOGRAPHY_AWS_MAX_ATTEMPTS`: Max retry attempts for Cartography-managed AWS clients. Default: `3`.
   - `CARTOGRAPHY_AWS_READ_TIMEOUT`: Read timeout in seconds for Cartography-managed AWS clients. Default: `120`.
   - Lambda keeps narrower defaults for its own regional calls: read timeout `30` seconds and max attempts `2`, while still inheriting the shared retry mode unless explicitly overridden in code.
   These settings help with API throttling and transient regional endpoint failures. They are separate from AWS SDK env vars like `AWS_MAX_ATTEMPTS` and `AWS_RETRY_MODE`, because Cartography now builds botocore config objects itself for AWS clients.

Single-account sync uses boto3's normal credential resolution behavior. If the account is in an AWS Organization, Cartography will attempt AWS Organizations sync as best-effort enrichment. Full organization hierarchy sync and cleanup require credentials from the management account or a delegated administrator account; otherwise Cartography skips Organizations cleanup and continues the account resource sync.

### Multiple AWS Account Setup

There are many ways to allow Cartography to pull from more than one AWS account. The recommended pattern is to configure one named AWS profile per account in `~/.aws/config` and run Cartography with `--aws-sync-all-profiles`.

If you want AWS Organizations hierarchy data, include a profile for the Organizations management account or a delegated administrator account. For large environments, pass that account ID with `--aws-organization-account-ids` so Cartography can sync Organizations once without probing every configured profile.

```bash
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --aws-sync-all-profiles \
  --aws-organization-account-ids 123456789012
```

If you omit `--aws-organization-account-ids`, Cartography will use `DescribeOrganization` against the configured profiles to find candidate accounts, prefer the management account when it is present, and then try to sync the hierarchy. This fallback is useful for small environments and ad hoc runs, but explicit organization account IDs are more predictable at scale.

In this example, we will assume that you are going to run Cartography on an EC2 instance.

1. Pick one of your AWS accounts to be the "**Hub**" account.  This Hub account will pull data from all of your other accounts - we'll call those "**Spoke**" accounts.

2. **Set up the IAM roles**: Create an IAM role named `cartography-read-only` on _all_ of your accounts.  Configure the role on all accounts as follows:
	1. Attach the built-in AWS [SecurityAudit IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) to the role.  This grants access to read security config metadata.
	2. Set up a trust relationship so that the Spoke accounts will allow the Hub account to assume the `cartography-read-only` role.  The resulting trust relationship should look something like this:

		```
		{
		  "Version": "2012-10-17",
		  "Statement": [
		    {
		      "Effect": "Allow",
		      "Principal": {
		        "AWS": "arn:aws:iam::<Hub's account number>:root"
		      },
		      "Action": "sts:AssumeRole"
		    }
		  ]
		}
		```
	3. Allow a role in the Hub account to **assume the `cartography-read-only` role** on your Spoke account(s).

		- On the Hub account, create a role called `cartography-service`.
		- On this new `cartography-service` role, add an inline policy with the following JSON:

			```
			{
			  "Version": "2012-10-17",
			  "Statement": [
			    {
			      "Effect": "Allow",
			      "Resource": "arn:aws:iam::*:role/cartography-read-only",
			      "Action": "sts:AssumeRole"
			    },
				{
				  "Effect": "Allow",
				  "Action": "ec2:DescribeRegions",
				  "Resource": "*"
				}
			  ]
			}
			```

			This allows the Hub role to assume the `cartography-read-only` role on your Spoke accounts and to fetch all the different regions used by the Spoke accounts.

		- When prompted to name the policy, you can name it anything you want - perhaps `CartographyAssumeRolePolicy`.

3. **Set up your EC2 instance to correctly access these AWS identities**

	1. Attach the `cartography-service` role to the EC2 instance that you will run Cartography on.  You can do this by following [these official AWS steps](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#attach-iam-role).

	2. Ensure that the `[default]` profile in your `AWS_CONFIG_FILE` file (default `~/.aws/config` in Linux, and `%UserProfile%\.aws\config` in Windows) looks like this:

			[default]
			region=<the region of your Hub account, e.g. us-east-1>
			output=json

	3.  Add a profile for each AWS account you want Cartography to sync with to your `AWS_CONFIG_FILE`.  It will look something like this:

		```
		[profile accountname1]
		role_arn = arn:aws:iam::<AccountId#1>:role/cartography-read-only
		region=us-east-1
		output=json
		credential_source = Ec2InstanceMetadata

		[profile accountname2]
		role_arn = arn:aws:iam::<AccountId#2>:role/cartography-read-only
		region=us-west-1
		output=json
		credential_source = Ec2InstanceMetadata

		... etc ...
		```
1. [Optional] Configure Cartography's shared AWS client retry behavior with:
   - `CARTOGRAPHY_AWS_RETRY_MODE`
   - `CARTOGRAPHY_AWS_MAX_ATTEMPTS`
   - `CARTOGRAPHY_AWS_READ_TIMEOUT`
   Default values and behavior are described in the single-account setup section above. These Cartography env vars control the botocore config objects Cartography builds for AWS clients.
1. [Optional] Use regional STS endpoints to avoid `InvalidToken` errors when assuming roles across regions. Add `sts_regional_endpoints = regional` to your AWS config file or set the `AWS_STS_REGIONAL_ENDPOINTS=regional` environment variable. [AWS Docs](https://docs.aws.amazon.com/sdkref/latest/guide/feature-sts-regionalized-endpoints.html).

### AWS Organizations Behavior

AWS Organizations sync is separate from per-account resource sync. It models the organization, root, organizational units, and account placement before Cartography syncs normal account-scoped resources.

| Configuration | Organizations behavior | Account resource sync |
|---------------|------------------------|-----------------------|
| Single-account credentials | Attempts Organizations sync with the current credentials. If the account cannot enumerate the hierarchy, Organizations cleanup is skipped. | Syncs the current account. |
| `--aws-sync-all-profiles --aws-organization-account-ids <account-id>` | Probes only the specified Organizations sync candidate IDs, groups them by organization, prefers the management account when present, and tries candidates until one syncs each organization. | Syncs each configured profile/account. |
| `--aws-sync-all-profiles` without organization account IDs | Probes configured profiles with `DescribeOrganization`, groups candidates by organization, prefers the management account when present, and tries candidates until one syncs each organization. | Syncs each configured profile/account. |
| No usable Organizations-enumerating account | Skips Organizations hierarchy writes and cleanup to preserve prior hierarchy data. | Continues account resource sync. |

AWS's managed `SecurityAudit` policy currently includes `organizations:Describe*` and `organizations:List*`, but the policy alone is not enough for full hierarchy enumeration. AWS Organizations allows `DescribeOrganization` from any member account, while hierarchy APIs such as `ListRoots`, `ListAccountsForParent`, and `ListOrganizationalUnitsForParent` require the management account or a delegated administrator account. Cartography only runs Organizations hierarchy cleanup after a complete hierarchy enumeration.

### Selective Syncing with `--aws-requested-syncs`

By default, Cartography syncs all available AWS resource types. If you want to sync only specific AWS resources, you can use the `--aws-requested-syncs` command-line flag. This accepts a comma-separated list of resource identifiers.

#### Usage Examples

Sync only EC2 instances, S3 buckets, and IAM resources:
```bash
cartography --neo4j-uri bolt://localhost:7687 --aws-requested-syncs "ec2:instance,s3,iam"
```

Sync only ECR and Lambda:
```bash
cartography --neo4j-uri bolt://localhost:7687 --aws-requested-syncs "ecr,lambda_function"
```

Sync only ECR pull through cache rules:
```bash
cartography --neo4j-uri bolt://localhost:7687 --aws-requested-syncs "ecr:pull_through_cache_rules"
```

#### Available Resource Identifiers

For a complete and up-to-date list of resource identifiers that can be specified with `--aws-requested-syncs`, refer to the `RESOURCE_FUNCTIONS` dictionary in `cartography/cartography/intel/aws/resources.py`.

**Note**: Cartography automatically handles resource dependencies and sync order internally, so you don't need to worry about the order in which you specify resources in the list. Using `--aws-requested-syncs` can significantly reduce sync time and API calls when you only need specific resources.

#### Additional Permissions

- `ecr:pull_through_cache_rules` requires `ecr:DescribePullThroughCacheRules`.
