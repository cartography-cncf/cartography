<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [OCITenancy](#ocitenancy)
  - [Relationships](#relationships)
- [OCIUser](#ociuser)
  - [Relationships\](#relationships%5C)
- [OCIGroup](#ocigroup)
  - [Relationships](#relationships-1)
- [OCIPolicy](#ocipolicy)
  - [Relationships](#relationships-2)
- [OCIRegion](#ociregion)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

#Copyright (c) 2020, Oracle and/or its affiliates.

## OCITenancy

Representation of an OCI Tenancy.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|name| The name of the account|
|lastupdated| Timestamp of the last time the node was updated|
|**ocid**| The OCI Tenancy ID number|

### Relationships
- Many node types belong to an `OCI Tenancy`.

	```
	(OCITenancy)-[RESOURCE]->(OCIUser,
                              OCIGroup,
                              OCICompartment)
	```
- An `OCIPolicy` node is defined for an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

 ## OCICompartment
Representation of an [OCICompartment](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Compartment)
/ Field / Description /
/-------/-------------/
/ firstseen / Timestamp of when a sync job first discovered this node  /
/ lastupdated /  Timestamp of the last time the node was updated /
/ compartmentid / The compartment id of the compartment /
/ name / The friendly name of the compartment  /
/ description / The description the compartment /
/ createdate / ISO 8601 date-time when the compartment was created /
/ **ocid** / OCI-unique identifier for this object /

- OCI Compartments can be members of OCI Compartments (up to 6 levels deep).

	```
	(OCICompartment)-[OCI_SUB_COMPARTMENT]->(OCICompartment)
	```

- OCI Tenancy's contain OCI Compartments.

	```
	(OCITenancy)-[RESOURCE]->(OCICompartment)
	```
- OCI Compartments can contain OCI Policies.

	```
	(OCICompartment)-[OCI_POLICY]->(OCIPolicy)
	```


## OCIUser
Representation of an [OCIUser](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/User).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| compartmentid | The compartment id of the user |
| name | The friendly name of the user |
| description | The description of the user |
| email | The description of the user |
| lifecycle_state | The user's current state. After creating a user, make sure its lifecycleState changes from CREATING to ACTIVE before using it. |
| is_mfa_activated | Flag indicates if MFA has been activated for the user. |
| can_use_api_keys | Indicates if the user can use API keys. |
| can_use_auth_tokens | Indicates if the user can use SWIFT passwords / auth tokens. |
| can_use_console_password | Indicates if the user can log in to the console. |
| can_use_customer_secret_keys | Indicates if the user can use SigV4 symmetric keys.Indicates if the user can use SigV4 symmetric keys.Indicates if the user can use SigV4 symmetric keys. |
| can_use_smtp_credentials | Indicates if the user can use SMTP passwords. |
| createdate | ISO 8601 date-time when the user was created |
| **ocid** | OCI-unique identifier for this object

### Relationships\
- OCI Users can be members of OCI Groups.

	```
	(OCIUser)-[MEMBER_OCI_GROUP]->(OCIGroup)
	```

- OCI Tenancy's contain OCI Users.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIUser)
	```

## OCIGroup

Representation of OCI [IAM Groups](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Group).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
| compartmentid | The OCID of the tenancy containing the group |
| name | The friendly name that identifies the group|
| description | The description the group |
| createdate| ISO 8601 date-time string when the group was created |
|**ocid** | The OCI-global identifier for this group |

### Relationships
- OCIUsers can be members of OCIGroups.

	```
	(OCIUser)-[MEMBER_OCI_GROUP]->(OCIGroup)
	```

- OCIGroups belong to OCITenancy's.

	```
	(OCITenancy)-[RESOURCE]->(OCIGroup)
	```

## OCIPolicy

Representation of an [OCI Policy](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Policy).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| compartmentid | The OCID of the compartment containing the policy |
| statements | An array of one or more policy statements written in the policy language.  |
| description | The description the policy |
| updatedate | ISO 8601 date-time when the policy was last updated |
| name | The friendly name (not ocid) identifying the policy |
| createdate | ISO 8601 date-time when the policy was created|
| **ocid** | The OCI-unique identifier for this object |

### Relationships

- An `OCIPolicy` node is defined in an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

- An `OCIPolicy` node is defined in an `OCICompartment`.

	```
	(OCICompartment)-[OCI_POLICY]->(OCIPolicy)
	```


- An `OCIPolicy` node is defined in an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

- An `OCIPolicy` node can reference an `OCICompartment`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCICompartment)
	```

- An `OCIPolicy` node can reference an `OCIGroup`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
	```

## OCIRegion
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The key (not ocid) identifying the region |
| name | The friendly name (not ocid) identifying the region |

- An `OCITenancy` node can reference an `OCIRegion`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
	```
 - Many node types belong to an `OCIRegion`.

	```
	(OCITenancy)<-[OCI_REGION]-(OCIUser,
                              OCIGroup,
                              OCICompartment)
	```

## OCIVcn

Representation of an [OCI Virtual Cloud Network (VCN)](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Vcn/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this VCN |
| display_name | The user-friendly name of the VCN |
| compartment_id | The OCID of the compartment containing the VCN |
| cidr_block | The first CIDR block associated with the VCN |
| dns_label | The DNS label for the VCN |
| lifecycle_state | The VCN's current state |
| region | The region the VCN resides in |
| createdate | ISO 8601 date-time when the VCN was created |

### Relationships

- OCI Compartments contain VCNs.

	```
	(OCICompartment)-[RESOURCE]->(OCIVcn)
	```

- VCNs contain Subnets.

	```
	(OCIVcn)-[OCI_SUBNET]->(OCISubnet)
	```

- VCNs contain Security Lists.

	```
	(OCIVcn)-[OCI_SECURITY_LIST]->(OCISecurityList)
	```

- VCNs contain Network Security Groups.

	```
	(OCIVcn)-[OCI_NETWORK_SECURITY_GROUP]->(OCINetworkSecurityGroup)
	```

- VCNs contain Internet Gateways.

	```
	(OCIVcn)-[OCI_INTERNET_GATEWAY]->(OCIInternetGateway)
	```

- VCNs contain NAT Gateways.

	```
	(OCIVcn)-[OCI_NAT_GATEWAY]->(OCINatGateway)
	```

- VCNs contain Route Tables.

	```
	(OCIVcn)-[OCI_ROUTE_TABLE]->(OCIRouteTable)
	```

## OCISubnet

Representation of an [OCI Subnet](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Subnet/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this subnet |
| display_name | The user-friendly name of the subnet |
| compartment_id | The OCID of the compartment containing the subnet |
| cidr_block | The CIDR block of the subnet |
| availability_domain | The availability domain of the subnet |
| dns_label | The DNS label for the subnet |
| lifecycle_state | The subnet's current state |
| vcn_id | The OCID of the VCN the subnet belongs to |
| route_table_id | The OCID of the route table associated with the subnet |
| security_list_ids | List of OCIDs of the security lists associated with the subnet |
| subnet_domain_name | The subnet's domain name |
| prohibit_public_ip_on_vnic | Whether VNICs in this subnet can have public IPs |
| region | The region the subnet resides in |
| createdate | ISO 8601 date-time when the subnet was created |

### Relationships

- VCNs contain Subnets.

	```
	(OCIVcn)-[OCI_SUBNET]->(OCISubnet)
	```

- Subnets are associated with a Route Table.

	```
	(OCISubnet)-[OCI_ROUTE_TABLE]->(OCIRouteTable)
	```

- Subnets are associated with one or more Security Lists.

	```
	(OCISubnet)-[OCI_SECURITY_LIST]->(OCISecurityList)
	```

- Subnets contain VNICs.

	```
	(OCISubnet)-[OCI_VNIC]->(OCIVnic)
	```

- Subnets can have a Flow Log.

	```
	(OCISubnet)-[OCI_FLOW_LOG]->(OCIFlowLog)
	```

## OCISecurityList

Representation of an [OCI Security List](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/SecurityList/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this security list |
| display_name | The user-friendly name of the security list |
| compartment_id | The OCID of the compartment containing the security list |
| vcn_id | The OCID of the VCN the security list belongs to |
| lifecycle_state | The security list's current state |
| ingress_security_rules | JSON string of ingress rules |
| egress_security_rules | JSON string of egress rules |
| region | The region the security list resides in |
| createdate | ISO 8601 date-time when the security list was created |

### Relationships

- VCNs contain Security Lists.

	```
	(OCIVcn)-[OCI_SECURITY_LIST]->(OCISecurityList)
	```

## OCINetworkSecurityGroup

Representation of an [OCI Network Security Group](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/NetworkSecurityGroup/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this NSG |
| display_name | The user-friendly name of the NSG |
| compartment_id | The OCID of the compartment containing the NSG |
| vcn_id | The OCID of the VCN the NSG belongs to |
| lifecycle_state | The NSG's current state |
| region | The region the NSG resides in |
| createdate | ISO 8601 date-time when the NSG was created |

### Relationships

- VCNs contain Network Security Groups.

	```
	(OCIVcn)-[OCI_NETWORK_SECURITY_GROUP]->(OCINetworkSecurityGroup)
	```

- NSGs contain Security Rules.

	```
	(OCINetworkSecurityGroup)-[OCI_NSG_RULE]->(OCINsgSecurityRule)
	```

## OCINsgSecurityRule

Representation of an OCI NSG Security Rule.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this rule |
| direction | INGRESS or EGRESS |
| protocol | The transport protocol (e.g., 6 for TCP, 17 for UDP) |
| description | Description of the rule |
| source | Source CIDR or NSG OCID for ingress rules |
| source_type | Type of source (CIDR_BLOCK, NSG, etc.) |
| destination | Destination CIDR or NSG OCID for egress rules |
| destination_type | Type of destination |
| is_stateless | Whether the rule is stateless |
| is_valid | Whether the rule is valid |
| tcp_dest_port_min | Minimum TCP destination port |
| tcp_dest_port_max | Maximum TCP destination port |
| tcp_src_port_min | Minimum TCP source port |
| tcp_src_port_max | Maximum TCP source port |
| udp_dest_port_min | Minimum UDP destination port |
| udp_dest_port_max | Maximum UDP destination port |
| icmp_type | ICMP type |
| icmp_code | ICMP code |

### Relationships

- NSGs contain Security Rules.

	```
	(OCINetworkSecurityGroup)-[OCI_NSG_RULE]->(OCINsgSecurityRule)
	```

## OCIInternetGateway

Representation of an [OCI Internet Gateway](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/InternetGateway/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this internet gateway |
| display_name | The user-friendly name of the internet gateway |
| compartment_id | The OCID of the compartment containing the gateway |
| vcn_id | The OCID of the VCN the gateway belongs to |
| is_enabled | Whether the gateway is enabled |
| lifecycle_state | The gateway's current state |
| region | The region the gateway resides in |
| createdate | ISO 8601 date-time when the gateway was created |

### Relationships

- VCNs contain Internet Gateways.

	```
	(OCIVcn)-[OCI_INTERNET_GATEWAY]->(OCIInternetGateway)
	```

## OCINatGateway

Representation of an [OCI NAT Gateway](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/NatGateway/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this NAT gateway |
| display_name | The user-friendly name of the NAT gateway |
| compartment_id | The OCID of the compartment containing the gateway |
| vcn_id | The OCID of the VCN the gateway belongs to |
| nat_ip | The IP address associated with the NAT gateway |
| block_traffic | Whether traffic is blocked through the gateway |
| lifecycle_state | The gateway's current state |
| region | The region the gateway resides in |
| createdate | ISO 8601 date-time when the gateway was created |

### Relationships

- VCNs contain NAT Gateways.

	```
	(OCIVcn)-[OCI_NAT_GATEWAY]->(OCINatGateway)
	```

## OCIRouteTable

Representation of an [OCI Route Table](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/RouteTable/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this route table |
| display_name | The user-friendly name of the route table |
| compartment_id | The OCID of the compartment containing the route table |
| vcn_id | The OCID of the VCN the route table belongs to |
| lifecycle_state | The route table's current state |
| route_rules | JSON string of route rules |
| region | The region the route table resides in |
| createdate | ISO 8601 date-time when the route table was created |

### Relationships

- VCNs contain Route Tables.

	```
	(OCIVcn)-[OCI_ROUTE_TABLE]->(OCIRouteTable)
	```

- Subnets are associated with a Route Table.

	```
	(OCISubnet)-[OCI_ROUTE_TABLE]->(OCIRouteTable)
	```

## OCIVnic

Representation of an [OCI VNIC](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Vnic/). A VNIC connects a compute instance to a subnet and can carry a public IP.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this VNIC |
| display_name | The user-friendly name of the VNIC |
| compartment_id | The OCID of the compartment containing the VNIC |
| availability_domain | The availability domain the VNIC resides in |
| lifecycle_state | The VNIC's current state |
| private_ip | The private IP address of the VNIC |
| public_ip | The public IP address of the VNIC (if any) |
| is_primary | Whether the VNIC is the primary VNIC of the instance |
| hostname_label | The hostname for the VNIC's primary private IP |
| mac_address | The MAC address of the VNIC |
| skip_source_dest_check | Whether source/destination check is skipped |
| subnet_id | The OCID of the subnet the VNIC is in |
| region | The region the VNIC resides in |
| createdate | ISO 8601 date-time when the VNIC was created |

### Relationships

- Subnets contain VNICs.

	```
	(OCISubnet)-[OCI_VNIC]->(OCIVnic)
	```

- VNIC Attachments reference VNICs (linking an instance to its VNIC).

	```
	(OCIVnicAttachment)-[OCI_VNIC]->(OCIVnic)
	```

## OCIFlowLog

Representation of an [OCI VCN Flow Log](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/flowlogoverview.htm). Flow logs are OCI service logs (`OCILog`) whose source service is `flowlogs`. The node carries both the `OCIFlowLog` and `OCILog` labels.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this log |
| display_name | The user-friendly name of the log |
| compartment_id | The OCID of the compartment containing the log |
| log_group_id | The OCID of the log group the log belongs to |
| log_type | The type of log (CUSTOM or SERVICE) |
| is_enabled | Whether the log is enabled |
| lifecycle_state | The log's current state |
| source_service | The service that created the log (e.g., flowlogs) |
| source_category | The log category (e.g., all) |
| source_resource | The OCID of the resource the log is configured for (subnet or VCN) |
| region | The region the log resides in |
| createdate | ISO 8601 date-time when the log was created |

### Relationships

- Subnets can have a Flow Log.

	```
	(OCISubnet)-[OCI_FLOW_LOG]->(OCIFlowLog)
	```

- VCNs can have a Flow Log.

	```
	(OCIVcn)-[OCI_FLOW_LOG]->(OCIFlowLog)
	```

## OCIInstance

Representation of an [OCI Compute Instance](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Instance/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this instance |
| display_name | The user-friendly name of the instance |
| compartment_id | The OCID of the compartment containing the instance |
| availability_domain | The availability domain the instance is in |
| fault_domain | The fault domain the instance is in |
| shape | The shape of the instance |
| lifecycle_state | The instance's current state |
| region | The region the instance resides in |
| image_id | The OCID of the image used to boot the instance |
| are_legacy_imds_endpoints_disabled | Whether legacy (v1) instance metadata service endpoints are disabled |
| is_secure_boot_enabled | Whether Secure Boot is enabled (shielded instance) |
| is_pv_encryption_in_transit_enabled | Whether paravirtualized in-transit encryption is enabled |
| is_monitoring_disabled | Whether the monitoring plugin (agent) is disabled |
| createdate | ISO 8601 date-time when the instance was created |

### Relationships

- OCI Compartments contain Instances.

	```
	(OCICompartment)-[RESOURCE]->(OCIInstance)
	```

- Instances have VNIC Attachments.

	```
	(OCIInstance)-[OCI_VNIC_ATTACHMENT]->(OCIVnicAttachment)
	```

- Instances have Boot Volume Attachments.

	```
	(OCIInstance)-[OCI_BOOT_VOLUME_ATTACHMENT]->(OCIBootVolumeAttachment)
	```

- Instances have Volume Attachments.

	```
	(OCIInstance)-[OCI_VOLUME_ATTACHMENT]->(OCIVolumeAttachment)
	```

- Instances are attached to Boot Volumes.

	```
	(OCIInstance)-[OCI_BOOT_VOLUME]->(OCIBootVolume)
	```

- Block Volumes are attached to Instances.

	```
	(OCIBlockVolume)-[ATTACHED_TO]->(OCIInstance)
	```

## OCIBootVolume

Representation of an [OCI Boot Volume](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/BootVolume/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this boot volume |
| display_name | The user-friendly name of the boot volume |
| compartment_id | The OCID of the compartment containing the boot volume |
| availability_domain | The availability domain the boot volume is in |
| lifecycle_state | The boot volume's current state |
| size_in_gbs | The size of the boot volume in GBs |
| kms_key_id | The OCID of the KMS key used to encrypt the boot volume (if any) |
| is_hydrated | Whether the boot volume's data has finished copying from the source |
| vpus_per_gb | The number of volume performance units per GB |
| image_id | The OCID of the image the boot volume was created from |
| has_backup_policy | Whether a volume backup policy is assigned to the boot volume |
| region | The region the boot volume resides in |
| createdate | ISO 8601 date-time when the boot volume was created |

### Relationships

- OCI Compartments contain Boot Volumes.

	```
	(OCICompartment)-[RESOURCE]->(OCIBootVolume)
	```

- Instances are attached to Boot Volumes.

	```
	(OCIInstance)-[OCI_BOOT_VOLUME]->(OCIBootVolume)
	```

## OCIBlockVolume

Representation of an [OCI Block Volume](https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Volume/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this block volume |
| display_name | The user-friendly name of the block volume |
| compartment_id | The OCID of the compartment containing the block volume |
| availability_domain | The availability domain the block volume is in |
| lifecycle_state | The block volume's current state |
| size_in_gbs | The size of the block volume in GBs |
| kms_key_id | The OCID of the KMS key used to encrypt the block volume (if any) |
| is_hydrated | Whether the block volume's data has finished copying from the source |
| vpus_per_gb | The number of volume performance units per GB |
| has_backup_policy | Whether a volume backup policy is assigned to the block volume |
| region | The region the block volume resides in |
| createdate | ISO 8601 date-time when the block volume was created |

### Relationships

- OCI Compartments contain Block Volumes.

	```
	(OCICompartment)-[RESOURCE]->(OCIBlockVolume)
	```

- Block Volumes are attached to Instances.

	```
	(OCIBlockVolume)-[ATTACHED_TO]->(OCIInstance)
	```

## OCIObjectStorageBucket

Representation of an [OCI Object Storage Bucket](https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/latest/Bucket/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| name | The name of the bucket (unique within namespace) |
| namespace | The Object Storage namespace the bucket belongs to |
| compartment_id | The OCID of the compartment containing the bucket |
| public_access_type | The type of public access (NoPublicAccess, ObjectRead, ObjectReadWithoutList) |
| storage_tier | The default storage tier (Standard, Archive, InfrequentAccess) |
| versioning | The versioning status (Enabled, Suspended, Disabled) |
| kms_key_id | The OCID of the KMS key used to encrypt the bucket (empty if Oracle-managed) |
| is_read_only | Whether the bucket is read-only |
| object_events_enabled | Whether object events are enabled |
| has_retention_rules | Whether the bucket has retention rules configured |
| approximate_count | The approximate number of objects in the bucket |
| approximate_size | The approximate total size of all objects in the bucket |
| region | The region the bucket resides in |
| createdate | ISO 8601 date-time when the bucket was created |

### Relationships

- OCI Compartments contain Object Storage Buckets.

	```
	(OCICompartment)-[RESOURCE]->(OCIObjectStorageBucket)
	```

## OCIFileSystem

Representation of an [OCI File Storage File System](https://docs.oracle.com/en-us/iaas/api/#/en/filestorage/latest/FileSystem/).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **ocid** | OCI-unique identifier for this file system |
| display_name | The user-friendly name of the file system |
| compartment_id | The OCID of the compartment containing the file system |
| availability_domain | The availability domain the file system is in |
| lifecycle_state | The file system's current state |
| kms_key_id | The OCID of the KMS key used to encrypt the file system (empty if Oracle-managed) |
| metered_bytes | The number of bytes consumed by the file system |
| region | The region the file system resides in |
| createdate | ISO 8601 date-time when the file system was created |

### Relationships

- OCI Compartments contain File Systems.

	```
	(OCICompartment)-[RESOURCE]->(OCIFileSystem)
	```
