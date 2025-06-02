## Cartography metadata schema

Some Cartography sync jobs write nodes to convey information about the job itself. See https://github.com/lyft/cartography/issues/758 for more background on this.

### SyncMetadata:ModuleSyncMetadata

This is a node to represent metadata about the sync job of a particular module. Its existence indicates that a particular sync job did happen.
The 'types' used here should be actual node labels. For example, if we did sync a particular AWSAccount's S3Buckets,
the `grouptype` is 'AWSAccount', the `groupid` is the particular account's `id`, and the `syncedtype` is 'S3Bucket'.

| Field | Description | Source|
|-------|-------------|------|
|**id**|`{group_type}_{group_id}_{synced_type}`|util.py|
|grouptype| The parent module's type |util.py|
|groupid|The parent module's id|util.py|
|syncedtype|The sub-module's type|util.py|
