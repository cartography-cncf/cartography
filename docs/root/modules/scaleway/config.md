# Scaleway Configuration

## Authentication

Use an API key linked to a dedicated Scaleway application with read-only permissions:

1. Create a policy in the [Scaleway IAM console](https://console.scaleway.com/iam/policies).
1. Create an application in the [Scaleway applications console](https://console.scaleway.com/iam/applications) and attach the policy.
1. Create an API key for that application in the [Scaleway API keys console](https://console.scaleway.com/iam/api-keys).
1. Store the secret key in an environment variable and note the access key.

## Required Permissions

Configure the read-only policy with:

1. A rule scoped to **Access to Organization features** with `OrganizationReadOnly`, `ProjectReadOnly`, and `IAMReadOnly`.
1. A rule scoped to **All current and future projects** under **Access to resources**, with `AllProductsReadOnly`.

## Configure Cartography

Provide these options:

- `--scaleway-access-key`: API access key.
- `--scaleway-secret-key-env-var`: Name of the environment variable containing the API secret key.
- `--scaleway-org`: Organization name from the [Scaleway organization console](https://console.scaleway.com/organization).

## Run Cartography

```bash
export SCALEWAY_SECRET_KEY='<secret-key>'
cartography \
  --selected-modules scaleway \
  --scaleway-org '<organization-name>' \
  --scaleway-access-key '<access-key>' \
  --scaleway-secret-key-env-var SCALEWAY_SECRET_KEY
```
