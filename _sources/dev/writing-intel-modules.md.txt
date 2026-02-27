# How to write a new intel module

If you want to add a new data type to Cartography, this is the guide for you. We look forward to receiving your PR!

## Before getting started...

Read through and follow the setup steps in [the Cartography developer guide](developer-guide). Learn the basics of
running, testing, and linting your code there.

## The fast way

To get started coding without reading this doc, just copy the structure of our [AWS EMR module](https://github.com/cartography-cncf/cartography/blob/master/cartography/intel/aws/emr.py) and use it as an example. For a longer written explanation of the "how" and "why", read on.

## Configuration and credential management

### Supplying credentials and arguments to your module

If you need to supply an API key or other credential to your Cartography module, we recommend adding a CLI argument. The CLI uses [Typer](https://typer.tiangolo.com/) with options organized into help panels per module. Add your options in `cartography/cli.py` following the existing patterns (e.g., Okta options). Credentials are typically read from environment variables and bound to Cartography's [Config object](https://github.com/cartography-cncf/cartography/blob/master/cartography/config.py) which is available in all modules.

### An important note on validating your commandline args

Note that it is your module's responsibility to validate arguments that you introduce. For example with the Okta module, we [validate](https://github.com/cartography-cncf/cartography/blob/811990606c22a42791d213c7ca845b15f87e47f1/cartography/intel/okta/__init__.py#L37) that `config.okta_api_key` has been defined before attempting to continue.

## Sync = Get, Transform, Load, Cleanup

A cartography intel module consists of one `sync` function. `sync` should call `get`, then `load`, and finally `cleanup`.

### Get

The `get` function [returns data as a list of dicts](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L98)
from a resource provider API, which is GCP in this particular example.

`get` should be "dumb" in the sense that it should not handle retry logic or data
manipulation. It should also raise an exception if it's not able to complete successfully.

### Transform

The `transform` function [manipulates the list of dicts](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L193)
to make it easier to ingest to the graph. `transform` functions are sometimes omitted when a module author decides that the output from the `get` is already in the shape that they need.

We have some best practices on handling transforms:

#### Handling required versus optional fields

We should directly access dicts in cases where not having the data should cause a sync to fail.
For example, if we are transforming AWS data, we definitely need an AWS object's ARN field because it uniquely
identifies the object. Therefore, we should access an object's ARN using `data['arn']` as opposed to
using `data.get('arn')` (the former will raise a `KeyError` if `arn` does not exist and the latter will just return
`None` without an exception).

We _want_ the sync to fail if an important field is not present in our data. The idea here is that
it is better to fail a sync than to add malformed data.

On the other hand, we should use `data.get('SomeField')` if `SomeField` is something optional that can afford to be
`None`.

For the sake of consistency, if a field does not exist, set it to `None` and not `""`.

Neo4j handles fields in `datetime` format, so when a date is returned as a string, it's best to parse it to enable the use of operators during querying.

### Load

[As seen in our AWS EMR example](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/intel/aws/emr.py#L113-L132), the `load` function ingests a list of dicts to Neo4j by calling [cartography.client.core.tx.load()](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/client/core/tx.py#L191-L212):
```python
def load_emr_clusters(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info(f"Loading EMR {len(cluster_data)} clusters for region '{region}' into graph.")
    load(
        neo4j_session,
        EMRClusterSchema(),
        cluster_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )
```

```{tip}
When defining nodes and properties, please follow the naming convention below:
- **Node classes** should end with `Schema`
- **Relationship classes** should end with `Rel`
- **Node property classes** should end with `Properties`
- **Relationship property classes** should end with `RelProperties`
```

#### Defining a node

As an example of a `CartographyNodeSchema`, you can view our [EMRClusterSchema code](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/intel/aws/emr.py#L106-L110):

```python
@dataclass(frozen=True)
class EMRClusterSchema(CartographyNodeSchema):
    label: str = 'EMRCluster'  # The label of the node
    properties: EMRClusterNodeProperties = EMRClusterNodeProperties()  # An object representing all properties on the EMR Cluster node
    sub_resource_relationship: EMRClusterToAWSAccountRel = EMRClusterToAWSAccountRel()
```

An `EMRClusterSchema` object inherits from the `CartographyNodeSchema` class and contains a node label, properties, and connection to its [sub-resource](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/graph/model.py#L216-L228): an `AWSAccount`.

Note that the typehints are necessary for Python dataclasses to work properly.


#### Defining node properties

Here's our [EMRClusterNodeProperties code](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/intel/aws/emr.py#L106-L110):

```python
@dataclass(frozen=True)
class EMRClusterNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('ClusterArn', extra_index=True)
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('Id')
    # ...
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    security_configuration: PropertyRef = PropertyRef('SecurityConfiguration')
```

A `CartographyNodeProperties` object consists of [PropertyRef](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/graph/model.py#L37) objects. `PropertyRefs` tell `querybuilder.build_ingestion_query()` where to find appropriate values for each field from the list of dicts.

For example, `id: PropertyRef = PropertyRef('Id')` above tells the querybuilder to set a field called `id` on the `EMRCluster` node using the value located at key `'id'` on each dict in the list.

As another example, `region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)` tells the querybuilder to set a field called `region` on the `EMRCluster` node using a keyword argument called `Region` supplied to `cartography.client.core.tx.load()`. `set_in_kwargs=True` is useful in cases where we want every object loaded by a single call to `load()` to have the same value for a given attribute.

##### Node property indexes
Cartography uses its data model to automatically create indexes for
- node properties that uniquely identify the node (e.g. `id`)
- node properties are used to connect a node to other nodes (i.e. they are used as part of a `TargetNodeMatcher` on a `CartographyRelSchema`.)
- a node's `lastupdated` field -- this is used to enable faster cleanup jobs

As seen in the above definition for `EMRClusterNodeProperties.arn`, you can also explicitly specify additional indexes for fields that you expect to be queried on by providing `extra_index=True` to the `PropertyRef` constructor:

```python
class EMRClusterNodeProperties(CartographyNodeProperties):
    # ...
    arn: PropertyRef = PropertyRef('ClusterArn', extra_index=True)
```

Index creation is idempotent (we only create them if they don't exist).

See [below](#indexescypher) for more information on indexes.


#### Extra node labels

You can add additional Neo4j labels to your nodes using `ExtraNodeLabels`:

```python
from cartography.models.core.nodes import ExtraNodeLabels

@dataclass(frozen=True)
class EMRClusterSchema(CartographyNodeSchema):
    label: str = 'EMRCluster'
    properties: EMRClusterNodeProperties = EMRClusterNodeProperties()
    sub_resource_relationship: EMRClusterToAWSAccountRel = EMRClusterToAWSAccountRel()

    # Add extra labels to the node
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(['Resource', 'AWSResource'])
```

This creates nodes with multiple labels: `(:EMRCluster:Resource:AWSResource)`. Extra labels are useful for:
- Creating taxonomies (e.g., all AWS resources share an `AWSResource` label)
- Enabling cross-module queries (e.g., find all `Resource` nodes regardless of specific type)
- Ontology mapping

#### Conditional node labels

```{warning}
Conditional labels are a specialized feature primarily used for ontology mapping scenarios where a single data source produces records that map to different semantic types. Most intel modules do not need this feature.
```

Sometimes you want to apply labels only when certain conditions are met. Use `ConditionalNodeLabel` for this:

```python
from cartography.models.core.nodes import ConditionalNodeLabel, ExtraNodeLabels

@dataclass(frozen=True)
class ECRImageSchema(CartographyNodeSchema):
    label: str = "ECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAccountRel = ECRImageToAccountRel()

    # Apply different ontology labels based on the image type
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([
        ConditionalNodeLabel(
            label="Image",
            conditions={"type": "IMAGE"}
        ),
        ConditionalNodeLabel(
            label="ImageAttestation",
            conditions={"type": "IMAGE_ATTESTATION"}
        ),
        ConditionalNodeLabel(
            label="ImageManifestList",
            conditions={"type": "IMAGE_MANIFEST_LIST"}
        ),
    ])
```

**Primary use case: Container Registry Images**

ECR (and other container registries) store different types of artifacts that share the same base schema but have fundamentally different semantic meanings:

| `type` field value | Ontology Label | Description |
|-------------------|----------------|-------------|
| `IMAGE` | `Image` | Standard container image |
| `IMAGE_ATTESTATION` | `ImageAttestation` | SLSA/Sigstore attestation |
| `IMAGE_MANIFEST_LIST` | `ImageManifestList` | Multi-arch manifest list |

Without conditional labels, we cannot accurately map these to distinct ontology types. An `ECRImage` node with `type: "IMAGE_ATTESTATION"` should be labeled as `ImageAttestation` in the ontology, not just generic `Image`.

**How it works:**
- String labels are applied unconditionally to all nodes during ingestion
- `ConditionalNodeLabel` labels are applied in a separate query after ingestion, only to nodes matching all specified conditions
- Conditions use exact string equality and are combined with AND logic
- When conditions change, labels are automatically added or removed on subsequent syncs

**Important notes:**
- Condition values must be strings (e.g., `"true"` not `True`)
- All conditions must match for the label to be applied (AND logic)
- Indexes are automatically created for conditional labels and their condition fields


#### Defining relationships

Relationships can be defined on `CartographyNodeSchema` on either their [sub_resource_relationship](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/graph/model.py#L216-L228) field or their [other_relationships](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/graph/model.py#L230-L237) field (you can find an example of `other_relationships` [here in our test data](https://github.com/cartography-cncf/cartography/blob/4bfafe0e0c205909d119cc7f0bae84b9f6944bdd/tests/data/graph/querybuilder/sample_models/interesting_asset.py#L89-L94)).

As seen above, an `EMRClusterSchema` only has a single relationship defined: an [EMRClusterToAWSAccountRel](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/intel/aws/emr.py#L94-L103):

```python
@dataclass(frozen=True)
# (:EMRCluster)<-[:RESOURCE]-(:AWSAccount)
class EMRClusterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'  # (1)
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(  # (2)
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD  # (3)
    rel_label: str = "RESOURCE"  # (4)
    properties: EMRClusterToAWSAccountRelRelProperties = EMRClusterToAWSAccountRelRelProperties()  #  (5)
```

This class is best described by explaining how it is processed: `build_ingestion_query()` will traverse the `EMRClusterSchema` to its `sub_resource_relationship` field and find the above `EMRClusterToAWSAccountRel` object. With this information, we know to
- draw a relationship to an `AWSAccount` node (1) using the label "`RESOURCE`" (4)
- by matching on the AWSAccount's "`id`" field" (2)
- where the relationship [directionality](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/graph/model.py#L12-L34) is pointed _inward_ toward the EMRCluster (3)
- making sure to define a set of properties for the relationship (5). The [full example RelProperties](https://github.com/cartography-cncf/cartography/blob/e6ada9a1a741b83a34c1c3207515a1863debeeb9/cartography/intel/aws/emr.py#L89-L91) is very short:

```python
@dataclass(frozen=True)
class EMRClusterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
```

```{important}
**Relationship Naming Guidelines**

When naming relationships in Cartography:
- Prefer clear verbs (e.g., OWNS, CONTAINS)
- Avoid ambiguous or passive phrasing (e.g., IS, CAN)
- Use direct and active forms
    - Prefer OWNS over OWNED_BY
    - Prefer CONTAINS over BELONGS_TO

Consistent, action-oriented naming improves graph readability and makes Cypher queries more intuitive.
```

### Sub-Resources relationship

A *sub-resource* is a specific type of composition relationship in which a node "belongs to" a higher-level entity such as an Account, Subscription, etc.

Examples:

* In **AWS**, the parent is typically an `AWSAccount`.
* In **Azure**, it's a `Tenant` or `Subscription`.
* In **GCP**, it's a `GCPProject`.

To define a sub-resource relationship, use the `sub_resource_relationship` property on the node class. It must follow these constraints:

* The target node matcher must have `set_in_kwargs=True` (required for auto-cleanup functionality).
* All `sub_resource_relationship`s must:

  * Use the label `RESOURCE`
  * Have the direction set to `INWARD`
* Each module:

  * **Must have at least one root node** (a node without a `sub_resource_relationship`)
  * **Must have at most one root node**

#### Common Relationship Types

While you're free to define custom relationships, using standardized types improves maintainability and facilitates querying and analysis.

**Composition**

* `(:Parent)-[:CONTAINS]->(:Child)`
* `(:Parent)-[:HAS]->(:Child)`

**Tagging**

* `(:Entity)-[:TAGGED]->(:Tag)`

**Group Membership**

* `(:Element)-[:MEMBER_OF]->(:Group)`
* `(:Element)-[:ADMIN_OF]->(:Group)`
    ```{note}
    If an element is an admin, both relationships (`MEMBER_OF` and `ADMIN_OF`) should be present for consistency.
    ```

**Ownership**

* `(:Entity)-[:OWNS]->(:OtherEntity)`

**Permissions (ACL)**

* `(:Actor)-[:CAN_ACCESS]->(:Entity)`
* `(:Actor)-[:CAN_READ]->(:Entity)`
* `(:Actor)-[:CAN_WRITE]->(:Entity)`
* `(:Actor)-[:CAN_ADD]->(:Entity)`
* `(:Actor)-[:CAN_DELETE]->(:Entity)`

#### The result

And those are all the objects necessary for this example! The resulting query will look something like this:

```cypher
UNWIND $DictList AS item
    MERGE (i:EMRCluster{id: item.Id})
    ON CREATE SET i.firstseen = timestamp()
    SET
        i.lastupdated = $lastupdated,
        i.arn = item.ClusterArn
        // ...

        WITH i, item
        CALL {
            WITH i, item

            OPTIONAL MATCH (j:AWSAccount{id: $AccountId})
            WITH i, item, j WHERE j IS NOT NULL
            MERGE (i)<-[r:RESOURCE]-(j)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r.lastupdated = $lastupdated
        }
```

And that's basically all you need to know to understand how to define your own nodes and relationships using cartography's data objects. For more information, you can view the [object model API documentation](https://github.com/cartography-cncf/cartography/blob/master/cartography/graph/model.py) as a reference.

### Additional concepts

This section explains cartography general patterns, conventions, and design decisions.

#### cartography's `update_tag`:

`cartography`'s global config object carries around an `update_tag` property which is a tag/label associated with the current sync. Cartography's sync code [sets this to a Unix timestamp of when the sync was started](https://github.com/cartography-cncf/cartography/blob/master/cartography/sync.py).

All `cartography` intel modules set the `lastupdated` property on all nodes and all relationships to this `update_tag`.


#### All nodes need these fields

- <a name="id">id</a> - an ID should be a string that uniquely identifies the node. In AWS, this is usually an
    ARN. In GCP, this is usually a partial URI.

    If possible, we should use API-provided fields for IDs and not create our own.
    In some cases though this is unavoidable -
    see [GCPNetworkTag](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema/gcp.md#gcpnetworktag).

    When setting an `id`, ensure that you also include the field name that it came from. For example, since we've
    decided to use `partial_uri`s as an id for a GCPVpc,  we should include both `partial_uri` _and_ `id` on the node.
    This way, a user can tell what fields were used to derive the `id`. This is accomplished [here](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L455-L457)

- `lastupdated` - See [below](#lastupdated-and-firstseen) on how this gets set automatically.
- `firstseen` - See [below](#lastupdated-and-firstseen) on how this gets set automatically.

#### All relationships need these fields

Cartography currently does not create indexes on relationships, so in most cases we should keep relationships lightweight with only these two fields:

- `lastupdated` - See [below](#lastupdated-and-firstseen) on how this gets set automatically.
- `firstseen` - See [below](#lastupdated-and-firstseen) on how this gets set automatically.

#### Run queries only on indexed fields for best performance

In this older example of ingesting GCP VPCs, we connect VPCs with GCPProjects
[based on their id fields](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/intel/gcp/compute.py#L451).
`id`s are indexed, as seen [here](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L45)
and [here](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher#L42).
All of these queries use indexes for faster lookup.

#### indexes.cypher

Older intel modules define indexes in [indexes.cypher](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/indexes.cypher).
By using CartographyNodeSchema and CartographyRelSchema objects, indexes are automatically created so you don't need to update this file!


#### lastupdated and firstseen

On every cartography node and relationship, we set the `lastupdated` field to the `UPDATE_TAG` and `firstseen` field to `timestamp()` (a built-in Neo4j function equivalent to epoch time in milliseconds). This is automatically handled by the cartography object model.

#### One-to-many relationships
We can use the Cartography data model to represent one-to-many relationships. For example, an AWS IAM instance profile
([API docs](https://docs.aws.amazon.com/IAM/latest/APIReference/API_InstanceProfile.html)) maps to one or more roles.

An example instance profile object looks like this:

```python
INSTANCE_PROFILES = [
    {
        "Path": "/",
        "InstanceProfileName": "my-instance-profile",
        "InstanceProfileId": "AIPA4SD",
        "Arn": "arn:aws:iam::1234:instance-profile/my-instance-profile",
        "CreateDate": datetime.datetime(2024, 12, 21, 23, 54, 16),
        "Roles": [
            {
                "Path": "/",
                "RoleName": "role1",
                "RoleId": "AROA4",
                "Arn": "arn:aws:iam::1234:role/role1",
                "CreateDate": datetime.datetime(2024, 12, 21, 6, 53, 29),
            },
            {
                "Path": "/",
                "RoleName": "role2",
                "RoleId": "AROA5",
                "Arn": "arn:aws:iam::1234:role/role2",
                "CreateDate": datetime.datetime(2024, 12, 21, 6, 53, 29),
            },
        ],
    },
]
```

Note that the `Roles` field in this data object is a list of objects (and that this is a one-to-many setup).

Here's how to represent this in the Cartography data model:

  1. Transform the data so that `Roles` becomes a list of IDs and not dicts. Here we will use ARNs. The result should be:

      ```python
      TRANSFORMED_INSTANCE_PROFILES = [
          {
              "Path": "/",
              "InstanceProfileName": "my-instance-profile",
              "InstanceProfileId": "AIPA4SD",
              "Arn": "arn:aws:iam::1234:instance-profile/my-instance-profile",
              "CreateDate": datetime.datetime(2024, 12, 21, 23, 54, 16),
              "Roles": [
                  "arn:aws:iam::1234:role/role1",
                  "arn:aws:iam::1234:role/role2",
              ]
          },
      ]
      ```

  1. Define the InstanceProfile node (irrelevant fields omitted for brevity):

      ```python
      @dataclass(frozen=True)
      class InstanceProfileSchema(CartographyNodeSchema):
          label: str = 'AWSInstanceProfile'
          properties: ...
          sub_resource_relationship: ...
          other_relationships: OtherRelationships = OtherRelationships([
              InstanceProfileToAWSRoleRel(),
          ])
      ```

  1. Define its association with AWS roles

      ```python
      @dataclass(frozen=True)
      class InstanceProfileToAWSRoleRel(CartographyRelSchema):
          target_node_label: str = 'AWSRole'
          target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
              {'arn': PropertyRef('Roles', one_to_many=True)},
          )
          direction: LinkDirection = LinkDirection.OUTWARD
          rel_label: str = "ASSOCIATED_WITH"
          properties: ...
      ```

        The key part is setting `one_to_many=True` in the PropertyRef for the TargetNodeMatcher. This instructs the data model
        to look for AWSRoles in the graph where their `arn` field is in the list pointed to by the `Roles` key on the data dict.

Now we can use the same steps described above in this doc to finish data ingestion.

### MatchLinks

See [the MatchLinks documentation](matchlinks) on how to connect existing nodes in the graph together using Cartography's data model.


### Cleanup

We have just added new nodes and relationships to the graph, and we have also updated previously-added ones
by using `MERGE`. We now need to delete nodes and relationships that no longer exist, and we do this by removing
all nodes and relationships that have `lastupdated` NOT set to the `update_tag` of this current run.

By using Cartography schema objects, a cleanup function is [trivial to write](https://github.com/cartography-cncf/cartography/blob/82e1dd0e851475381ac8f2a9a08027d67ec1d772/cartography/intel/aws/emr.py#L77-L80):

```python
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running EMR cleanup job.")
    cleanup_job = GraphJob.from_node_schema(EMRClusterSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)
```

#### Scoped cleanups

By default, a node_schema has `scoped_cleanup` flag set to True. This means that when we run a clean up job on that
node type, then we will only delete stale nodes that are connected to the current sub-resource being synced. This is
designed for modules like AWS or GCP where there a clear definition of a "tenant"-like object because each account or
project gets synced in one at a time and it doesn't make sense to delete objects outside of the current tenant being
synced.

For some other modules that don't have a clear tenant-like relationship, you can set `scoped_cleanup` to False on the
node_schema. This might make sense for a vuln scanner module where there is no logical tenant object.

#### Hierarchical data and cascade_delete

Some data sources have multi-tier hierarchical structures where nodes own other nodes via RESOURCE relationships. Examples include:

- **GCP**: Organization → Folders → Projects → Compute instances, Storage buckets, etc.
- **GitLab**: Organization → Groups → Projects → Branches, Dependencies, etc.

In Cartography, RESOURCE relationships point from parent to child:

```
(Parent)-[:RESOURCE]->(Child)
```

When a parent node becomes stale and is deleted, you may want its children to be deleted as well. The `cascade_delete` parameter enables this behavior:

```python
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    cleanup_job = GraphJob.from_node_schema(
        MyParentSchema(),
        common_job_parameters,
        cascade_delete=True,  # Also delete children when parent is stale
    )
    cleanup_job.run(neo4j_session)
```

When `cascade_delete=True`, the cleanup query becomes:

```cypher
WHERE n.lastupdated <> $UPDATE_TAG
WITH n LIMIT $LIMIT_SIZE
OPTIONAL MATCH (n)-[:RESOURCE]->(child)
WHERE child IS NULL OR child.lastupdated <> $UPDATE_TAG
DETACH DELETE child, n;
```

**When to use cascade_delete:**

- Use `cascade_delete=True` when child nodes are meaningless without their parent (e.g., GitLab branches without their project)
- Use `cascade_delete=False` (default) when children should persist independently or when another module manages their lifecycle

**Important notes:**

- Only affects direct children (one level deep via `RESOURCE` relationships). Grandchildren require cleaning up intermediate levels first.
- Children that were re-parented in the current sync (matching `UPDATE_TAG`) are protected from deletion.
- Only valid with scoped cleanup (`scoped_cleanup=True`). Unscoped cleanups will raise an error if `cascade_delete=True`.
- Default is `False` for backward compatibility.

#### Legacy notes

Older intel modules still do this process with hand-written cleanup jobs that work like this:

- Delete all old nodes

    You can see this in our [GCP VPCs example](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L4).
    We run `DETACH DELETE` to delete an old node and disconnect it from all other nodes.

- Delete all old relationships

   You can see this in the GCP VPC example [here](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L10)
   and [here](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/data/jobs/cleanup/gcp_compute_vpc_cleanup.json#L16).

   - Q: We just `DETACH DELETE`'d the node. Why do we need to delete the relationships too?

   - A: There are cases where the node may continue to exist but the relationships between it and other nodes have changed.
       Explicitly deleting stale relationships accounts for this case.
       See this [short discussion](https://github.com/cartography-cncf/cartography/pull/124/files#r312277725).

## Error handling principles

- Don't catch the base Exception class when error handling because it makes problems difficult to trace.

- Do catch the narrowest possible class of exception.

- Only catch exceptions when your code can resolve the issue. Otherwise, allow exceptions to bubble up.

## Schema

- Update the [schema](https://github.com/cartography-cncf/cartography/tree/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/docs/schema)
with every change!

## Making tests

- Before making tests, read through and follow the setup steps in [the Cartography developer guide](developer-guide).

- Add fake data for testing at `tests/data`. We can see
the AWS EC2 instance example [here](https://github.com/cartography-cncf/cartography/blob/d42253b9223ced996fa9c51dee3a51942e0a08f4/tests/data/aws/ec2/instances.py#L4).

- If needed, add unit tests to `tests/unit/cartography/intel`. As seen in this GCP [example](https://github.com/lyft/cartography/blob/828ed600f2b14adae9d0b78ef82de0acaf24b86a/tests/unit/cartography/intel/gcp/test_compute.py),
  these tests ensure that `transform*` manipulates the data in expected ways.

- Add integration tests to  `tests/integration/cartography/intel`. See this AWS EC2 instance [example](https://github.com/cartography-cncf/cartography/blob/d42253b9223ced996fa9c51dee3a51942e0a08f4/tests/integration/cartography/intel/aws/ec2/test_ec2_instances.py#L17-L22).
  These tests assume that you have neo4j running at localhost:7687 with no password, and ensure that nodes loaded to the
  graph match your mock data.

## Other

- We prefer and will accept PRs which incrementally add information from a particular data source. Incomplete
representations are OK provided they are consistent over time. For example, we don't sync 100% of AWS resources but the
resources that exist in the graph don't change across syncs.

- Each intel module offers its own view of the graph

    ```{note}
    This best practice is a little less precise, so if you've gotten to this point and you need clarification, just submit your PR and ask us.
    ```

    As much as possible, each intel module should ingest data without assuming that a different module will ingest the
    same data. Explained another way, each module should "offer its own perspective" on the data. We believe doing this
    gives us a more complete graph. Below are some key guidelines clarifying and justifying this design choice.

- It is possible (and encouraged) for more than one intel module to modify the same node type. However, there are two distinct patterns for this:

    **Simple Relationship Pattern**: When data type A only refers to data type B by an ID without providing additional properties about B, we can just define a relationship schema. This way when A is loaded, the relationship schema performs a `MATCH` to find and connect to existing nodes of type B.

    For example, when an RDS instance refers to EC2 security groups by ID, we create a relationship from the RDS instance to the security group nodes, since the RDS API doesn't provide additional properties about the security groups beyond their IDs.

    ```python
    # RDS Instance refers to Security Groups by ID only
    @dataclass(frozen=True)
    class RDSInstanceToSecurityGroupRel(CartographyRelSchema):
        target_node_label: str = "EC2SecurityGroup"
        target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
            "id": PropertyRef("SecurityGroupId"),  # Just the ID, no additional properties
        })
        direction: LinkDirection = LinkDirection.OUTWARD
        rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
        properties: RDSInstanceToSecurityGroupRelProperties = RDSInstanceToSecurityGroupRelProperties()
    ```

    **Composite Node Pattern**: When a data type `A` refers to another data type `B` and offers additional fields about `B` that `B` doesn't have itself, we should define a composite node schema. This composite node would be named "`BASchema`" to denote that it's a "`B`" object as known by an "`A`" object. When loaded, the composite node schema targets the same node label as the primary `B` schema, allowing the loading system to perform a `MERGE` operation that combines properties from both sources.

    For example, in the AWS EC2 module, we have both `EBSVolumeSchema` (from the EBS API) and `EBSVolumeInstanceSchema` (from the EC2 Instance API). The EC2 Instance API provides additional properties about EBS volumes that the EBS API doesn't have, such as `deleteontermination`. Both schemas target the same `EBSVolume` node label, allowing the node to accumulate properties from both sources.

    ```python
    # EC2 Instance provides additional properties about EBS Volumes
    @dataclass(frozen=True)
    class EBSVolumeInstanceProperties(CartographyNodeProperties):
        id: PropertyRef = PropertyRef("VolumeId")
        arn: PropertyRef = PropertyRef("Arn", extra_index=True)
        lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
        # Additional property that EBS API doesn't have
        deleteontermination: PropertyRef = PropertyRef("DeleteOnTermination")

    @dataclass(frozen=True)
    class EBSVolumeInstanceSchema(CartographyNodeSchema):
        label: str = "EBSVolume"  # Same label as EBSVolumeSchema
        properties: EBSVolumeInstanceProperties = EBSVolumeInstanceProperties()
        sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
        # ... other relationships
    ```

    The key distinction is whether the referring module provides additional properties about the target entity. If it does, use a composite node schema. If it only provides IDs, use a simple relationship schema.

    In case you're curious, here's some [historical context](https://github.com/cartography-cncf/cartography/issues/1210) on how we got here.
