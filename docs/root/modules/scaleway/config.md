## Scaleway Configuration

Follow these steps to analyze Scaleway objects with Cartography.

```{important}
We strongly advise to use an API Key linked to a dedicated application with restricted permissions (read-only).
```
1. Create a policy in Scaleway
    1. Create a `read only` policy in [Scaleway console](https://console.scaleway.com/iam/policies)
    1. Create a first rule with `Access to Organization features` scope, then add following permissions sets `OrganizationReadOnly`, `ProjectReadOnly`, `IAMReadOnly`
    1. Create a second rule with `Access to resources` set to `All current and future projects`, then add the following permission set `AllProductsReadOnly`
1. Create an application in [Scaleway console](https://console.scaleway.com/iam/applications) and attach your `read only` policy
1. Create your Scaleway API Key
    1. Create an API Key in [Scaleway console](https://console.scaleway.com/iam/api-keys) linked to your application
    1. Populate an environment variable with the `secret key`. You can pass the environment variable name via CLI with the `--scaleway-secret-key-env-var` parameter.
    1. Pass the `access key` to the CLI with the `--scaleway-access-key` parameter.
1. Get your organization name from [Scaleway console](https://console.scaleway.com/organization) and pass it via CLI with the `--scaleway-org` parameter.
