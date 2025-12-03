## GCP Configuration

Follow these steps to analyze GCP projects with Cartography.

### 1. Create an Identity

Create a User Account or Service Account for Cartography to run as.

### 2. Grant Required Roles

Grant the following roles to the identity at the **organization level**. This ensures Cartography can access all projects within the organization. See [GCP's resource hierarchy documentation](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#organizations) for details.

| Role | Purpose | Required |
|------|---------|----------|
| `roles/iam.securityReviewer` | List/get IAM roles and service accounts | Yes |
| `roles/resourcemanager.organizationViewer` | List/get GCP Organizations | Yes |
| `roles/resourcemanager.folderViewer` | List/get GCP Folders | Yes |
| `roles/cloudasset.viewer` | Sync IAM policy bindings (effective policies across org hierarchy) | Optional |

To grant a role at the organization level:
```bash
gcloud organizations add-iam-policy-binding YOUR_ORG_ID \
    --member="user:YOUR_EMAIL_OR_SERVICE_ACCOUNT" \
    --role="ROLE_NAME"
```

You can find your organization ID with:
```bash
gcloud organizations list
```

### 3. Configure Authentication

Ensure the machine running Cartography can authenticate to this identity:

- **Method 1 (Credentials file)**: Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to a JSON credentials file. Ensure only the Cartography user has read access to this file.
- **Method 2 (Default service account)**: If running on GCE or another GCP service, use the default service account credentials. See the [official docs](https://cloud.google.com/docs/authentication/production) on Application Default Credentials.

### Cloud Asset Inventory (CAI)

Cartography uses the [Cloud Asset Inventory API](https://cloud.google.com/asset-inventory/docs/overview) for two features:

1. **IAM Fallback**: When the IAM API is disabled on a target project, Cartography falls back to CAI to retrieve service accounts and custom roles.
2. **Policy Bindings**: Sync effective IAM policies (including inherited policies from parent orgs/folders) for all resources.

#### Setup

CAI API calls are billed against your **quota project** (the project associated with your Application Default Credentials), not the target projects being scanned.

1. Enable the Cloud Asset Inventory API on your quota project:
   ```bash
   gcloud services enable cloudasset.googleapis.com --project=YOUR_QUOTA_PROJECT
   ```

2. Check your current quota project:
   ```bash
   gcloud config get-value project
   ```

3. For policy bindings sync, grant `roles/cloudasset.viewer` at the **organization level** (see roles table above).

#### Limitations

- **IAM Fallback**: Only retrieves custom roles defined at the project level. Predefined roles (e.g., `roles/viewer`, `roles/editor`) are not included. Enable the IAM API on target projects for complete role coverage.
- **Policy Bindings**: Requires organization-level `roles/cloudasset.viewer`. If this role is missing, Cartography will log a warning and skip policy bindings sync (other sync operations will continue normally).
