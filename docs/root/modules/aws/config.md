## AWS Configuration


Follow these steps to analyze AWS assets with Cartography.

In a nutshell, Cartography uses the [boto3](https://github.com/boto/boto3) library to retrieve assets from AWS and respects all settings and credentials passed to boto3. If you've used boto3 before, then you're already very familiar with setting up Cartography for AWS.

### Very helpful references
- Ensure your ~/.aws/credentials and ~/.aws/config files are set up correctly: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html
- Review the various AWS environment variables: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html
- Refer to boto3's standard order of precedence when retrieving credentials: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials

### Single AWS Account Setup

1. Set up an AWS identity (user, group, or role) for Cartography to use. Ensure that this identity has the built-in AWS [SecurityAudit policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_security-auditor) (arn:aws:iam::aws:policy/SecurityAudit) attached. This policy grants access to read security config metadata.
   1. If you want to use AWS Inspector, the SecurityAudit policy does not yet contain permissions for `inspector2`, so you will also need the [AmazonInspector2ReadOnlyAccess policy](https://docs.aws.amazon.com/inspector/latest/user/security-iam-awsmanpol.html#security-iam-awsmanpol-AmazonInspector2ReadOnlyAccess).
1. Set up AWS credentials to this identity on your server, using a `config` and `credential` file.  For details, see AWS' [official guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
1. [Optional] Configure AWS Retry settings using `AWS_MAX_ATTEMPTS` and `AWS_RETRY_MODE` environment variables. This helps in API Rate Limit throttling and TooManyRequestException related errors. For details, see AWS' [official guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).

### Multiple AWS Account Setup

There are many ways to allow Cartography to pull from more than one AWS account.  We can't cover all of them, but here's one way that works at Lyft.  In this scenario we will assume that you are going to run Cartography on an EC2 instance.

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
1. [Optional] Configure AWS Retry settings using `AWS_MAX_ATTEMPTS` and `AWS_RETRY_MODE` environment variables. This helps in API Rate Limit throttling and TooManyRequestException related errors. For details, see AWS' [official guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).
1. [Optional] Use regional STS endpoints to avoid `InvalidToken` errors when assuming roles across regions. Add `sts_regional_endpoints = regional` to your AWS config file or set the `AWS_STS_REGIONAL_ENDPOINTS=regional` environment variable. [AWS Docs](https://docs.aws.amazon.com/sdkref/latest/guide/feature-sts-regionalized-endpoints.html).

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

#### Available Resource Identifiers

The following resource identifiers can be specified with `--aws-requested-syncs`:

- `acm:certificate` - AWS Certificate Manager certificates
- `apigateway` - API Gateway REST APIs
- `apigatewayv2` - API Gateway v2 (HTTP and WebSocket APIs)
- `bedrock` - Amazon Bedrock resources
- `cloudtrail` - CloudTrail trails
- `cloudtrail_management_events` - CloudTrail management events
- `cloudwatch` - CloudWatch resources
- `codebuild` - CodeBuild projects
- `cognito` - Cognito user pools
- `config` - AWS Config resources
- `dynamodb` - DynamoDB tables
- `ec2:autoscalinggroup` - EC2 Auto Scaling groups
- `ec2:images` - EC2 AMIs
- `ec2:instance` - EC2 instances
- `ec2:internet_gateway` - Internet gateways
- `ec2:keypair` - EC2 key pairs
- `ec2:launch_templates` - EC2 launch templates
- `ec2:load_balancer` - Classic Load Balancers
- `ec2:load_balancer_v2` - Application and Network Load Balancers
- `ec2:network_acls` - Network ACLs
- `ec2:network_interface` - Network interfaces
- `ec2:reserved_instances` - EC2 Reserved Instances
- `ec2:route_table` - Route tables
- `ec2:security_group` - Security groups
- `ec2:snapshots` - EBS snapshots
- `ec2:subnet` - Subnets
- `ec2:tgw` - Transit gateways
- `ec2:volumes` - EBS volumes
- `ec2:vpc` - VPCs
- `ec2:vpc_endpoint` - VPC endpoints
- `ec2:vpc_peering` - VPC peering connections
- `ecr` - Elastic Container Registry repositories
- `ecr:image_layers` - ECR image layers
- `ecs` - Elastic Container Service clusters and services
- `efs` - Elastic File System file systems
- `eks` - Elastic Kubernetes Service clusters
- `elasticache` - ElastiCache clusters
- `elastic_ip_addresses` - Elastic IP addresses
- `elasticsearch` - Elasticsearch domains
- `emr` - Elastic MapReduce clusters
- `eventbridge` - EventBridge rules
- `glue` - AWS Glue resources
- `guardduty` - GuardDuty findings
- `iam` - IAM users, groups, roles, and policies
- `iaminstanceprofiles` - IAM instance profiles
- `identitycenter` - Identity Center (AWS SSO) instances
- `inspector` - AWS Inspector findings
- `kms` - KMS keys
- `lambda_function` - Lambda functions
- `permission_relationships` - IAM permission relationships
- `rds` - RDS database instances and clusters
- `redshift` - Redshift clusters
- `resourcegroupstaggingapi` - AWS resource tags
- `route53` - Route 53 hosted zones and records
- `s3` - S3 buckets
- `s3accountpublicaccessblock` - S3 account-level public access block configuration
- `sagemaker` - SageMaker resources
- `secretsmanager` - Secrets Manager secrets
- `securityhub` - Security Hub findings
- `sns` - SNS topics
- `sqs` - SQS queues
- `ssm` - Systems Manager

**Note**: Cartography automatically handles resource dependencies and sync order internally, so you don't need to worry about the order in which you specify resources in the list. Using `--aws-requested-syncs` can significantly reduce sync time and API calls when you only need specific resources.
