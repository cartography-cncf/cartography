## OCI Configuration

Follow these steps to analyze Oracle Cloud Infrastructure (OCI) assets with Cartography.

### 1. Create an OCI Identity

Create a User Account or API Key for Cartography to use. See the [OCI documentation on API Key authentication](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

### 2. Grant Required Policies

Grant the following IAM policies to the identity. These policies should be applied at the **tenancy level** to allow Cartography to read all resources.

```
Allow group CartographyGroup to inspect all-resources in tenancy
Allow group CartographyGroup to read policies in tenancy
Allow group CartographyGroup to read compartments in tenancy
Allow group CartographyGroup to read users in tenancy
Allow group CartographyGroup to read groups in tenancy
Allow group CartographyGroup to read tenancies in tenancy
```

For more information on OCI policies, see the [OCI Common Policies documentation](https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm).

### 3. Configure OCI Credentials

Cartography uses the standard OCI SDK configuration file. Create or update your OCI config file at `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

For detailed instructions on setting up the config file, see the [OCI SDK Configuration documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).
