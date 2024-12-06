## Azure Schema

.. _azure_schema:

### AzureTenant

Representation of an [Azure Tenant](https://docs.microsoft.com/en-us/rest/api/resources/Tenants/List).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Tenant ID number|

#### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzureTenant)-[RESOURCE]->(AzurePrincipal)
        ```

### AzurePrincipal

Representation of an [Azure Principal](https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**email**| Email of the Azure Principal|

#### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzurePrincipal)-[RESOURCE]->(AzureTenant)
        ```

### AzureSubscription

Representation of an [Azure Subscription](https://docs.microsoft.com/en-us/rest/api/resources/subscriptions)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Subscription ID number|
|name | The friendly name that identifies the subscription|
|path | The full ID for the Subscription|
|state| Can be one of ``Enabled \| Disabled \| Deleted \| PastDue \| Warned``|

#### Relationships

- Azure Tenant contains one or more Subscriptions.

        ```
        (AzureTenant)-[RESOURCE]->(AzureSubscription)
        ```

### VirtualMachine

Representation of an [Azure Virtual Machine](https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Virtual Machine ID number|
|type | The type of the resource|
|location | The location where Virtual Machine is created|
|resourcegroup | The Resource Group where Virtual Machine is created|
|name | The friendly name that identifies the Virtual Machine|
|plan | The plan associated with the Virtual Machine|
|size | The size of the Virtual Machine|
|license\_type | The type of license|
|computer\_name | The computer name|
|identity\_type | The type of identity used for the virtual machine|
|zones | The Virtual Machine zones|
|ultra\_ssd\_enabled | Enables or disables a capability on the virtual machine or virtual machine scale set.|
|priority | Specifies the priority for the virtual machine|
|eviction\_policy | Specifies the eviction policy for the Virtual Machine|

#### Relationships

- Azure Subscription contains one or more Virtual Machines.

        ```
        (AzureSubscription)-[RESOURCE]->(VirtualMachine)
        ```

### AzureDataDisk

Representation of an [Azure Data Disk](https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/get#datadisk).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Data Disk ID number|
|lun | Specifies the logical unit number of the data disk|
|name | The data disk name|
|vhd | The virtual hard disk associated with data disk|
|image | The source user image virtual hard disk|
|size | The size of the disk in GB|
|caching | Specifies the caching requirement|
|createoption | Specifies how the disk should be created|
|write\_accelerator\_enabled | Specifies whether writeAccelerator should be enabled or disabled on the data disk|
|managed\_disk\_storage\_type | The data disk storage type|

#### Relationships

- Azure Virtual Machines are attached to Data Disks.

        ```
        (VirtualMachine)-[ATTACHED_TO]->(AzureDataDisk)
        ```

### AzureDisk

Representation of an [Azure Disk](https://docs.microsoft.com/en-us/rest/api/compute/disks).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Disk ID number|
|type | The type of the resource|
|location | The location where Disk is created|
|resourcegroup | The Resource Group where Disk is created|
|name | The friendly name that identifies the Disk|
|createoption | Specifies how the disk should be created|
|disksizegb | The size of the disk in GB|
|encryption | Specifies whether the disk has encryption enabled |
|maxshares | Specifies how many machines can share the disk|
|ostype | The operating system type of the disk|
|tier | Performance Tier associated with the disk|
|sku | The disk sku name|
|zones | The logical zone list for disk|

#### Relationships

- Azure Subscription contains one or more Disks.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureDisk)
        ```

### AzureSnapshot

Representation of an [Azure Snapshot](https://docs.microsoft.com/en-us/rest/api/compute/snapshots).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Snapshot ID number|
|type | The type of the resource|
|location | The location where snapshot is created|
|resourcegroup | The Resource Group where snapshot is created|
|name | The friendly name that identifies the snapshot|
|createoption | Specifies how the disk should be created|
|disksizegb | The size of the snapshot in GB|
|encryption | Specifies whether the snapshot has encryption enabled |
|incremental | Indicates whether a snapshot is incremental or not |
|network\_access\_policy | Policy for accessing the snapshot via network|
|ostype | The operating system type of the snapshot|
|tier | Performance Tier associated with the snapshot|
|sku | The snapshot sku name|
|zones | The logical zone list for snapshot|

#### Relationships

- Azure Subscription contains one or more Snapshots.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureSnapshot)
        ```

### AzureSQLServer

Representation of an [AzureSQLServer](https://docs.microsoft.com/en-us/rest/api/sql/servers).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|location | The location where the resource is created|
|resourcegroup | The Resource Group where SQL Server is created|
|name | The friendly name that identifies the SQL server|
|kind | Specifies the kind of SQL server|
|state | The state of the server|
|version | The version of the server |

#### Relationships

- Azure Subscription contains one or more SQL Servers.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureSQLServer)
        ```
- Azure SQL Server can be used by one or more Azure Server DNS Aliases.

        ```
        (AzureSQLServer)-[USED_BY]->(AzureServerDNSAlias)
        ```
- Azure SQL Server can be administered by one or more Azure Server AD Administrators.

        ```
        (AzureSQLServer)-[ADMINISTERED_BY]->(AzureServerADAdministrator)
        ```
- Azure SQL Server has one or more Azure Recoverable Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRecoverableDatabase)
        ```
- Azure SQL Server has one or more Azure Restorable Dropped Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRestorableDroppedDatabase)
        ```
- Azure SQL Server has one or more Azure Failover Group.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureFailoverGroup)
        ```
- Azure SQL Server has one or more Azure Elastic Pool.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureElasticPool)
        ```
- Azure SQL Server has one or more Azure SQL Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureSQLDatabase)
        ```

### AzureServerDNSAlias

Representation of an [AzureServerDNSAlias](https://docs.microsoft.com/en-us/rest/api/sql/serverdnsaliases).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the server DNS alias|
|dnsrecord | The fully qualified DNS record for alias.|

#### Relationships

- Azure SQL Server can be used by one or more Azure Server DNS Aliases.

        ```
        (AzureSQLServer)-[USED_BY]->(AzureServerDNSAlias)
        ```

### AzureServerADAdministrator

Representation of an [AzureServerADAdministrator](https://docs.microsoft.com/en-us/rest/api/sql/serverazureadadministrators).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|administratortype | The type of the server administrator.|
|login | The login name of the server administrator.|

#### Relationships

- Azure SQL Server can be administered by one or more Azure Server AD Administrators.

        ```
        (AzureSQLServer)-[ADMINISTERED_BY]->(AzureServerADAdministrator)
        ```

### AzureRecoverableDatabase

Representation of an [AzureRecoverableDatabase](https://docs.microsoft.com/en-us/rest/api/sql/recoverabledatabases).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|edition | The edition of the database.|
|servicelevelobjective | The service level objective name of the database.|
|lastbackupdate | The last available backup date of the database (ISO8601 format).|

#### Relationships

- Azure SQL Server has one or more Azure Recoverable Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRecoverableDatabase)
        ```

### AzureRestorableDroppedDatabase

Representation of an [AzureRestorableDroppedDatabase](https://docs.microsoft.com/en-us/rest/api/sql/restorabledroppeddatabases).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The geo-location where the resource lives.|
|databasename | The name of the database.|
|creationdate | The creation date of the database (ISO8601 format).|
|deletiondate | The deletion date of the database (ISO8601 format).|
|restoredate | The earliest restore date of the database (ISO8601 format).|
|edition | The edition of the database.|
|servicelevelobjective | The service level objective name of the database.|
|maxsizebytes | The max size in bytes of the database.|

#### Relationships

- Azure SQL Server has one or more Azure Restorable Dropped Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRestorableDroppedDatabase)
        ```

### AzureFailoverGroup

Representation of an [AzureFailoverGroup](https://docs.microsoft.com/en-us/rest/api/sql/failovergroups).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The geo-location where the resource lives.|
|replicationrole | Local replication role of the failover group instance.|
|replicationstate | Replication state of the failover group instance.|

#### Relationships

- Azure SQL Server has one or more Azure Failover Group.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureFailoverGroup)
        ```

### AzureElasticPool

Representation of an [AzureElasticPool](https://docs.microsoft.com/en-us/rest/api/sql/elasticpools).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The location of the resource.|
|kind | The kind of elastic pool.|
|creationdate | The creation date of the elastic pool (ISO8601 format).|
|state | The state of the elastic pool.|
|maxsizebytes | The storage limit for the database elastic pool in bytes.|
|licensetype | The license type to apply for this elastic pool. |
|zoneredundant | Specifies whether or not this elastic pool is zone redundant, which means the replicas of this elastic pool will be spread across multiple availability zones.|

#### Relationships

- Azure SQL Server has one or more Azure Elastic Pool.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureElasticPool)
        ```

### AzureSQLDatabase

Representation of an [AzureSQLDatabase](https://docs.microsoft.com/en-us/rest/api/sql/databases).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The location of the resource.|
|kind | The kind of database.|
|creationdate | The creation date of the database (ISO8601 format).|
|databaseid | The ID of the database.|
|maxsizebytes | The max size of the database expressed in bytes.|
|licensetype | The license type to apply for this database.|
|secondarylocation | The default secondary region for this database.|
|elasticpoolid | The resource identifier of the elastic pool containing this database.|
|collation | The collation of the database.|
|failovergroupid | Failover Group resource identifier that this database belongs to.|
|zoneredundant | Whether or not this database is zone redundant, which means the replicas of this database will be spread across multiple availability zones.|
|restorabledroppeddbid | The resource identifier of the restorable dropped database associated with create operation of this database.|
|recoverabledbid | The resource identifier of the recoverable database associated with create operation of this database.|

#### Relationships

- Azure SQL Server has one or more Azure SQL Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureSQLDatabase)
        ```
- Azure SQL Database contains one or more Azure Replication Links.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureReplicationLink)
        ```
- Azure SQL Database contains a Database Threat Detection Policy.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureDatabaseThreatDetectionPolicy)
        ```
- Azure SQL Database contains one or more Restore Points.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureRestorePoint)
        ```
- Azure SQL Database contains Transparent Data Encryption.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureTransparentDataEncryption)
        ```

### AzureReplicationLink

Representation of an [AzureReplicationLink](https://docs.microsoft.com/en-us/rest/api/sql/replicationlinks).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | Location of the server that contains this firewall rule.|
|partnerdatabase | The name of the partner database.|
|partnerlocation | The Azure Region of the partner database.|
|partnerrole | The role of the database in the replication link.|
|partnerserver | The name of the server hosting the partner database.|
|mode | Replication mode of this replication link.|
|state | The replication state for the replication link.|
|percentcomplete | The percentage of seeding complete for the replication link.|
|role | The role of the database in the replication link.|
|starttime | The start time for the replication link.|
|terminationallowed | Legacy value indicating whether termination is allowed.|

#### Relationships

- Azure SQL Database contains one or more Azure Replication Links.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureReplicationLink)
        ```

### AzureDatabaseThreatDetectionPolicy

Representation of an [AzureDatabaseThreatDetectionPolicy](https://docs.microsoft.com/en-us/rest/api/sql/databasethreatdetectionpolicies).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The geo-location where the resource lives.|
|kind | The kind of the resource.|
|emailadmins | Specifies that the alert is sent to the account administrators.|
|emailaddresses | Specifies the semicolon-separated list of e-mail addresses to which the alert is sent.|
|retentiondays | Specifies the number of days to keep in the Threat Detection audit logs.|
|state | Specifies the state of the policy.|
|storageendpoint | Specifies the blob storage endpoint.|
|useserverdefault | Specifies whether to use the default server policy.|
|disabledalerts | Specifies the semicolon-separated list of alerts that are disabled, or empty string to disable no alerts.|

#### Relationships

- Azure SQL Database contains a Database Threat Detection Policy.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureDatabaseThreatDetectionPolicy)
        ```

### AzureRestorePoint

Representation of an [AzureRestorePoint](https://docs.microsoft.com/en-us/rest/api/sql/restorepoints).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The geo-location where the resource lives.|
|restoredate | The earliest time to which this database can be restored.|
|restorepointtype | The type of restore point.|
|creationdate | The time the backup was taken.|

#### Relationships

- Azure SQL Database contains one or more Restore Points.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureRestorePoint)
        ```

### AzureTransparentDataEncryption

Representation of an [AzureTransparentDataEncryption](https://docs.microsoft.com/en-us/rest/api/sql/transparentdataencryptions).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The resource location.|
|status | The status of the database transparent data encryption.|

#### Relationships

- Azure SQL Database contains Transparent Data Encryption.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureTransparentDataEncryption)
        ```

### AzureStorageAccount

Representation of an [AzureStorageAccount](https://docs.microsoft.com/en-us/rest/api/storagerp/storageaccounts).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|location | The geo-location where the resource lives.|
|resourcegroup | The Resource Group where the storage account is created|
|name | The name of the resource.|
|kind | Gets the Kind of the resource.|
|creationtime | Gets the creation date and time of the storage account in UTC.|
|hnsenabled | Specifies if the Account HierarchicalNamespace is enabled.|
|primarylocation | Gets the location of the primary data center for the storage account.|
|secondarylocation | Gets the location of the geo-replicated secondary for the storage account.|
|provisioningstate | Gets the status of the storage account at the time the operation was called.|
|statusofprimary | Gets the status availability status of the primary location of the storage account.|
|statusofsecondary | Gets the status availability status of the secondary location of the storage account.|
|supportshttpstrafficonly | Allows https traffic only to storage service if sets to true.|

#### Relationships

- Azure Subscription contains one or more Storage Accounts.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureStorageAccount)
        ```
- Azure Storage Accounts uses one or more Queue Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageQueueService)
        ```
- Azure Storage Accounts uses one or more Table Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageTableService)
        ```
- Azure Storage Accounts uses one or more File Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageFileService)
        ```
- Azure Storage Accounts uses one or more Blob Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageBlobService)
        ```

### AzureStorageQueueService

Representation of an [AzureStorageQueueService](https://docs.microsoft.com/en-us/rest/api/storagerp/queueservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue service.|

#### Relationships

- Azure Storage Accounts uses one or more Queue Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageQueueService)
        ```
- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

### AzureStorageTableService

Representation of an [AzureStorageTableService](https://docs.microsoft.com/en-us/rest/api/storagerp/tableservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table service.|

#### Relationships

- Azure Storage Accounts uses one or more Table Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageTableService)
        ```
- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

### AzureStorageFileService

Representation of an [AzureStorageFileService](https://docs.microsoft.com/en-us/rest/api/storagerp/fileservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the file service.|

#### Relationships

- Azure Storage Accounts uses one or more File Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageFileService)
        ```
- Table Service contains one or more file shares.

        ```
        (AzureStorageFileService)-[CONTAINS]->(AzureStorageFileShare)
        ```

### AzureStorageBlobService

Representation of an [AzureStorageBlobService](https://docs.microsoft.com/en-us/rest/api/storagerp/blobservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the blob service.|

#### Relationships

- Azure Storage Accounts uses one or more Blob Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageBlobService)
        ```
- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```

### AzureStorageQueue

Representation of an [AzureStorageQueue](https://docs.microsoft.com/en-us/rest/api/storagerp/queue).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue.|

#### Relationships

- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

### AzureStorageTable

Representation of an [AzureStorageTable](https://docs.microsoft.com/en-us/rest/api/storagerp/table).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table resource.|
|tablename | Table name under the specified account.|

#### Relationships

- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

### AzureStorageFileShare

Representation of an [AzureStorageFileShare](https://docs.microsoft.com/en-us/rest/api/storagerp/fileshares).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the resource.|
|lastmodifiedtime | Specifies the date and time the share was last modified.|
|sharequota | The maximum size of the share, in gigabytes.|
|accesstier | Specifies the access tier for the share.|
|deleted | Indicates whether the share was deleted.|
|accesstierchangetime | Indicates the last modification time for share access tier.|
|accesstierstatus | Indicates if there is a pending transition for access tier.|
|deletedtime | The deleted time if the share was deleted.|
|enabledprotocols | The authentication protocol that is used for the file share.|
|remainingretentiondays | Remaining retention days for share that was soft deleted.|
|shareusagebytes | The approximate size of the data stored on the share.|
|version | The version of the share.|

#### Relationships

- File Service contains one or more file shares.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageFileShare)
        ```

### AzureStorageBlobContainer

Representation of an [AzureStorageBlobContainer](https://docs.microsoft.com/en-us/rest/api/storagerp/blobcontainers).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the resource.|
|deleted | Indicates whether the blob container was deleted.|
|deletedtime | Blob container deletion time.|
|defaultencryptionscope | Default the container to use specified encryption scope for all writes.|
|publicaccess | Specifies whether data in the container may be accessed publicly and the level of access.|
|leasestatus | The lease status of the container.|
|leasestate | Lease state of the container.|
|lastmodifiedtime | Specifies the date and time the container was last modified.|
|remainingretentiondays | Specifies the remaining retention days for soft deleted blob container.|
|version | The version of the deleted blob container.|
|hasimmutabilitypolicy | Specifies the if the container has an ImmutabilityPolicy or not.|
|haslegalhold | Specifies if the container has any legal hold tags.|
|leaseduration | Specifies whether the lease on a container is of infinite or fixed duration, only when the container is leased.|

#### Relationships

- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```

### AzureCosmosDBAccount

Representation of an [AzureCosmosDBAccount](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|location | The location of the resource group to which the resource belongs.|
|resourcegroup | The Resource Group where the database account is created.|
|name | The name of the ARM resource.|
|kind | Indicates the type of database account.|
|type | The type of Azure resource.|
|ipranges | List of IpRules.|
|capabilities | List of Cosmos DB capabilities for the account.|
|documentendpoint | The connection endpoint for the Cosmos DB database account.|
|virtualnetworkfilterenabled | Flag to indicate whether to enable/disable Virtual Network ACL rules.|
|enableautomaticfailover | Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage.|
|provisioningstate | The status of the Cosmos DB account at the time the operation was called.|
|multiplewritelocations | Enables the account to write in multiple locations.|
|accountoffertype | The offer type for the Cosmos DB database account.|
|publicnetworkaccess | Whether requests from Public Network are allowed.|
|enablecassandraconnector | Enables the cassandra connector on the Cosmos DB C* account.|
|connectoroffer | The cassandra connector offer type for the Cosmos DB database C* account.|
|disablekeybasedmetadatawriteaccess | Disable write operations on metadata resources (databases, containers, throughput) via account keys.|
|keyvaulturi | The URI of the key vault.|
|enablefreetier | Flag to indicate whether Free Tier is enabled.|
|enableanalyticalstorage | Flag to indicate whether to enable storage analytics.|
|defaultconsistencylevel | The default consistency level and configuration settings of the Cosmos DB account.|
|maxstalenessprefix | When used with the Bounded Staleness consistency level, this value represents the number of stale requests tolerated.|
|maxintervalinseconds | When used with the Bounded Staleness consistency level, this value represents the time amount of staleness (in seconds) tolerated.|

#### Relationships

- Azure Subscription contains one or more database accounts.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureCosmosDBAccount)
        ```
- Azure Database Account can be read from, written from and is associated with Azure CosmosDB Locations.

        ```
        (AzureCosmosDBAccount)-[CAN_WRITE_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureCosmosDBAccount)-[CAN_READ_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureCosmosDBAccount)-[ASSOCIATED_WITH]->(AzureCosmosDBLocation)
        ```
- Azure Database Account contains one or more Cors Policy.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBCorsPolicy)
        ```
- Azure Database Account contains one or more failover policies.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBAccountFailoverPolicy)
        ```
- Azure Database Account is configured with one or more private endpoint connections.

        ```
        (AzureCosmosDBAccount)-[CONFIGURED_WITH]->(AzureCDBPrivateEndpointConnection)
        ```
- Azure Database Account is configured with one or more virtual network rules.

        ```
        (AzureCosmosDBAccount)-[CONFIGURED_WITH]->(AzureCosmosDBVirtualNetworkRule)
        ```
- Azure Database Account contains one or more SQL databases.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBSqlDatabase)
        ```
- Azure Database Account contains one or more Cassandra keyspace.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBCassandraKeyspace)
        ```
- Azure Database Account contains one or more MongoDB Database.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBMongoDBDatabase)
        ```
- Azure Database Account contains one or more table resource.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBTableResource)
        ```

### AzureCosmosDBLocation

Representation of an [Azure CosmosDB Location](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique identifier of the region within the database account.|
|locationname | The name of the region.|
|documentendpoint | The connection endpoint for the specific region.|
|provisioningstate | The status of the Cosmos DB account at the time the operation was called.|
|failoverpriority | The failover priority of the region.|
|iszoneredundant | Flag to indicate whether or not this region is an AvailabilityZone region.|

#### Relationships

- Azure Database Account has write permissions from, read permissions from and is associated with Azure CosmosDB Locations.

        ```
        (AzureCosmosDBAccount)-[CAN_WRITE_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureCosmosDBAccount)-[CAN_READ_FROM]->(AzureCosmosDBLocation)
        ```
        (AzureCosmosDBAccount)-[ASSOCIATED_WITH]->(AzureCosmosDBLocation)
        ```

### AzureCosmosDBCorsPolicy

Representation of an [Azure Cosmos DB Cors Policy](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier for Cors Policy.|
|allowedorigins | The origin domains that are permitted to make a request against the service via CORS.|
|allowedmethods | The methods (HTTP request verbs) that the origin domain may use for a CORS request.|
|allowedheaders | The request headers that the origin domain may specify on the CORS request.|
|exposedheaders | The response headers that may be sent in the response to the CORS request and exposed by the browser to the request issuer.|
|maxageinseconds | The maximum amount time that a browser should cache the preflight OPTIONS request.|

#### Relationships

- Azure Database Account contains one or more Cors Policy.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBCorsPolicy)
        ```

### AzureCosmosDBAccountFailoverPolicy

Representation of an Azure Database Account [Failover Policy](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique identifier of the region in which the database account replicates to.|
|locationname | The name of the region in which the database account exists.|
|failoverpriority | The failover priority of the region. A failover priority of 0 indicates a write region.|

#### Relationships

- Azure Database Account contains one or more failover policies.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBAccountFailoverPolicy)
        ```

### AzureCDBPrivateEndpointConnection

Representation of an Azure Cosmos DB [Private Endpoint Connection](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource Id for the resource.|
|name | The name of the resource.|
|privateendpointid | Resource id of the private endpoint.|
|status | The private link service connection status.|
|actionrequired | Any action that is required beyond basic workflow (approve/ reject/ disconnect).|

#### Relationships

- Azure Database Account is configured with one or more private endpoint connections.

        ```
        (AzureCosmosDBAccount)-[CONFIGURED_WITH]->(AzureCDBPrivateEndpointConnection)
        ```

### AzureCosmosDBVirtualNetworkRule

Representation of an Azure Cosmos DB [Virtual Network Rule](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Resource ID of a subnet.|
|ignoremissingvnetserviceendpoint | Create firewall rule before the virtual network has vnet service endpoint enabled.|

#### Relationships

- Azure Database Account is configured with one or more virtual network rules.

        ```
        (AzureCosmosDBAccount)-[CONFIGURED_WITH]->(AzureCosmosDBVirtualNetworkRule)
        ```

### AzureCosmosDBSqlDatabase

Representation of an [AzureCosmosDBSqlDatabase](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

#### Relationships

- Azure Database Account contains one or more SQL databases.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBSqlDatabase)
        ```
- SQL Databases contain one or more SQL containers.

        ```
        (AzureCosmosDBSqlDatabase)-[CONTAINS]->(AzureCosmosDBSqlContainer)
        ```

### AzureCosmosDBCassandraKeyspace

Representation of an [AzureCosmosDBCassandraKeyspace](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

#### Relationships

- Azure Database Account contains one or more Cassandra keyspace.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBCassandraKeyspace)
        ```
- Cassandra Keyspace contains one or more Cassandra tables.

        ```
        (AzureCosmosDBCassandraKeyspace)-[CONTAINS]->(AzureCosmosDBCassandraTable)
        ```

### AzureCosmosDBMongoDBDatabase

Representation of an [AzureCosmosDBMongoDBDatabase](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

#### Relationships

- Azure Database Account contains one or more MongoDB Database.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBMongoDBDatabase)
        ```
- MongoDB database contains one or more MongoDB collections.

        ```
        (AzureCosmosDBMongoDBDatabase)-[CONTAINS]->(AzureCosmosDBMongoDBCollection)
        ```

### AzureCosmosDBTableResource

Representation of an [AzureCosmosDBTableResource](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|

#### Relationships

- Azure Database Account contains one or more table resource.

        ```
        (AzureCosmosDBAccount)-[CONTAINS]->(AzureCosmosDBTableResource)
        ```

### AzureCosmosDBSqlContainer

Representation of an [AzureCosmosDBSqlContainer](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|container| Name of the Cosmos DB SQL container.|
|defaultttl| Default time to live.|
|analyticalttl| Specifies the Analytical TTL.|
|isautomaticindexingpolicy| Indicates if the indexing policy is automatic.|
|indexingmode|  Indicates the indexing mode.|
|conflictresolutionpolicymode| Indicates the conflict resolution mode.|

#### Relationships

- SQL Databases contain one or more SQL containers.

        ```
        (AzureCosmosDBSqlDatabase)-[CONTAINS]->(AzureCosmosDBSqlContainer)
        ```

### AzureCosmosDBCassandraTable

Representation of an [AzureCosmosDBCassandraTable](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|container| Name of the Cosmos DB Cassandra table.|
|defaultttl| Time to live of the Cosmos DB Cassandra table.|
|analyticalttl| Specifies the Analytical TTL.|

#### Relationships

- Cassandra Keyspace contains one or more Cassandra tables.

        ```
        (AzureCosmosDBCassandraKeyspace)-[CONTAINS]->(AzureCosmosDBCassandraTable)
        ```

### AzureCosmosDBMongoDBCollection

Representation of an [AzureCosmosDBMongoDBCollection](https://docs.microsoft.com/en-us/rest/api/cosmos-db-resource-provider/).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The unique resource identifier of the ARM resource.|
|name | The name of the ARM resource.|
|type| The type of Azure resource.|
|location| The location of the resource group to which the resource belongs.|
|throughput| Value of the Cosmos DB resource throughput or autoscaleSettings.|
|maxthroughput| Represents maximum throughput, the resource can scale up to.|
|collectionname| Name of the Cosmos DB MongoDB collection.|
|analyticalttl| Specifies the Analytical TTL.|

#### Relationships

- MongoDB database contains one or more MongoDB collections.

        ```
        (AzureCosmosDBMongoDBDatabase)-[CONTAINS]->(AzureCosmosDBMongoDBCollection)
        ```
