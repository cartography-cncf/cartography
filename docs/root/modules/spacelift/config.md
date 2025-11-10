## Spacelift Configuration

Follow these steps to analyze Spacelift infrastructure in Cartography.

### 1. Prepare Spacelift API Credentials

1. Generate a Spacelift API token:
   - Log in to your Spacelift account
   - Navigate to your user settings or organization settings
   - Generate an API token with appropriate permissions
   - See [Spacelift's API documentation](https://docs.spacelift.io/integrations/api) for detailed instructions

2. Set up your environment:
   - Store your API token in an environment variable (e.g., `SPACELIFT_API_TOKEN`)
   - Note your Spacelift API endpoint (typically `https://YOUR_ACCOUNT.app.spacelift.io/graphql`)

### 2. Configure Cartography

Pass the Spacelift configuration to Cartography via CLI:

```bash
cartography \
  --spacelift-api-endpoint https://YOUR_ACCOUNT.app.spacelift.io/graphql \
  --spacelift-api-token-env-var SPACELIFT_API_TOKEN
```

#### Required Parameters

- `--spacelift-api-endpoint`: Your Spacelift GraphQL API endpoint
- `--spacelift-api-token-env-var`: Name of the environment variable containing your Spacelift API token

### 3. (Optional) Configure EC2 Ownership Tracking

If you want to track EC2 instances created/modified by Spacelift runs via CloudTrail data:

1. Set up CloudTrail logs in an S3 bucket
2. Use AWS Athena to query and export relevant CloudTrail events to S3 as JSON files
3. Configure the S3 location in Cartography:

```bash
cartography \
  --spacelift-api-endpoint https://YOUR_ACCOUNT.app.spacelift.io/graphql \
  --spacelift-api-token-env-var SPACELIFT_API_TOKEN \
  --spacelift-ec2-ownership-s3-bucket YOUR_BUCKET_NAME \
  --spacelift-ec2-ownership-s3-prefix cloudtrail-data/ \
  --spacelift-ec2-ownership-aws-profile your-aws-profile  # optional
```

#### EC2 Ownership Parameters

- `--spacelift-ec2-ownership-s3-bucket`: S3 bucket containing CloudTrail data exports
- `--spacelift-ec2-ownership-s3-prefix`: S3 prefix where JSON files are stored
- `--spacelift-ec2-ownership-aws-profile`: (Optional) AWS profile to use for S3 access

### What Gets Synced

Cartography will sync the following Spacelift resources:

- **Accounts**: Your Spacelift organization
- **Spaces**: Organizational units for grouping resources
- **Stacks**: Infrastructure-as-code stacks
- **Runs**: Deployment executions
- **Git Commits**: Commits associated with runs
- **Users**: Human and system users triggering runs
- **Worker Pools**: Custom worker pool configurations
- **Workers**: Individual workers in pools
- **EC2 Ownership** (optional): CloudTrail events linking runs to EC2 instances
