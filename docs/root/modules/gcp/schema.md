## GCP Schema

### GCPOrganization

Representation of a GCP [Organization](https://cloud.google.com/resource-manager/reference/rest/v1/organizations) object.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AWSAccount, AzureTenant).

| Field          | Description                                                                                                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| firstseen      | Timestamp of when a sync job first discovered this node                                                                                                                                 |
| lastupdated    | Timestamp of the last time the node was updated                                                                                                                                         |
| id             | The name of the GCP Organization, e.g. "organizations/1234"                                                                                                                             |
| displayname    | The "friendly name", e.g. "My Company"                                                                                                                                                  |
| lifecyclestate | The organization's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/organizations#LifecycleState). |

#### Relationships

- GCPOrganizations contain GCPFolders.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPFolder)
    ```

- GCPOrganizations can contain GCPProjects.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPProject)
    ```

### GCPFolder

 Representation of a GCP [Folder](https://cloud.google.com/resource-manager/reference/rest/v2/folders).  An additional helpful reference is the [Google Compute Platform resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy).

| Field          | Description                                                                                                                                                                 |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| firstseen      | Timestamp of when a sync job first discovered this node                                                                                                                     |
| lastupdated    | Timestamp of the last time the node was updated                                                                                                                             |
| id             | The name of the folder, e.g. "folders/1234"                                                                                                                                 |
| foldername     | The name of the folder, e.g. "folders/1234"                                                                                                                                 |
| displayname    | A friendly name of the folder, e.g. "My Folder".                                                                                                                            |
| lifecyclestate | The folder's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v2/folders#LifecycleState). |
| parent_org     | If the folder's parent is an organization, this field contains the organization ID, e.g. "organizations/1234"                                                               |
| parent_folder  | If the folder's parent is another folder, this field contains the folder ID, e.g. "folders/5678"                                                                            |


#### Relationships

- GCPFolders are sub-resources of GCPOrganizations.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPFolder)
    ```

- GCPFolders can have parent GCPOrganizations.

    ```
    (GCPFolder)-[PARENT]->(GCPOrganization)
    ```

- GCPFolders can have parent GCPFolders.

    ```
    (GCPFolder)-[PARENT]->(GCPFolder)
    ```

- GCPFolders can contain GCPProjects

    ```
    (GCPProject)-[PARENT]->(GCPFolder)
    ```

- GCPFolders can contain other GCPFolders.

    ```
    (GCPFolder)-[PARENT]->(GCPFolder)
    ```

### GCPProject

 Representation of a GCP [Project](https://cloud.google.com/resource-manager/reference/rest/v1/projects).  An additional helpful reference is the [Google Compute Platform resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy).

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AWSAccount, AzureTenant).

 | Field          | Description                                                                                                                                                                   |
 | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
 | firstseen      | Timestamp of when a sync job first discovered this node                                                                                                                       |
 | lastupdated    | Timestamp of the last time the node was updated                                                                                                                               |
 | id             | The ID of the project, e.g. "sys-12345"                                                                                                                                       |
 | projectid      | The ID of the project, e.g. "sys-12345"                                                                                                                                       |
 | projectnumber  | The number uniquely identifying the project, e.g. '987654'                                                                                                                    |
 | displayname    | A friendly name of the project, e.g. "MyProject".                                                                                                                             |
 | lifecyclestate | The project's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/projects#LifecycleState). |
 | parent_org     | If the project's parent is an organization, this field contains the organization ID, e.g. "organizations/1234"                                                                |
 | parent_folder  | If the project's parent is a folder, this field contains the folder ID, e.g. "folders/5678"                                                                                  |

 ### Relationships

- GCPProjects are sub-resources of GCPOrganizations.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPProject)
    ```

- GCPProjects can have a parent GCPOrganization.

    ```
    (GCPProject)-[PARENT]->(GCPOrganization)
    ```

- GCPProjects can have a parent GCPFolder.

    ```
    (GCPProject)-[PARENT]->(GCPFolder)
    ```

- GCPVpcs are part of GCPProjects

    ```
    (GCPProject)-[RESOURCE]->(GCPVpc)
    ```


### GCPBucket
Representation of a GCP [Storage Bucket](https://cloud.google.com/storage/docs/json_api/v1/buckets).

> **Ontology Mapping**: This node has the extra label `ObjectStorage` to enable cross-platform queries for object storage across different systems (e.g., S3Bucket, AzureStorageBlobContainer).

| Field                         | Description                                                                                                                                                                                                                                         |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| firstseen                     | Timestamp of when a sync job first discovered this node |
| lastupdated                   | Timestamp of the last time the node was updated |
| id                            | The ID of the storage bucket, e.g. "bucket-12345" |
| projectnumber                 | The number uniquely identifying the project associated with the storage bucket, e.g. '987654' |
| self_link                     | The URI of the storage bucket |
| kind                          | The kind of item this is. For storage buckets, this is always storage#bucket |
| location                      | The location of the bucket. Object data for objects in the bucket resides in physical storage within this region. Defaults to US. See [Cloud Storage bucket locations](https://cloud.google.com/storage/docs/locations) for the authoritative list. |
| location_type                 | The type of location that the bucket resides in, as determined by the `location` property |
| meta_generation               | The metadata generation of this bucket |
| storage_class                 | The bucket's default storage class, used whenever no `storageClass` is specified for a newly-created object. For more information, see [storage classes](https://cloud.google.com/storage/docs/storage-classes) |
| time_created                  | The creation time of the bucket in RFC 3339 format |
| retention_period              | The period of time, in seconds, that objects in the bucket must be retained and cannot be deleted, overwritten, or archived |
| iam_config_bucket_policy_only | The bucket's [Bucket Policy Only](https://cloud.google.com/storage/docs/bucket-policy-only) configuration |
| owner_entity                  | The entity, in the form `project-owner-projectId` |
| owner_entity_id               | The ID for the entity |
| versioning_enabled            | The bucket's versioning configuration (if set to `True`, versioning is fully enabled for this bucket) |
| log_bucket                    | The destination bucket where the current bucket's logs should be placed |
| requester_pays                | The bucket's billing configuration (if set to true, Requester Pays is enabled for this bucket) |
| default_kms_key_name          | A Cloud KMS key that will be used to encrypt objects inserted into this bucket, if no encryption method is specified |

#### Relationships

- GCPBuckets are part of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPBucket)
    ```

- GCPBuckets can be labelled with GCPBucketLabels.

    ```
    (GCPBucket)<-[LABELLED]-(GCPBucketLabels)
    ```

- GCPPrincipals with appropriate permissions can read from GCP buckets. Created from [gcp_permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml).

    ```
    (GCPPrincipal)-[CAN_READ]->(GCPBucket)
    ```

- GCPPrincipals with appropriate permissions can write to GCP buckets. Created from [gcp_permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml).

    ```
    (GCPPrincipal)-[CAN_WRITE]->(GCPBucket)
    ```

- GCPPrincipals with appropriate permissions can delete from GCP buckets. Created from [gcp_permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/gcp_permission_relationships.yaml).

    ```
    (GCPPrincipal)-[CAN_DELETE]->(GCPBucket)
    ```


### GCPDNSZone

Representation of a GCP [DNS Zone](https://cloud.google.com/dns/docs/reference/v1/).

| Field      | Description                                             |
| ---------- | ------------------------------------------------------- |
| created_at | The date and time the zone was created                  |
| description              | An optional description of the zone|
| dns_name | The DNS name of this managed zone, for instance "example.com.". |
| firstseen  | Timestamp of when a sync job first discovered this node |
| **id**                   |Unique identifier|
| name       | The name of the zone                                    |
| nameservers |Virtual name servers the zone is delegated to |
| visibility | The zone's visibility: `public` zones are exposed to the Internet, while `private` zones are visible only to Virtual Private Cloud resources.|


#### Relationships

- GKEClusters are resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPDNSZone)
    ```


### GCPBucketLabel:Label
Representation of a GCP [Storage Bucket Label](https://cloud.google.com/storage/docs/key-terms#bucket-labels).  This node contains a key-value pair.

 | Field       | Description                                                         |
 | ----------- | ------------------------------------------------------------------- |
 | firstseen   | Timestamp of when a sync job first discovered this node             |
 | lastupdated | Timestamp of the last time the node was updated                     |
 | id          | The ID of the bucket label.  Takes the form "GCPBucketLabel\_{key}." |
 | key         | The key of the bucket label.                                        |
 | value       | The value of the bucket label.                                      |

- GCPBuckets can be labeled with GCPBucketLabels.

    ```
    (GCPBucket)<-[LABELED]-(GCPBucketLabels)
    ```


### GCPInstance

Representation of a GCP [Instance](https://cloud.google.com/compute/docs/reference/rest/v1/instances).  Additional references can be found in the [official documentation]( https://cloud.google.com/compute/docs/concepts).

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different systems (e.g., EC2Instance, AzureVirtualMachine, DODroplet).

| Field            | Description |
| ---------------- | ----------- |
| firstseen        | Timestamp of when a sync job first discovered this node |
| lastupdated      | Timestamp of the last time the node was updated |
| id               | The partial resource URI representing this instance. Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}`. |
| partial_uri      | Same as `id` above. |
| self_link        | The full resource URI representing this instance. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}` |
| instancename     | The name of the instance, e.g. "my-instance" |
| zone_name        | The zone that the instance is installed on |
| hostname         | If present, the hostname of the instance |
| exposed_internet | Set to True  with `exposed_internet_type = 'direct'` if there is an 'allow' IPRule attached to one of the instance's ingress firewalls with the following conditions:  The 'allow' IpRule allows traffic from one or more TCP ports, and the 'allow' IpRule is not superceded by a 'deny' IPRule (in GCP, a firewall rule of priority 1 gets applied ahead of a firewall rule of priority 100, and 'deny' rules of the same priority are applied ahead of 'allow' rules) |
| exposed_internet_type | A string indicating the type of internet exposure. Currently only `'direct'` is supported (exposed via firewall rules). Set by the `gcp_compute_asset_inet_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/gcp_compute_asset_inet_exposure.json). |
| status           | The [GCP Instance Lifecycle](https://cloud.google.com/compute/docs/instances/instance-life-cycle) state of the instance |
#### Relationships

- GCPInstances are resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPInstance)
    ```

- GCPNetworkInterfaces are attached to GCPInstances

    ```
    (GCPInstance)-[NETWORK_INTERFACE]->(GCPNetworkInterface)
    ```

- GCP Instances may be members of one or more GCP VPCs.

    ```
    (GCPInstance)-[:MEMBER_OF_GCP_VPC]->(GCPVpc)
    ```

    This relationship is created by an [analysis job](../../dev/writing-analysis-jobs.html)
    defined at `cartography/data/jobs/analysis/gcp_compute_instance_vpc_analysis.json`.

    Also note that this relationship is a shortcut for:

    ```
    (GCPInstance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:PART_OF_SUBNET]->(GCPSubnet)<-[:RESOURCE]-(GCPVpc)
    ```

- GCP Instances may have GCP Tags defined on them for use in [network firewall routing](https://cloud.google.com/blog/products/gcp/labelling-and-grouping-your-google-cloud-platform-resources).

    ```
    (GCPInstance)-[:TAGGED]->(GCPNetworkTag)
    ```

- GCP Firewalls allow ingress to GCP instances.
    ```
    (GCPFirewall)-[:FIREWALL_INGRESS]->(GCPInstance)
    ```

    Note that this relationship is a shortcut for:
    ```
    (vpc:GCPVpc)<-[MEMBER_OF_GCP_VPC]-(GCPInstance)-[TAGGED]->(GCPNetworkTag)-[TARGET_TAG]-(GCPFirewall{direction: 'INGRESS'})<-[RESOURCE]-(vpc)
    ```

    as well as
    ```
    MATCH (fw:GCPFirewall{direction: 'INGRESS', has_target_service_accounts: False}})
    WHERE NOT (fw)-[TARGET_TAG]->(GCPNetworkTag)
    MATCH (GCPInstance)-[MEMBER_OF_GCP_VPC]->(GCPVpc)-[RESOURCE]->(fw)
    ```

### GCPNetworkTag

Representation of a Tag defined on a GCP Instance or GCP Firewall.  Tags are defined on GCP instances for use in [network firewall routing](https://cloud.google.com/blog/products/gcp/labelling-and-grouping-your-google-cloud-platform-resources).

| Field       | Description                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| firstseen   | Timestamp of when a sync job first discovered this node                                                    |
| lastupdated | Timestamp of the last time the node was updated                                                            |
| id          | GCP doesn't define a resource URI for Tags so we define this as `{instance resource URI}/tags/{tag value}` |
| tag_id      | same as `id`                                                                                               |
| value       | The actual value of the tag                                                                                |

#### Relationships

- GCP Instances can be labeled with tags.
    ```
    (GCPInstance)-[:TAGGED]->(GCPNetworkTag)
    ```

- GCP Firewalls can be labeled with tags to direct traffic to or deny traffic to labeled GCPInstances
    ```
    (GCPFirewall)-[:TARGET_TAG]->(GCPNetworkTag)
    ```

- GCPNetworkTags are defined on a VPC and only have effect on assets in that VPC

    ```
    (GCPVpc)-[DEFINED_IN]->(GCPNetworkTag)
    ```

### GCPVpc

Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/).  In GCP documentation this is also known simply as a "Network" object.

| Field                      | Description |
| -------------------------- | ----------- |
| firstseen                  | Timestamp of when a sync job first discovered this node |
| lastupdated                | Timestamp of the last time the node was updated |
| id                         | The partial resource URI representing this VPC.  Has the form `projects/{project_name}/global/networks/{vpc name}`. |
| partial_uri                | Same as `id` |
| self_link                  | The full resource URI representing this VPC. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}` |
| name                       | The name of the VPC |
| project_id                 | The project ID that this VPC belongs to |
| auto_create_subnetworks    | When set to true, the VPC network is created in "auto" mode. When set to false, the VPC network is created in "custom" mode.  An auto mode VPC network starts with one subnet per region. Each subnet has a predetermined range as described in [Auto mode VPC network IP ranges](https://cloud.google.com/vpc/docs/vpc#ip-ranges). |
| routing_confg_routing_mode | The network-wide routing mode to use. If set to REGIONAL, this network's Cloud Routers will only advertise routes with subnets of this network in the same region as the router. If set to GLOBAL, this network's Cloud Routers will advertise routes with all subnets of this network, across regions. |
| description                | A description for the VPC |

#### Relationships

- GCPVpcs are part of projects

    ```
    (:GCPProject)-[:RESOURCE]->(:GCPVpc)
    ```

- GCPVpcs contain GCPSubnets

    ```
    (:GCPVpc)-[:HAS]->(:GCPSubnet)
    ```

- GCPSubnets are part of GCP VPCs

    ```
    (:GCPVpc)-[:RESOURCE]->(:GCPSubnet)
    ```

- GCPNetworkTags are defined on a VPC and only have effect on assets in that VPC

    ```
    (:GCPVpc)-[:DEFINED_IN]->(:GCPNetworkTag)
    ```

- GCP Instances may be members of one or more GCP VPCs.

    ```
    (:GCPInstance)-[:MEMBER_OF_GCP_VPC]->(:GCPVpc)
    ```

    Also note that this relationship is a shortcut for:

    ```
    (:GCPInstance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:PART_OF_SUBNET]->(:GCPSubnet)<-[:RESOURCE]-(:GCPVpc)
    ```

### GCPNetworkInterface

Representation of a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

| Field       | Description |
| ----------- | ----------- |
| firstseen   | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id          | A partial resource URI representing this network interface.  Note: GCP does not define a partial resource URI for network interfaces, so we create one so we can uniquely identify GCP network interfaces.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}`. |
| nic_id      | Same as `id` |
| name        | The name of the network interface |
| private_ip  | The private IP address of this network interface.  This IP is valid on the network interface's VPC. |

#### Relationships

- GCPNetworkInterfaces are attached to GCPInstances

    ```
    (GCPInstance)-[NETWORK_INTERFACE]->(GCPNetworkInterface)
    ```

- GCPNetworkInterfaces are connected to GCPSubnets

    ```
    (GCPNetworkInterface)-[PART_OF_SUBNET]->(GCPSubnet)
    ```

- GCPNetworkInterfaces have GCPNicAccessConfig objects defined on them

    ```
    (GCPNetworkInterface)-[RESOURCE]->(GCPNicAccessConfig)
    ```


### GCPNicAccessConfig

Representation of the AccessConfig object on a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

| Field                  | Description |
| ---------------------- | ----------- |
| firstseen              | Timestamp of when a sync job first discovered this node |
| lastupdated            | Timestamp of the last time the node was updated |
| id                     | A partial resource URI representing this AccessConfig.  Note: GCP does not define a partial resource URI for AccessConfigs, so we create one so we can uniquely identify GCP network interface access configs.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}/accessconfigs/{access config type}`. |
| partial_uri            | Same as `id` |
| type                   | The type of configuration. GCP docs say: "The default and only option is ONE_TO_ONE_NAT." |
| name                   | The name of this access configuration. The default and recommended name is External NAT, but you can use any arbitrary string, such as My external IP or Network Access. |
| public_ip              | The external IP associated with this instance |
| set_public_ptr         | Specifies whether a public DNS 'PTR' record should be created to map the external IP address of the instance to a DNS domain name. |
| public_ptr_domain_name | The DNS domain name for the public PTR record. You can set this field only if the setPublicPtr field is enabled. |
| network_tier           | This signifies the networking tier used for configuring this access configuration and can only take the following values: PREMIUM, STANDARD. |

#### Relationships

- GCPNetworkInterfaces have GCPNicAccessConfig objects defined on them

    ```
    (GCPNetworkInterface)-[RESOURCE]->(GCPNicAccessConfig)
    ```


### GCPRecordSet

Representation of a GCP [Resource Record Set](https://cloud.google.com/dns/docs/reference/v1/).

| Field      | Description                                             |
| ---------- | ------------------------------------------------------- |
| data | Data contained in the record
| firstseen  | Timestamp of when a sync job first discovered this node |
| **id**                   |Composite key `name|type|zone_id` to ensure uniqueness across record types and zones|
| name       | The name of the Resource Record Set                                    |
| type | The identifier of a supported record type. See the list of [Supported DNS record types](https://cloud.google.om/dns/docs/overview#supported_dns_record_types).
| ttl | Number of seconds that this ResourceRecordSet can be cached by resolvers.


#### Relationships

- GCPRecordSets are records of GCPDNSZones.

    ```
    (GCPDNSZone)-[HAS_RECORD]->(GCPRecordSet)
    ```


### GCPSubnet

Representation of a GCP [Subnetwork](https://cloud.google.com/compute/docs/reference/rest/v1/subnetworks).

| Field                    | Description                                                                                                                                                                                        |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| firstseen                | Timestamp of when a sync job first discovered this node                                                                                                                                            |
| lastupdated              | Timestamp of the last time the node was updated                                                                                                                                                    |
| id                       | A partial resource URI representing this Subnet.  Has the form `projects/{project}/regions/{region}/subnetworks/{subnet name}`.                                                                    |
| partial_uri              | Same as `id`                                                                                                                                                                                       |
| self_link                | The full resource URI representing this subnet. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`                                                                                 |
| project_id               | The project ID that this Subnet belongs to                                                                                                                                                         |
| name                     | The name of this Subnet                                                                                                                                                                            |
| region                   | The region of this Subnet                                                                                                                                                                          |
| gateway_address          | Gateway IP address of this Subnet                                                                                                                                                                  |
| ip_cidr_range            | The CIDR range covered by this Subnet                                                                                                                                                              |
| vpc_partial_uri          | The partial URI of the VPC that this Subnet is a part of                                                                                                                                           |
| private_ip_google_access | Whether the VMs in this subnet can access Google services without assigned external IP addresses. This field can be both set at resource creation time and updated using setPrivateIpGoogleAccess. |

#### Relationships

- GCPSubnets are resources of GCPProjects (primary organizational relationship)

    ```
    (:GCPProject)-[:RESOURCE]->(:GCPSubnet)
    ```

- GCPSubnets are part of GCP VPCs

    ```
    (:GCPVpc)-[:HAS]->(:GCPSubnet)
    ```

- GCPNetworkInterfaces are connected to GCPSubnets

    ```
    (:GCPNetworkInterface)-[:PART_OF_SUBNET]->(:GCPSubnet)
    ```


### GCPFirewall

Representation of a GCP [Firewall](https://cloud.google.com/compute/docs/reference/rest/v1/firewalls/list).

| Field                       | Description |
| --------------------------- | ----------- |
| firstseen                   | Timestamp of when a sync job first discovered this node |
| lastupdated                 | Timestamp of the last time the node was updated |
| id                          | A partial resource URI representing this Firewall. |
| partial_uri                 | Same as `id` |
| direction                   | Either 'INGRESS' for inbound or 'EGRESS' for outbound |
| disabled                    | Whether this firewall object is disabled |
| priority                    | The priority of this firewall rule from 1 (apply this first)-65535 (apply this last) |
| self_link                   | The full resource URI to this firewall |
| has_target_service_accounts | Set to True if this Firewall has target service accounts defined. This field is currently a placeholder for future functionality to add GCP IAM objects to Cartography. If True, this firewall rule will only apply to GCP instances that use the specified target service account. |

#### Relationships

- Firewalls belong to VPCs

    ```
    (GCPVpc)-[RESOURCE]->(GCPFirewall)
    ```

- Firewalls define rules that allow traffic

    ```
    (GCPIpRule)-[ALLOWED_BY]->(GCPFirewall)
    ```

- Firewalls define rules that deny traffic

    ```
    (GCPIpRule)-[DENIED_BY]->(GCPFirewall)
    ```

- GCP Firewalls can be labeled with tags to direct traffic to or deny traffic to labeled GCPInstances
    ```
    (GCPFirewall)-[:TARGET_TAG]->(GCPNetworkTag)
    ```

- GCP Firewalls allow ingress to GCP instances.
    ```
    (GCPFirewall)-[:FIREWALL_INGRESS]->(GCPInstance)
    ```

    Note that this relationship is a shortcut for:
    ```
    (vpc:GCPVpc)<-[MEMBER_OF_GCP_VPC]-(GCPInstance)-[TAGGED]->(GCPNetworkTag)-[TARGET_TAG]-(GCPFirewall{direction: 'INGRESS'})<-[RESOURCE]-(vpc)
    ```

    as well as
    ```
    MATCH (fw:GCPFirewall{direction: 'INGRESS', has_target_service_accounts: False}})
    WHERE NOT (fw)-[TARGET_TAG]->(GCPNetworkTag)
    MATCH (GCPInstance)-[MEMBER_OF_GCP_VPC]->(GCPVpc)-[RESOURCE]->(fw)
    ```


### GCPForwardingRule

Representation of GCP [Forwarding Rules](https://cloud.google.com/compute/docs/reference/rest/v1/forwardingRules/list) and [Global Forwarding Rules](https://cloud.google.com/compute/docs/reference/rest/v1/globalForwardingRules/list).

> **Ontology Mapping**: This node has the extra label `LoadBalancer` to enable cross-platform queries for load balancers across different systems (e.g., AWSLoadBalancerV2, LoadBalancer, AzureLoadBalancer).

| Field                 | Description                                                                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| firstseen             | Timestamp of when a sync job first discovered this node                                                                                              |
| lastupdated           | Timestamp of the last time the node was updated                                                                                                      |
| id                    | A partial resource URI representing this Forwarding Rule                                                                                             |
| partial_uri           | Same as `id`                                                                                                                                         |
| ip_address            | IP address that this Forwarding Rule serves                                                                                                          |
| ip_protocol           | IP protocol to which this rule applies                                                                                                               |
| load_balancing_scheme | Specifies the Forwarding Rule type                                                                                                                   |
| name                  | Name of the Forwarding Rule                                                                                                                          |
| network               | A partial resource URI of the network this Forwarding Rule belongs to                                                                                |
| port_range            | Port range used in conjunction with a target resource. Only packets addressed to ports in the specified range will be forwarded to target configured |
| ports                 | Ports to forward to a backend service. Only packets addressed to these ports are forwarded to the backend services configured                        |
| project_id            | The project ID that this Forwarding Rule belongs to                                                                                                  |
| region                | The region of this Forwarding Rule                                                                                                                   |
| self_link             | Server-defined URL for the resource                                                                                                                  |
| subnetwork            | A partial resource URI of the subnetwork this Forwarding Rule belongs to                                                                             |
| target                | A partial resource URI of the target resource to receive the traffic                                                                                 |

#### Relationships

- GCPForwardingRules can be a resource of a GCPVpc.

    ```
    (GCPVpc)-[RESOURCE]->(GCPForwardingRule)
    ```

- GCPForwardingRules can be a resource of a GCPSubnet.

    ```
    (GCPSubnet)-[RESOURCE]->(GCPForwardingRule)
    ```

### GKECluster

Representation of a GCP [GKE Cluster](https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/).

| Field                      | Description                                                                                                                                                                                                       |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| basic_auth                 | Set to `True` if both `masterauth_username` and `masterauth_password` are set                                                                                                                                     |
| created_at                 | The date and time the cluster was created                                                                                                                                                                         |
| cluster_ipv4cidr           | The IP address range of the container pods in the cluster                                                                                                                                                         |
| current_master_version     | The current software version of the master endpoint                                                                                                                                                               |
| database_encryption        | Configuration of etcd encryption                                                                                                                                                                                  |
| description                | An optional description of the cluster                                                                                                                                                                            |
| endpoint                   | The IP address of the cluster's master endpoint. The endpoint can be accessed from the internet at https://username:password@endpoint/                                                                            |
| exposed_internet           | Set to `True` if at least among `private_nodes`, `private_endpoint_enabled`, or `master_authorized_networks` are disabled                                                                                         |
| firstseen                  | Timestamp of when a sync job first discovered this node                                                                                                                                                           |
| **id**                     | Same as `self_link`                                                                                                                                                                                               |
| initial_version            | The initial Kubernetes version for the cluster                                                                                                                                                                    |
| location                   | The name of the Google Compute Engine zone or region in which the cluster resides                                                                                                                                 |
| logging_service            | The logging service used to write logs. Available options: `logging.googleapis.com/kubernetes`, `logging.googleapis.com`, `none`                                                                                  |
| master_authorized_networks | If enabled, it disallows all external traffic to access Kubernetes master through HTTPS except traffic from the given CIDR blocks, Google Compute Engine Public IPs and Google Prod IPs                           |
| masterauth_username        | The username to use for HTTP basic authentication to the master endpoint. For clusters v1.6.0 and later, basic authentication can be disabled by leaving username unspecified (or setting it to the empty string) |
| masterauth_password        | The password to use for HTTP basic authentication to the master endpoint. If a password is provided for cluster creation, username must be non-empty                                                              |
| monitoring_service         | The monitoring service used to write metrics. Available options: `monitoring.googleapis.com/kubernetes`, `monitoring.googleapis.com`, `none`                                                                      |
| name                       | The name of the cluster                                                                                                                                                                                           |
| network                    | The name of the Google Compute Engine network to which the cluster is connected                                                                                                                                   |
| network_policy             | Set to `True` if a network policy provider has been enabled                                                                                                                                                       |
| private_endpoint_enabled   | Whether the master's internal IP address is used as the cluster endpoint                                                                                                                                          |
| private_endpoint           | The internal IP address of the cluster's master endpoint                                                                                                                                                          |
| private_nodes              | If enabled, all nodes are given only private addresses and communicate with the master via private networking                                                                                                     |
| public_endpoint            | The external IP address of the cluster's master endpoint                                                                                                                                                          |
| **self_link**              | Server-defined URL for the resource                                                                                                                                                                               |
| services_ipv4cidr          | The IP address range of the Kubernetes services in the cluster                                                                                                                                                    |
| shielded_nodes             | Whether Shielded Nodes are enabled                                                                                                                                                                                |
| status                     | The current status of the cluster                                                                                                                                                                                 |
| subnetwork                 | The name of the Google Compute Engine subnetwork to which the cluster is connected                                                                                                                                |
| zone                       | The name of the Google Compute Engine zone in which the cluster resides                                                                                                                                           |


#### Relationships

- GKEClusters are resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GKECluster)
    ```


### GCPIpRule::IpPermissionInbound::IpRule

A GCPIpRule node represents an inbound GCP firewall IP rule. It carries semantic labels for compatibility with generic inbound rule queries.

> **Ontology Mapping**: This node has the extra labels `IpPermissionInbound` and `IpRule` to preserve semantic compatibility.

| Field       | Description                                                 |
| ----------- | ----------------------------------------------------------- |
| **ruleid**  | `{firewall_partial_uri}/{rule_type}/{port_range}{protocol}` |
| firstseen   | Timestamp of when a sync job first discovered this node     |
| lastupdated | Timestamp of the last time the node was updated             |
| protocol    | The protocol this rule applies to                           |
| fromport    | Lowest port in the range defined by this rule               |
| toport      | Highest port in the range defined by this rule              |

#### Relationships

- GCP firewall rules are defined on GCPIpRange objects.

	```
	(GCPIpRange)-[MEMBER_OF_IP_RULE]->(GCPIpRule)
	```

- Firewalls define rules that allow traffic

    ```
    (GCPIpRule)-[ALLOWED_BY]->(GCPFirewall)
    ```

- Firewalls define rules that deny traffic

    ```
    (GCPIpRule)-[DENIED_BY]->(GCPFirewall)
    ```

### GCPIpRange::IpRange

Representation of an IP range or subnet.

> **Ontology Mapping**: This node has the extra label `IpRange` to preserve cross-platform semantics for generic IP ranges.

| Field       | Description                                                              |
| ----------- | ------------------------------------------------------------------------ |
| firstseen   | Timestamp of when a sync job first discovered this node                  |
| lastupdated | Timestamp of the last time the node was updated                          |
| id          | CIDR notation for the IP range. E.g. "0.0.0.0/0" for the whole internet. |

#### Relationships

- GCPIpRanges are members of GCPIpRules.

	```
	(GCPIpRange)-[MEMBER_OF_IP_RULE]->(GCPIpRule)
	```

### GCPServiceAccount

Representation of a GCP [Service Account](https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts).

| Field          | Description                                                                                     |
| -------------- | ----------------------------------------------------------------------------------------------- |
| id             | The unique identifier for the service account.                                                  |
| email          | The email address associated with the service account.                                          |
| displayName    | The display name of the service account.                                                        |
| oauth2ClientId | The OAuth2 client ID associated with the service account.                                       |
| uniqueId       | The unique ID of the service account.                                                           |
| disabled       | A boolean indicating if the service account is disabled.                                        |
| lastupdated    | The timestamp of the last update.                                                               |
| projectId      | The ID of the GCP project to which the service account belongs.                                 |

#### Relationships

- GCPServiceAccounts are resources of GCPProjects.

    ```
    (GCPServiceAccount)-[RESOURCE]->(GCPProject)
    ```

### GCPRole

Representation of a GCP [Role](https://cloud.google.com/iam/docs/reference/rest/v1/organizations.roles).

Roles exist at different levels in the GCP hierarchy and are synced separately:
- **Predefined/Basic roles** (`roles/*`) - Global roles defined by Google, synced at the organization level
- **Custom organization roles** (`organizations/*/roles/*`) - Custom roles defined at the organization level
- **Custom project roles** (`projects/*/roles/*`) - Custom roles defined at the project level

**Important**: Organization-level roles (predefined + custom org) and project-level roles (custom project) have different sub-resource relationships:
- Organization-level roles are sub-resources of `GCPOrganization`
- Project-level roles are sub-resources of `GCPProject`

| Field               | Description                                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| id                  | The unique identifier for the role (same as name).                                                    |
| name                | The name of the role (e.g., `roles/editor`, `organizations/123/roles/custom`, `projects/abc/roles/custom`). |
| title               | The human-readable title of the role.                                                                 |
| description         | A description of the role.                                                                            |
| deleted             | A boolean indicating if the role is deleted.                                                          |
| etag                | The ETag of the role for optimistic concurrency control.                                              |
| permissions         | A list of permissions included in the role.                                                           |
| role\_type          | The type of the role: `BASIC`, `PREDEFINED`, or `CUSTOM`.                                             |
| scope               | The scope of the role: `GLOBAL` (predefined/basic), `ORGANIZATION` (custom org), or `PROJECT` (custom project). |
| lastupdated         | The timestamp of the last update.                                                                     |
| project\_id         | The ID of the GCP project for project-level custom roles only.                                        |
| organization\_id    | The ID of the GCP organization for organization-level roles (predefined and custom org) only.         |

#### Relationships

- Organization-level GCPRoles (predefined/basic and custom org roles) are sub-resources of GCPOrganizations.

    ```
    (GCPOrganization)-[RESOURCE]->(GCPRole)
    ```

- Project-level GCPRoles (custom project roles) are sub-resources of GCPProjects.

    ```
    (GCPProject)-[RESOURCE]->(GCPRole)
    ```

- GCPPolicyBindings grant GCPRoles.

    ```
    (GCPPolicyBinding)-[GRANTS_ROLE]->(GCPRole)
    ```

### GCPKeyRing

Representation of a GCP [Key Ring](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings).

| Field | Description |
|---|---|
| id | The full resource name of the Key Ring. |
| name | The short name of the Key Ring. |
| location | The GCP location of the Key Ring. |
| lastupdated | The timestamp of the last update. |
| project\_id | The full project ID (projects/...) this Key Ring belongs to. |

#### Relationships

  - GCPKeyRings are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPKeyRing)
    ```

### GCPCryptoKey

Representation of a GCP [Crypto Key](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys).

| Field | Description |
|---|---|
| id | The full resource name of the Crypto Key. |
| name | The short name of the Crypto Key. |
| rotation\_period | The rotation period of the key (e.g., `7776000s`). |
| purpose | The key purpose (e.g., `ENCRYPT_DECRYPT`). |
| state | The state of the primary key version (e.g., `ENABLED`). |
| lastupdated | The timestamp of the last update. |
| project\_id | The full project ID (projects/...) this key belongs to. |
| key\_ring\_id | The full ID of the parent Key Ring. |

#### Relationships

  - GCPCryptoKeys are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCryptoKey)
    ```
  - GCPKeyRings contain GCPCryptoKeys.
    ```
    (GCPKeyRing)-[CONTAINS]->(GCPCryptoKey)
    ```

### GCPPolicyBinding

Representation of a GCP [IAM Policy Binding](https://cloud.google.com/iam/docs/reference/rest/v1/Policy#Binding). Policy bindings connect principals (users, service accounts, groups) to roles on specific resources.

| Field                | Description                                                                      |
| -------------------- | -------------------------------------------------------------------------------- |
| id                   | The unique identifier for the policy binding in  the format "{resource}_{role}". |
| role                 | The name of the GCP role being granted.                                          |
| resource             | The full resource name where the policy binding is attached.                     |
| resource_type        | The type of resource.                                                            |
| members              | A list of principal email addresses that are granted the role.                   |
| has_condition        | A boolean indicating if the policy binding has a condition attached.             |
| condition_title      | The title of the condition.                                                      |
| condition_expression | The expression of the condition.                                                 |
| firstseen            | Timestamp of when a sync job first discovered this node.                         |
| lastupdated          | Timestamp of the last time the node was updated.                                 |

#### Relationships

- GCPPolicyBindings are resources of GCPProjects.

    ```
    (GCPProject)-[:RESOURCE]->(GCPPolicyBinding)
    ```

- GCPPrincipals have allow policies that grant them access.

    ```
    (GCPPrincipal)-[:HAS_ALLOW_POLICY]->(GCPPolicyBinding)
    ```

- GCPPolicyBindings grant roles to principals.

    ```
    (GCPPolicyBinding)-[:GRANTS_ROLE]->(GCPRole)
    ```

### GCPBigtableInstance

Representation of a GCP [Bigtable Instance](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances).

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for database instances across different systems (e.g., RDSInstance, DynamoDBTable, AzureSQLDatabase).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The full resource name of the Bigtable Instance. |
| name | The full resource name of the Bigtable Instance. |
| display\_name | The human-readable display name for the instance. |
| state | The current state of the instance (e.g., `READY`). |
| type | The type of instance (e.g., `PRODUCTION`). |

#### Relationships

  - GCPBigtableInstances are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPBigtableInstance)
    ```

### GCPBigtableCluster

Representation of a GCP [Bigtable Cluster](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.clusters).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The full resource name of the Bigtable Cluster. |
| name | The full resource name of the Bigtable Cluster. |
| location | The GCP location where this cluster resides (e.g., `projects/.../locations/us-central1-b`). |
| state | The current state of the cluster (e.g., `READY`). |
| default\_storage\_type | The storage media type for the cluster (e.g., `SSD`). |

#### Relationships

  - GCPBigtableClusters are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPBigtableCluster)
    ```
  - GCPBigtableInstances have one or more Clusters.
    ```
    (GCPBigtableInstance)-[:HAS_CLUSTER]->(GCPBigtableCluster)
    ```

### GCPBigtableTable

Representation of a GCP [Bigtable Table](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.tables).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The full resource name of the Bigtable Table. |
| name | The full resource name of the Bigtable Table. |
| granularity | The granularity at which timestamps are stored (e.g., `MILLIS`). |

#### Relationships

  - GCPBigtableTables are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPBigtableTable)
    ```
  - GCPBigtableInstances have one or more Tables.
    ```
    (GCPBigtableInstance)-[:HAS_TABLE]->(GCPBigtableTable)
    ```

### GCPBigtableAppProfile

Representation of a GCP [Bigtable App Profile](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.appProfiles).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The full resource name of the App Profile. |
| name | The full resource name of the App Profile. |
| description | The user-provided description of the app profile. |
| multi\_cluster\_routing\_use\_any | Whether this profile routes to any available cluster. |
| single\_cluster\_routing\_cluster\_id | The full resource ID of the cluster this profile routes to, if configured. |

#### Relationships

  - GCPBigtableAppProfiles are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPBigtableAppProfile)
    ```
  - GCPBigtableInstances have one or more App Profiles.
    ```
    (GCPBigtableInstance)-[:HAS_APP_PROFILE]->(GCPBigtableAppProfile)
    ```
  - GCPBigtableAppProfiles (with single cluster routing) route to a specific Cluster.
    ```
    (GCPBigtableAppProfile)-[:ROUTES_TO]->(GCPBigtableCluster)
    ```

### GCPBigtableBackup

Representation of a GCP [Bigtable Backup](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.clusters.backups).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The full resource name of the Backup. |
| name | The full resource name of the Backup. |
| source\_table | The full resource name of the table this backup was created from. |
| expire\_time | The timestamp when the backup will expire. |
| start\_time | The timestamp when the backup creation started. |
| end\_time | The timestamp when the backup creation finished. |
| size\_bytes | The size of the backup in bytes. |
| state | The current state of the backup (e.g., `READY`). |

#### Relationships

  - GCPBigtableBackups are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPBigtableBackup)
    ```
  - GCPBigtableClusters store Backups.
    ```
    (GCPBigtableCluster)-[:STORES_BACKUP]->(GCPBigtableBackup)
    ```
  - GCPBigtableTables are backed up as Backups.
    ```
    (GCPBigtableTable)-[:BACKED_UP_AS]->(GCPBigtableBackup)
    ```

### GCPVertexAIModel

Representation of a GCP [Vertex AI Model](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the model (e.g., `projects/{project}/locations/{location}/models/{model_id}`) |
| name | Same as `id` |
| display_name | User-provided display name of the model |
| description | Description of the model |
| version_id | The version ID of the model |
| version_create_time | Timestamp when this model version was created |
| version_update_time | Timestamp when this model version was last updated |
| create_time | Timestamp when the model was originally created |
| update_time | Timestamp when the model was last updated |
| artifact_uri | The path to the directory containing the Model artifact and supporting files (GCS URI) |
| etag | Used to perform consistent read-modify-write updates |
| labels | JSON string of user-defined labels |
| training_pipeline | Resource name of the Training Pipeline that created this model |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIModels are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAIModel)
    ```

- GCPVertexAIModels are stored in GCPBuckets.
    ```
    (GCPVertexAIModel)-[:STORED_IN]->(GCPBucket)
    ```

- GCPVertexAITrainingPipelines produce GCPVertexAIModels.
    ```
    (GCPVertexAITrainingPipeline)-[:PRODUCES]->(GCPVertexAIModel)
    ```

- GCPVertexAIDeployedModels are instances of GCPVertexAIModels.
    ```
    (GCPVertexAIDeployedModel)-[:INSTANCE_OF]->(GCPVertexAIModel)
    ```

### GCPVertexAIEndpoint

Representation of a GCP [Vertex AI Endpoint](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the endpoint (e.g., `projects/{project}/locations/{location}/endpoints/{endpoint_id}`) |
| name | Same as `id` |
| display_name | User-provided display name of the endpoint |
| description | Description of the endpoint |
| create_time | Timestamp when the endpoint was created |
| update_time | Timestamp when the endpoint was last updated |
| etag | Used to perform consistent read-modify-write updates |
| network | The full name of the Google Compute Engine network to which the endpoint should be peered |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIEndpoints are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAIEndpoint)
    ```

- GCPVertexAIEndpoints serve GCPVertexAIDeployedModels.
    ```
    (GCPVertexAIEndpoint)-[:SERVES]->(GCPVertexAIDeployedModel)
    ```

### GCPVertexAIDeployedModel

Representation of a deployed model on a Vertex AI Endpoint. This is derived from the [deployedModels field](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints#DeployedModel) on an Endpoint.

| Field | Description |
|-------|-------------|
| **id** | Synthetic ID combining endpoint and deployed model ID (e.g., `{endpoint_id}/deployedModels/{deployed_model_id}`) |
| deployed_model_id | The ID of the DeployedModel (unique within the endpoint) |
| model | Full resource name of the Model that this DeployedModel is serving |
| display_name | User-provided display name of the deployed model |
| create_time | Timestamp when the deployed model was created |
| dedicated_resources | JSON string of the dedicated resources for this deployed model |
| automatic_resources | JSON string of the automatic resources for this deployed model |
| enable_access_logging | Whether access logging is enabled for this deployed model |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIEndpoints serve GCPVertexAIDeployedModels.
    ```
    (GCPVertexAIEndpoint)-[:SERVES]->(GCPVertexAIDeployedModel)
    ```

- GCPVertexAIDeployedModels are instances of GCPVertexAIModels.
    ```
    (GCPVertexAIDeployedModel)-[:INSTANCE_OF]->(GCPVertexAIModel)
    ```

### GCPVertexAIWorkbenchInstance

Representation of a GCP [Vertex AI Workbench Instance](https://cloud.google.com/vertex-ai/docs/workbench/reference/rest/v2/projects.locations.instances) (v2 API).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the instance (e.g., `projects/{project}/locations/{location}/instances/{instance_id}`) |
| name | Same as `id` |
| creator | Email address of the user who created the instance |
| create_time | Timestamp when the instance was created |
| update_time | Timestamp when the instance was last updated |
| state | The state of the instance (e.g., `ACTIVE`, `STOPPED`) |
| health_state | The health state of the instance (e.g., `HEALTHY`) |
| health_info | JSON string with detailed health information |
| gce_setup | JSON string with GCE setup configuration |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIWorkbenchInstances are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAIWorkbenchInstance)
    ```

- GCPVertexAIWorkbenchInstances use GCPServiceAccounts.
    ```
    (GCPVertexAIWorkbenchInstance)-[:USES_SERVICE_ACCOUNT]->(GCPServiceAccount)
    ```

### GCPVertexAITrainingPipeline

Representation of a GCP [Vertex AI Training Pipeline](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.trainingPipelines).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the training pipeline (e.g., `projects/{project}/locations/{location}/trainingPipelines/{pipeline_id}`) |
| name | Same as `id` |
| display_name | User-provided display name of the training pipeline |
| create_time | Timestamp when the pipeline was created |
| update_time | Timestamp when the pipeline was last updated |
| start_time | Timestamp when the pipeline started running |
| end_time | Timestamp when the pipeline finished |
| state | The state of the pipeline (e.g., `PIPELINE_STATE_SUCCEEDED`) |
| error | JSON string with error information if the pipeline failed |
| model_to_upload | JSON string describing the model that was uploaded |
| training_task_definition | The training task definition schema URI |
| dataset_id | Full resource name of the Dataset used for training (used for relationships) |
| model_id | Full resource name of the Model produced by training (used for relationships) |
| gcs_bucket_id | List of GCS bucket names read during training (used for relationships) |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAITrainingPipelines are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAITrainingPipeline)
    ```

- GCPVertexAITrainingPipelines produce GCPVertexAIModels.
    ```
    (GCPVertexAITrainingPipeline)-[:PRODUCES]->(GCPVertexAIModel)
    ```

- GCPVertexAITrainingPipelines read from GCPVertexAIDatasets.
    ```
    (GCPVertexAITrainingPipeline)-[:READS_FROM]->(GCPVertexAIDataset)
    ```

- GCPVertexAITrainingPipelines read from GCPBuckets.
    ```
    (GCPVertexAITrainingPipeline)-[:READS_FROM]->(GCPBucket)
    ```

### GCPVertexAIFeatureGroup

Representation of a GCP [Vertex AI Feature Group](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.featureGroups). Feature Groups are the new architecture for Vertex AI Feature Store.

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the feature group (e.g., `projects/{project}/locations/{location}/featureGroups/{feature_group_id}`) |
| name | Same as `id` |
| create_time | Timestamp when the feature group was created |
| update_time | Timestamp when the feature group was last updated |
| etag | Used to perform consistent read-modify-write updates |
| bigquery_source_uri | The BigQuery source URI for the feature group |
| entity_id_columns | JSON array of entity ID column names |
| timestamp_column | The timestamp column name (for time series features) |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIFeatureGroups are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAIFeatureGroup)
    ```

### GCPVertexAIDataset

Representation of a GCP [Vertex AI Dataset](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.datasets).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the dataset (e.g., `projects/{project}/locations/{location}/datasets/{dataset_id}`) |
| name | Same as `id` |
| display_name | User-provided display name of the dataset |
| create_time | Timestamp when the dataset was created |
| update_time | Timestamp when the dataset was last updated |
| etag | Used to perform consistent read-modify-write updates |
| data_item_count | The number of data items in the dataset |
| metadata_schema_uri | The metadata schema URI for the dataset |
| metadata | JSON string with dataset metadata |
| encryption_spec | JSON string with encryption configuration |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPVertexAIDatasets are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPVertexAIDataset)
    ```

- GCPVertexAITrainingPipelines read from GCPVertexAIDatasets.
    ```
    (GCPVertexAITrainingPipeline)-[:READS_FROM]->(GCPVertexAIDataset)
    ```

### GCPCloudSQLInstance

Representation of a GCP [Cloud SQL Instance](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances).

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for database instances across different systems (e.g., RDSInstance, AzureSQLDatabase, GCPBigtableInstance).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | The instance's `selfLink`, which is its unique URI. |
| name | The user-assigned name of the instance. |
| database\_version | The database engine type and version (e.g., `POSTGRES_15`). |
| region | The GCP region the instance lives in. |
| gce\_zone | The specific Compute Engine zone the instance is serving from. |
| state | The current state of the instance (e.g., `RUNNABLE`). |
| backend\_type | The type of instance (e.g., `SECOND_GEN`). |
| service\_account\_email | The email of the service account used by this instance. |
| connection\_name | The connection string for accessing the instance (e.g., `project:region:instance`). |
| tier | The machine type tier (e.g., `db-custom-1-3840`). |
| disk\_size\_gb | Storage capacity in gigabytes. |
| disk\_type | Storage disk type (e.g., `PD_SSD`, `PD_HDD`, `HYPERDISK_BALANCED`). |
| availability\_type | Availability configuration (`ZONAL` or `REGIONAL` for high availability). |
| backup\_enabled | Boolean indicating if automated backups are enabled. |
| require\_ssl | Boolean indicating if SSL/TLS encryption is required for connections. |
| ip\_addresses | JSON string containing array of IP addresses with their types (PRIMARY, PRIVATE, OUTGOING). |
| backup\_configuration | JSON string containing full backup configuration including retention and point-in-time recovery settings. |

#### Relationships

  - GCPCloudSQLInstances are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudSQLInstance)
    ```
  - GCPCloudSQLInstances are associated with GCPVpcs.
    ```
    (GCPCloudSQLInstance)-[:ASSOCIATED_WITH]->(GCPVpc)
    ```
  - GCPCloudSQLInstances use GCPServiceAccounts.
    ```
    (GCPCloudSQLInstance)-[:USES_SERVICE_ACCOUNT]->(GCPServiceAccount)
    ```

### GCPCloudSQLDatabase

Representation of a GCP [Cloud SQL Database](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/databases).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | A unique ID constructed from the parent instance ID and database name. |
| name | The name of the database. |
| charset | The character set for the database. |
| collation | The collation for the database. |

#### Relationships

  - GCPCloudSQLDatabases are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudSQLDatabase)
    ```
  - GCPCloudSQLInstances contain GCPCloudSQLDatabases.
    ```
    (GCPCloudSQLInstance)-[:CONTAINS]->(GCPCloudSQLDatabase)
    ```

### GCPCloudSQLUser

Representation of a GCP [Cloud SQL User](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/users).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | A unique ID constructed from the parent instance ID and the user's name and host. |
| name | The name of the user. |
| host | The host from which the user is allowed to connect. |

#### Relationships

  - GCPCloudSQLUsers are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudSQLUser)
    ```
  - GCPCloudSQLInstances have GCPCloudSQLUsers.
    ```
    (GCPCloudSQLInstance)-[:HAS_USER]->(GCPCloudSQLUser)
    ```

### GCPCloudSQLBackupConfiguration

Representation of a GCP [Cloud SQL Backup Configuration](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances#backupconfiguration). This node captures the backup settings for a Cloud SQL instance.

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | A unique ID constructed from the parent instance ID with `/backupConfig` suffix. |
| enabled | Boolean indicating whether automated backups are enabled. |
| start\_time | The start time for the daily backup window in UTC (HH:MM format). |
| location | The location where backups are stored. |
| point\_in\_time\_recovery\_enabled | Boolean indicating whether point-in-time recovery is enabled. |
| transaction\_log\_retention\_days | Number of days of transaction logs retained for point-in-time recovery. |
| backup\_retention\_settings | String representation of backup retention configuration (e.g., retained backup count). |
| binary\_log\_enabled | Boolean indicating whether binary logging is enabled. |
| instance\_id | The ID of the parent Cloud SQL instance. |

#### Relationships

  - GCPCloudSQLBackupConfigurations are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudSQLBackupConfiguration)
    ```
  - GCPCloudSQLInstances have GCPCloudSQLBackupConfigurations.
    ```
    (GCPCloudSQLInstance)-[:HAS_BACKUP_CONFIG]->(GCPCloudSQLBackupConfiguration)
    ```

### GCPCloudFunction

Representation of a Google [Cloud Function](https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions) (v1 API).

> **Ontology Mapping**: This node has the extra label `Function` and normalized `_ont_*` properties for cross-platform serverless function queries. See [Function](../../ontology/schema.md#function).

| Field                 | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| id                    | The full, unique resource name of the function.                             |
| name                  | The full, unique resource name of the function (same as id).                |
| description           | User-provided description of the function.                                  |
| runtime               | The language runtime environment for the function (e.g., python310).        |
| entry_point           | The name of the function within the source code to be executed.             |
| status                | The current state of the function (e.g., ACTIVE, OFFLINE, DEPLOY_IN_PROGRESS). |
| update_time           | The timestamp when the function was last modified.                          |
| service_account_email | The email of the service account the function runs as.                      |
| https_trigger_url     | The public URL if the function is triggered by an HTTP request.             |
| event_trigger_type    | The type of event that triggers the function (e.g., a Pub/Sub message).     |
| event_trigger_resource| The specific resource the event trigger monitors.                           |
| project_id            | The ID of the GCP project to which the function belongs.                    |
| region                | The GCP region where the function is deployed.                              |
| lastupdated           | Timestamp of when the data was last updated in the graph.                   |

#### Relationships

- GCPCloudFunctions are resources of GCPProjects.

    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudFunction)
    ```

- GCPCloudFunctions run as GCPServiceAccounts.

    ```
    (GCPCloudFunction)-[:RUNS_AS]->(GCPServiceAccount)
    ```

### GCPSecretManagerSecret

Representation of a GCP [Secret Manager Secret](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets). A Secret is a logical container for secret data that can have multiple versions.

> **Ontology Mapping**: This node has the extra label `Secret` and normalized `_ont_*` properties for cross-platform secret queries. See [Secret](../../ontology/schema.md#secret).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the secret (e.g., `projects/{project}/secrets/{secret_id}`) |
| name | The short name of the secret |
| project_id | The GCP project ID that owns this secret |
| rotation_enabled | Boolean indicating if automatic rotation is configured |
| rotation_period | The rotation period in seconds (if rotation is enabled) |
| rotation_next_time | Epoch timestamp of the next scheduled rotation |
| created_date | Epoch timestamp when the secret was created |
| expire_time | Epoch timestamp when the secret will automatically expire and be deleted |
| replication_type | The replication policy type: `automatic` or `user_managed` |
| etag | Used to perform consistent read-modify-write updates |
| labels | JSON string of user-defined labels |
| topics | JSON string of Pub/Sub topics for rotation notifications |
| version_aliases | JSON string mapping alias names to version numbers |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPSecretManagerSecrets are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPSecretManagerSecret)
    ```

### GCPSecretManagerSecretVersion

Representation of a GCP [Secret Manager Secret Version](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets.versions). A SecretVersion stores a specific version of secret data within a Secret.

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the version (e.g., `projects/{project}/secrets/{secret_id}/versions/{version}`) |
| secret_id | Full resource name of the parent secret |
| version | The version number (e.g., "1", "2") |
| state | The current state of the version: `ENABLED`, `DISABLED`, or `DESTROYED` |
| created_date | Epoch timestamp when the version was created |
| destroy_time | Epoch timestamp when the version was destroyed (only present if state is `DESTROYED`) |
| etag | Used to perform consistent read-modify-write updates |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPSecretManagerSecretVersions are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPSecretManagerSecretVersion)
    ```

- GCPSecretManagerSecretVersions are versions of GCPSecretManagerSecrets.
    ```
    (GCPSecretManagerSecretVersion)-[:VERSION_OF]->(GCPSecretManagerSecret)
    ```

### Artifact Registry Resources

#### Overview

Google Cloud Artifact Registry is a universal package manager for managing container images and language packages. Cartography ingests the following Artifact Registry resources with dedicated node types for each artifact category:

```mermaid
graph LR
    Project[GCPProject]
    Repository[GCPArtifactRegistryRepository]
    ContainerImage[GCPArtifactRegistryContainerImage]
    HelmChart[GCPArtifactRegistryHelmChart]
    LanguagePackage[GCPArtifactRegistryLanguagePackage]
    GenericArtifact[GCPArtifactRegistryGenericArtifact]
    PlatformImage[GCPArtifactRegistryPlatformImage]
    TrivyFinding[TrivyImageFinding]
    Package[Package]

    Project -->|RESOURCE| Repository
    Project -->|RESOURCE| ContainerImage
    Project -->|RESOURCE| HelmChart
    Project -->|RESOURCE| LanguagePackage
    Project -->|RESOURCE| GenericArtifact
    Project -->|RESOURCE| PlatformImage
    Repository -->|CONTAINS| ContainerImage
    Repository -->|CONTAINS| HelmChart
    Repository -->|CONTAINS| LanguagePackage
    Repository -->|CONTAINS| GenericArtifact
    ContainerImage -->|HAS_MANIFEST| PlatformImage
    TrivyFinding -->|AFFECTS| ContainerImage
    Package -->|DEPLOYED| ContainerImage
```

#### GCPArtifactRegistryRepository

Representation of a GCP [Artifact Registry Repository](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories).

> **Ontology Mapping**: This node has the extra label `ContainerRegistry` to enable cross-platform queries for container registries across different systems (e.g., ECRRepository, GCPArtifactRegistryRepository, GitLabContainerRepository).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the repository (e.g., `projects/{project}/locations/{location}/repositories/{repo}`) |
| name | The short name of the repository |
| format | The format of packages stored in the repository (e.g., `DOCKER`, `MAVEN`, `NPM`, `PYTHON`, `GO`, `APT`, `YUM`) |
| mode | The mode of the repository (e.g., `STANDARD_REPOSITORY`, `VIRTUAL_REPOSITORY`, `REMOTE_REPOSITORY`) |
| description | User-provided description of the repository |
| location | The GCP region where the repository is located |
| registry_uri | The Docker registry URI for Docker format repositories (e.g., `us-east1-docker.pkg.dev/{project}/{repo}`) |
| size_bytes | The size of the repository in bytes |
| kms_key_name | The Cloud KMS key name used to encrypt the repository |
| create_time | Timestamp when the repository was created |
| update_time | Timestamp when the repository was last updated |
| cleanup_policy_dry_run | Whether cleanup policies are in dry run mode |
| vulnerability_scanning_enabled | Whether vulnerability scanning is enabled |
| project_id | The GCP project ID |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryRepositories are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryRepository)
    ```

- GCPArtifactRegistryRepositories contain artifacts (ContainerImage, HelmChart, LanguagePackage, GenericArtifact).
    ```
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryContainerImage)
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryHelmChart)
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryLanguagePackage)
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryGenericArtifact)
    ```

#### GCPArtifactRegistryContainerImage

Representation of a [Docker Image](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.dockerImages) in a GCP Artifact Registry repository.

> **Ontology Mapping**: This node has conditional extra labels based on the image media type: `Image` for single-image manifests (Docker V2 manifest or OCI image manifest), or `ImageManifestList` for multi-architecture manifest lists (Docker V2 manifest list or OCI image index). These labels enable cross-platform queries for container images across different systems (e.g., ECRImage, GitLabContainerImage).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the Docker image |
| name | The short name of the image |
| uri | The URI of the image |
| digest | The image digest (e.g., `sha256:...`) |
| tags | Tags associated with the image |
| image_size_bytes | Size of the image in bytes |
| media_type | The media type of the image manifest |
| upload_time | Timestamp when the image was uploaded |
| build_time | Timestamp when the image was built |
| update_time | Timestamp when the image was last updated |
| repository_id | Full resource name of the parent repository |
| project_id | The GCP project ID |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryContainerImages are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryContainerImage)
    ```

- GCPArtifactRegistryRepositories contain GCPArtifactRegistryContainerImages.
    ```
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryContainerImage)
    ```

- GCPArtifactRegistryContainerImages have GCPArtifactRegistryPlatformImages (for multi-architecture images).
    ```
    (GCPArtifactRegistryContainerImage)-[:HAS_MANIFEST]->(GCPArtifactRegistryPlatformImage)
    ```

- TrivyImageFindings affect GCPArtifactRegistryContainerImages.
    ```
    (TrivyImageFinding)-[:AFFECTS]->(GCPArtifactRegistryContainerImage)
    ```

- Packages are deployed in GCPArtifactRegistryContainerImages.
    ```
    (Package)-[:DEPLOYED]->(GCPArtifactRegistryContainerImage)
    ```

#### GCPArtifactRegistryHelmChart

Representation of a Helm chart stored as an OCI artifact in a GCP Artifact Registry repository. Helm charts are stored in Docker-format repositories and identified by their media type.

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the Helm chart |
| name | The short name of the chart |
| uri | The URI of the chart |
| version | The version of the chart (extracted from tags) |
| create_time | Timestamp when the chart was created |
| update_time | Timestamp when the chart was last updated |
| repository_id | Full resource name of the parent repository |
| project_id | The GCP project ID |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryHelmCharts are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryHelmChart)
    ```

- GCPArtifactRegistryRepositories contain GCPArtifactRegistryHelmCharts.
    ```
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryHelmChart)
    ```

#### GCPArtifactRegistryLanguagePackage

Representation of a language package in a GCP Artifact Registry repository. This node type covers [Maven Artifacts](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.mavenArtifacts), [npm Packages](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.npmPackages), [Python Packages](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.pythonPackages), and [Go Modules](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.goModules).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the package |
| name | The short name of the package |
| format | The format of the package (`MAVEN`, `NPM`, `PYTHON`, `GO`) |
| uri | The URI of the package |
| version | The version of the package |
| package_name | Human-readable package name |
| create_time | Timestamp when the package was created |
| update_time | Timestamp when the package was last updated |
| repository_id | Full resource name of the parent repository |
| project_id | The GCP project ID |
| group_id | (Maven only) The Maven group ID |
| artifact_id | (Maven only) The Maven artifact ID |
| tags | (npm only) Tags associated with the package |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryLanguagePackages are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryLanguagePackage)
    ```

- GCPArtifactRegistryRepositories contain GCPArtifactRegistryLanguagePackages.
    ```
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryLanguagePackage)
    ```

#### GCPArtifactRegistryGenericArtifact

Representation of a generic artifact in a GCP Artifact Registry repository. This node type covers [APT Artifacts](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.aptArtifacts) and [YUM Artifacts](https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.yumArtifacts).

| Field | Description |
|-------|-------------|
| **id** | Full resource name of the artifact |
| name | The short name of the artifact |
| format | The format of the artifact (`APT`, `YUM`) |
| package_name | The package name |
| repository_id | Full resource name of the parent repository |
| project_id | The GCP project ID |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryGenericArtifacts are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryGenericArtifact)
    ```

- GCPArtifactRegistryRepositories contain GCPArtifactRegistryGenericArtifacts.
    ```
    (GCPArtifactRegistryRepository)-[:CONTAINS]->(GCPArtifactRegistryGenericArtifact)
    ```

#### GCPArtifactRegistryPlatformImage

Representation of a platform-specific manifest within a multi-architecture Docker image. This node captures the individual platform configurations (architecture, OS) for images that support multiple platforms.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier combining parent artifact and manifest digest |
| digest | The digest of this specific platform manifest |
| architecture | CPU architecture (e.g., `amd64`, `arm64`) |
| os | Operating system (e.g., `linux`, `windows`) |
| os_version | OS version if specified |
| os_features | OS features if specified |
| variant | Platform variant (e.g., `v8` for arm64) |
| media_type | The media type of the manifest |
| parent_artifact_id | Full resource name of the parent Docker image |
| project_id | The GCP project ID |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- GCPArtifactRegistryPlatformImages are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPArtifactRegistryPlatformImage)
    ```

- GCPArtifactRegistryContainerImages have GCPArtifactRegistryPlatformImages.
    ```
    (GCPArtifactRegistryContainerImage)-[:HAS_MANIFEST]->(GCPArtifactRegistryPlatformImage)
    ```

#### Trivy Integration Queries

Find all vulnerabilities affecting GCP Artifact Registry container images:

```cypher
MATCH (vuln:TrivyImageFinding)-[:AFFECTS]->(img:GCPArtifactRegistryContainerImage)
RETURN vuln.name, vuln.severity, img.uri, img.digest
ORDER BY vuln.severity DESC
```

Find packages deployed in GCP container images with their vulnerabilities:

```cypher
MATCH (pkg:Package)-[:DEPLOYED]->(img:GCPArtifactRegistryContainerImage)
OPTIONAL MATCH (vuln:TrivyImageFinding)-[:AFFECTS]->(pkg)
RETURN img.uri, pkg.name, pkg.installed_version, collect(vuln.name) AS vulnerabilities
```

Find critical vulnerabilities in GCP images with available fixes:

```cypher
MATCH (vuln:TrivyImageFinding {severity: 'CRITICAL'})-[:AFFECTS]->(img:GCPArtifactRegistryContainerImage)
MATCH (vuln)-[:AFFECTS]->(pkg:Package)
OPTIONAL MATCH (pkg)-[:SHOULD_UPDATE_TO]->(fix:TrivyFix)
RETURN vuln.name, img.uri, pkg.name, pkg.installed_version, fix.version AS fixed_version
```

### Cloud Run Resources

#### Overview

Google Cloud Run is a serverless compute platform for running containers. Cartography ingests the following Cloud Run resources:

```mermaid
graph LR
    Project[GCPProject]
    Service[GCPCloudRunService]
    Revision[GCPCloudRunRevision]
    Job[GCPCloudRunJob]
    Execution[GCPCloudRunExecution]
    ServiceAccount[GCPServiceAccount]

    Project -->|RESOURCE| Service
    Project -->|RESOURCE| Revision
    Project -->|RESOURCE| Job
    Project -->|RESOURCE| Execution

    Service -->|HAS_REVISION| Revision
    Job -->|HAS_EXECUTION| Execution

    Revision -->|USES_SERVICE_ACCOUNT| ServiceAccount
    Job -->|USES_SERVICE_ACCOUNT| ServiceAccount
```

### GCPCloudRunService

Representation of a GCP [Cloud Run Service](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.services).

> **Ontology Mapping**: This node has the extra label `Function` to enable cross-platform queries for serverless functions across different systems (e.g., AWSLambda, AzureFunctionApp, GCPCloudFunction).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | Full resource name of the service (e.g., `projects/{project}/locations/{location}/services/{service}`) |
| name | Short name of the service |
| location | The GCP location where the service is deployed |
| container_image | The container image for the service |
| service_account_email | The email of the service account used by this service |

#### Relationships

  - GCPCloudRunServices are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudRunService)
    ```
  - GCPCloudRunServices have GCPCloudRunRevisions.
    ```
    (GCPCloudRunService)-[:HAS_REVISION]->(GCPCloudRunRevision)
    ```

### GCPCloudRunRevision

Representation of a GCP [Cloud Run Revision](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.services.revisions).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | Full resource name of the revision (e.g., `projects/{project}/locations/{location}/services/{service}/revisions/{revision}`) |
| name | Short name of the revision |
| service | Full resource name of the parent service |
| container_image | The container image for this revision |
| service_account_email | The email of the service account used by this revision |
| log_uri | URI to Cloud Logging for this revision |

#### Relationships

  - GCPCloudRunRevisions are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudRunRevision)
    ```
  - GCPCloudRunServices have GCPCloudRunRevisions.
    ```
    (GCPCloudRunService)-[:HAS_REVISION]->(GCPCloudRunRevision)
    ```
  - GCPCloudRunRevisions use GCPServiceAccounts.
    ```
    (GCPCloudRunRevision)-[:USES_SERVICE_ACCOUNT]->(GCPServiceAccount)
    ```

### GCPCloudRunJob

Representation of a GCP [Cloud Run Job](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.jobs).

> **Ontology Mapping**: This node has the extra label `Function` to enable cross-platform queries for serverless functions across different systems (e.g., AWSLambda, AzureFunctionApp, GCPCloudFunction).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | Full resource name of the job (e.g., `projects/{project}/locations/{location}/jobs/{job}`) |
| name | Short name of the job |
| location | The GCP location where the job is deployed |
| container_image | The container image for the job |
| service_account_email | The email of the service account used by this job |

#### Relationships

  - GCPCloudRunJobs are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudRunJob)
    ```
  - GCPCloudRunJobs have GCPCloudRunExecutions.
    ```
    (GCPCloudRunJob)-[:HAS_EXECUTION]->(GCPCloudRunExecution)
    ```
  - GCPCloudRunJobs use GCPServiceAccounts.
    ```
    (GCPCloudRunJob)-[:USES_SERVICE_ACCOUNT]->(GCPServiceAccount)
    ```

### GCPCloudRunExecution

Representation of a GCP [Cloud Run Execution](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.jobs.executions).

| Field | Description |
|---|---|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated| Timestamp of the last time the node was updated |
| **id** | Full resource name of the execution (e.g., `projects/{project}/locations/{location}/jobs/{job}/executions/{execution}`) |
| name | Short name of the execution |
| job | Full resource name of the parent job |
| status | Completion status of the execution (e.g., `SUCCEEDED`, `FAILED`) |
| cancelled_count | Number of tasks that were cancelled |
| failed_count | Number of tasks that failed |
| succeeded_count | Number of tasks that succeeded |

#### Relationships

  - GCPCloudRunExecutions are resources of GCPProjects.
    ```
    (GCPProject)-[:RESOURCE]->(GCPCloudRunExecution)
    ```
  - GCPCloudRunJobs have GCPCloudRunExecutions.
    ```
    (GCPCloudRunJob)-[:HAS_EXECUTION]->(GCPCloudRunExecution)
    ```
