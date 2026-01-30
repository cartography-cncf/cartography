## Spacelift Configuration

Follow these steps to analyze Spacelift infrastructure in Cartography.

### 1. Prepare Spacelift API Credentials

Cartography supports two authentication methods for Spacelift:

#### Method 1: API Key ID and Secret (Recommended)

This is the recommended method as it uses short-lived tokens and doesn't require manual token generation.

1. Generate a Spacelift API key:
   - Log in to your Spacelift account
   - Navigate to your user settings or organization settings
   - Create an API key and download the credentials
   - You'll receive an API key ID (26-character ULID) and a secret
   - See [Spacelift's API documentation](https://docs.spacelift.io/integrations/api) for detailed instructions

2. Set up your environment:
   - Store your API key ID in an environment variable (e.g., `SPACELIFT_API_KEY_ID`)
   - Store your API key secret in an environment variable (e.g., `SPACELIFT_API_KEY_SECRET`)
   - Note your Spacelift API endpoint (typically `https://YOUR_ACCOUNT.app.spacelift.io/graphql`)

3. Configure Cartography:

```bash
cartography \
  --spacelift-api-endpoint https://YOUR_ACCOUNT.app.spacelift.io/graphql \
  --spacelift-api-key-id-env-var SPACELIFT_API_KEY_ID \
  --spacelift-api-key-secret-env-var SPACELIFT_API_KEY_SECRET
```

Cartography will automatically exchange your API key credentials for a JWT token when needed.

#### Method 2: Pre-generated JWT Token (Alternative)

If you prefer to manage token generation yourself, you can provide a pre-generated JWT token.

1. Generate a Spacelift API token manually using your API key
2. Store the token in an environment variable (e.g., `SPACELIFT_API_TOKEN`)
3. Configure Cartography:

```bash
cartography \
  --spacelift-api-endpoint https://YOUR_ACCOUNT.app.spacelift.io/graphql \
  --spacelift-api-token-env-var SPACELIFT_API_TOKEN
```

### 2. Required Parameters

One of these authentication combinations is required:

**Option A (Recommended):**
- `--spacelift-api-endpoint`: Your Spacelift GraphQL API endpoint
- `--spacelift-api-key-id-env-var`: Name of the environment variable containing your API key ID (default: `SPACELIFT_API_KEY_ID`)
- `--spacelift-api-key-secret-env-var`: Name of the environment variable containing your API key secret (default: `SPACELIFT_API_KEY_SECRET`)

**Option B (Alternative):**
- `--spacelift-api-endpoint`: Your Spacelift GraphQL API endpoint
- `--spacelift-api-token-env-var`: Name of the environment variable containing your pre-generated JWT token (default: `SPACELIFT_API_TOKEN`)

### 3. (Optional) Configure EC2 Ownership Tracking

If you want to track EC2 instances created/modified by Spacelift runs via CloudTrail data:

1. Set up CloudTrail logs in an S3 bucket
2. Use AWS Athena to query and export relevant CloudTrail events to S3 as JSON files
3. Add the S3 configuration to your Cartography command:

```bash
# Example with API key authentication
cartography \
  --spacelift-api-endpoint https://YOUR_ACCOUNT.app.spacelift.io/graphql \
  --spacelift-api-key-id-env-var SPACELIFT_API_KEY_ID \
  --spacelift-api-key-secret-env-var SPACELIFT_API_KEY_SECRET \
  --spacelift-ec2-ownership-s3-bucket YOUR_BUCKET_NAME \
  --spacelift-ec2-ownership-s3-prefix cloudtrail-data/ \
  --spacelift-ec2-ownership-aws-profile your-aws-profile  # optional
```

#### EC2 Ownership Parameters

- `--spacelift-ec2-ownership-s3-bucket`: S3 bucket containing CloudTrail data exports
- `--spacelift-ec2-ownership-s3-prefix`: S3 prefix where JSON files are stored
- `--spacelift-ec2-ownership-aws-profile`: (Optional) AWS profile to use for S3 access

### 4. What Gets Synced

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
