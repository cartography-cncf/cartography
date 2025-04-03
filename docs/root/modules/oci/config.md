## OCI Config

:::{important}
TODO: Help wanted
:::

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_OCI__SYNC_ALL_PROFILES** | `bool` _(default: False)_ | Enable OCI sync for all discovered named profiles. When this parameter is supplied cartography will discover all configured OCI named profiles (see https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) and run the OCI sync job for each profile not named "DEFAULT". If this parameter is not supplied, cartography will use the default OCI credentials available in your environment to run the OCI sync once. |
