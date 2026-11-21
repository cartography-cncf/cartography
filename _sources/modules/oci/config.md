# OCI Configuration

## Authentication

Create an OCI user and API signing key for Cartography. See the
[OCI API key authentication guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

## Required Permissions

Apply these IAM policies to the Cartography identity at the tenancy level:

```
Allow group CartographyGroup to inspect all-resources in tenancy
Allow group CartographyGroup to read policies in tenancy
Allow group CartographyGroup to read compartments in tenancy
Allow group CartographyGroup to read users in tenancy
Allow group CartographyGroup to read groups in tenancy
Allow group CartographyGroup to read tenancies in tenancy
```

Replace `CartographyGroup` with the group that contains the Cartography user.

## Configure Cartography

Cartography uses the standard OCI SDK configuration file. Create or update
`~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

## Run Cartography

```bash
cartography --selected-modules oci
```

## References

- [OCI common policies](https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)
- [OCI SDK configuration](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm)
