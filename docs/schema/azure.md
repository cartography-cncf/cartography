# Cartography - Microsoft Azure Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [AzureTenant](#azuretenant)
  - [Relationships](#relationships)
- [AzurePrincipal](#azureprincipal)
  - [Relationships](#relationships-1)
- [AzureSubscription](#azuresubscription)
  - [Relationships](#relationships-2)
- [VirtualMachine](#virtualmachine)
  - [Relationships](#relationships-3)
- [AzureDataDisk](#azuredatadisk)
  - [Relationships](#relationships-4)
- [AzureDisk](#azuredisk)
  - [Relationships](#relationships-5)
- [AzureSnapshot](#azuresnapshot)
  - [Relationships](#relationships-6)
- [AzureSQLServer](#azuresqlserver)
  - [Relationships](#relationships-7)
- [AzureServerDNSAlias](#azureserverdnsalias)
  - [Relationships](#relationships-8)
- [AzureServerADAdministrator](#azureserveradadministrator)
  - [Relationships](#relationships-9)
- [AzureRecoverableDatabase](#azurerecoverabledatabase)
  - [Relationships](#relationships-10)
- [AzureRestorableDroppedDatabase](#azurerestorabledroppeddatabase)
  - [Relationships](#relationships-11)
- [AzureFailoverGroup](#azurefailovergroup)
  - [Relationships](#relationships-12)
- [AzureElasticPool](#azureelasticpool)
  - [Relationships](#relationships-13)
- [AzureSQLDatabase](#azuresqldatabase)
  - [Relationships](#relationships-14)
- [AzureReplicationLink](#azurereplicationlink)
  - [Relationships](#relationships-15)
- [AzureDatabaseThreatDetectionPolicy](#azuredatabasethreatdetectionpolicy)
  - [Relationships](#relationships-16)
- [AzureRestorePoint](#azurerestorepoint)
  - [Relationships](#relationships-17)
- [AzureTransparentDataEncryption](#azuretransparentdataencryption)
  - [Relationships](#relationships-18)
- [AzureStorageAccount](#azurestorageaccount)
  - [Relationships](#relationships-19)
- [AzureStorageQueueService](#azurestoragequeueservice)
  - [Relationships](#relationships-20)
- [AzureStorageTableService](#azurestoragetableservice)
  - [Relationships](#relationships-21)
- [AzureStorageFileService](#azurestoragefileservice)
  - [Relationships](#relationships-22)
- [AzureStorageBlobService](#azurestorageblobservice)
  - [Relationships](#relationships-23)
- [AzureStorageQueue](#azurestoragequeue)
  - [Relationships](#relationships-24)
- [AzureStorageTable](#azurestoragetable)
  - [Relationships](#relationships-25)
- [AzureStorageFileShare](#azurestoragefileshare)
  - [Relationships](#relationships-26)
- [AzureStorageBlobContainer](#azurestorageblobcontainer)
  - [Relationships](#relationships-27)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## AzureTenant

Representation of an [Azure Tenant](https://docs.microsoft.com/en-us/rest/api/resources/Tenants/List).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Tenant ID number|

### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzureTenant)-[RESOURCE]->(AzurePrincipal)
        ```

## AzurePrincipal

Representation of an [Azure Principal](https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**email**| Email of the Azure Principal|

### Relationships

- Azure Principal is part of the Azure Account.

        ```
        (AzurePrincipal)-[RESOURCE]->(AzureTenant)
        ```

## AzureSubscription

Representation of an [Azure Subscription](https://docs.microsoft.com/en-us/rest/api/resources/subscriptions)..

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The Azure Subscription ID number|
|name | The friendly name that identifies the subscription|
|path | The full ID for the Subscription|
|state| Can be one of `Enabled | Disabled | Deleted | PastDue | Warned`|

### Relationships

- Azure Tenant contains one or more Subscriptions.

        ```
        (AzureTenant)-[RESOURCE]->(AzureSubscription)
        ```

## VirtualMachine

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
|license_type | The type of license|
|computer_name | The computer name|
|identity_type | The type of identity used for the virtual machine|
|zones | The Virtual Machine zones|
|ultra_ssd_enabled | Enables or disables a capability on the virtual machine or virtual machine scale set.|
|priority | Specifies the priority for the virtual machine|
|eviction_policy | Specifies the eviction policy for the Virtual Machine|

### Relationships

- Azure Subscription contains one or more Virtual Machines.

        ```
        (AzureSubscription)-[RESOURCE]->(VirtualMachine)
        ```

## AzureDataDisk

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
|write_accelerator_enabled | Specifies whether writeAccelerator should be enabled or disabled on the data disk|
|managed_disk_storage_type | The data disk storage type|

### Relationships

- Azure Virtual Machines are attached to Data Disks.

        ```
        (VirtualMachine)-[ATTACHED_TO]->(AzureDataDisk)
        ```

## AzureDisk

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

### Relationships

- Azure Subscription contains one or more Disks.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureDisk)
        ```

## AzureSnapshot

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
|network_access_policy | Policy for accessing the snapshot via network|
|ostype | The operating system type of the snapshot|
|tier | Performance Tier associated with the snapshot|
|sku | The snapshot sku name|
|zones | The logical zone list for snapshot|

### Relationships

- Azure Subscription contains one or more Snapshots.

        ```
        (AzureSubscription)-[RESOURCE]->(AzureSnapshot)
        ```

## AzureSQLServer

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

### Relationships

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

## AzureServerDNSAlias

Representation of an [AzureServerDNSAlias](https://docs.microsoft.com/en-us/rest/api/sql/serverdnsaliases).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the server DNS alias|
|dnsrecord | The fully qualified DNS record for alias.|

### Relationships

- Azure SQL Server can be used by one or more Azure Server DNS Aliases.

        ```
        (AzureSQLServer)-[USED_BY]->(AzureServerDNSAlias)
        ```

## AzureServerADAdministrator

Representation of an [AzureServerADAdministrator](https://docs.microsoft.com/en-us/rest/api/sql/serverazureadadministrators).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|administratortype | The type of the server administrator.|
|login | The login name of the server administrator.|

### Relationships

- Azure SQL Server can be administered by one or more Azure Server AD Administrators.

        ```
        (AzureSQLServer)-[ADMINISTERED_BY]->(AzureServerADAdministrator)
        ```

## AzureRecoverableDatabase

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

### Relationships

- Azure SQL Server has one or more Azure Recoverable Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRecoverableDatabase)
        ```

## AzureRestorableDroppedDatabase

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

### Relationships

- Azure SQL Server has one or more Azure Restorable Dropped Database.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureRestorableDroppedDatabase)
        ```

## AzureFailoverGroup

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

### Relationships

- Azure SQL Server has one or more Azure Failover Group.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureFailoverGroup)
        ```

## AzureElasticPool

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

### Relationships

- Azure SQL Server has one or more Azure Elastic Pool.

        ```
        (AzureSQLServer)-[RESOURCE]->(AzureElasticPool)
        ```

## AzureSQLDatabase

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

### Relationships

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

## AzureReplicationLink

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

### Relationships

- Azure SQL Database contains one or more Azure Replication Links.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureReplicationLink)
        ```

## AzureDatabaseThreatDetectionPolicy

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

### Relationships

- Azure SQL Database contains a Database Threat Detection Policy.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureDatabaseThreatDetectionPolicy)
        ```

## AzureRestorePoint

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

### Relationships

- Azure SQL Database contains one or more Restore Points.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureRestorePoint)
        ```

## AzureTransparentDataEncryption

Representation of an [AzureTransparentDataEncryption](https://docs.microsoft.com/en-us/rest/api/sql/transparentdataencryptions).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The resource ID|
|name | The name of the resource.|
|location | The resource location.|
|status | The status of the database transparent data encryption.|

### Relationships

- Azure SQL Database contains Transparent Data Encryption.

        ```
        (AzureSQLDatabase)-[CONTAINS]->(AzureTransparentDataEncryption)
        ```

## AzureStorageAccount

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

### Relationships

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

## AzureStorageQueueService

Representation of an [AzureStorageQueueService](https://docs.microsoft.com/en-us/rest/api/storagerp/queueservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue service.|

### Relationships

- Azure Storage Accounts uses one or more Queue Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageQueueService)
        ```
- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

## AzureStorageTableService

Representation of an [AzureStorageTableService](https://docs.microsoft.com/en-us/rest/api/storagerp/tableservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table service.|

### Relationships

- Azure Storage Accounts uses one or more Table Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageTableService)
        ```
- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

## AzureStorageFileService

Representation of an [AzureStorageFileService](https://docs.microsoft.com/en-us/rest/api/storagerp/fileservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the file service.|

### Relationships

- Azure Storage Accounts uses one or more File Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageFileService)
        ```
- Table Service contains one or more file shares.

        ```
        (AzureStorageFileService)-[CONTAINS]->(AzureStorageFileShare)
        ```

## AzureStorageBlobService

Representation of an [AzureStorageBlobService](https://docs.microsoft.com/en-us/rest/api/storagerp/blobservices).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the blob service.|

### Relationships

- Azure Storage Accounts uses one or more Blob Services.

        ```
        (AzureStorageAccount)-[USES]->(AzureStorageBlobService)
        ```
- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```

## AzureStorageQueue

Representation of an [AzureStorageQueue](https://docs.microsoft.com/en-us/rest/api/storagerp/queue).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the queue.|

### Relationships

- Queue Service contains one or more queues.

        ```
        (AzureStorageQueueService)-[CONTAINS]->(AzureStorageQueue)
        ```

## AzureStorageTable

Representation of an [AzureStorageTable](https://docs.microsoft.com/en-us/rest/api/storagerp/table).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Fully qualified resource ID for the resource.|
|type | The type of the resource.|
|name | The name of the table resource.|
|tablename | Table name under the specified account.|

### Relationships

- Table Service contains one or more tables.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageTable)
        ```

## AzureStorageFileShare

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

### Relationships

- File Service contains one or more file shares.

        ```
        (AzureStorageTableService)-[CONTAINS]->(AzureStorageFileShare)
        ```

## AzureStorageBlobContainer

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

### Relationships

- Blob Service contains one or more blob containers.

        ```
        (AzureStorageBlobService)-[CONTAINS]->(AzureStorageBlobContainer)
        ```
