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
| subnet_domain_name | The subnet's domain name |
| prohibit_public_ip_on_vnic | Whether VNICs in this subnet can have public IPs |
| region | The region the subnet resides in |
| createdate | ISO 8601 date-time when the subnet was created |

### Relationships

- VCNs contain Subnets.

	```
	(OCIVcn)-[OCI_SUBNET]->(OCISubnet)
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
