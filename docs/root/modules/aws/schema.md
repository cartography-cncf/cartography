## AWS Schema


### AWSAccount

Representation of an AWS Account.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|name| The name of the account|
|inscope| Indicates that the account is part of the sync scope (true or false).
|foreign| Indicates if the account is not part of the sync scope (true or false). One such example is an account that is trusted as part of cross-account AWSRole trust not in scope for sync.
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The AWS Account ID number|

#### Relationships
- Many node types belong to an `AWSAccount`.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSDNSZone,
                                :AWSGroup,
                                :AWSInspectorFinding,
                                :AWSInspectorPackage,
                                :AWSLambda,
                                :AWSPrincipal,
                                :AWSUser,
                                :AWSVpc,
                                :AutoScalingGroup,
                                :DNSZone,
                                :DynamoDBTable,
                                :EBSSnapshot,
                                :EBSVolume,
                                :EC2Image,
                                :EC2Instance,
                                :EC2Reservation,
                                :EC2ReservedInstance,
                                :EC2SecurityGroup,
                                :ElasticIPAddress,
                                :ESDomain,
                                :LaunchConfiguration,
                                :LaunchTemplate,
                                :LaunchTemplateVersion,
                                :LoadBalancer,
                                :RDSCluster,
                                :RDSInstance,
                                :RDSSnapshot,
                                :SecretsManagerSecret,
                                :SecurityHub,
                                :SQSQueue,
                                :SSMInstanceInformation,
                                :SSMInstancePatch,
                                ...)
    ```

- An `AWSPolicy` node is defined for an `AWSAccount`.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSPolicy)
    ```

- `AWSRole` nodes are defined in `AWSAccount` nodes.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSRole)
    ```

### AWSCidrBlock
#### AWSIpv4CidrBlock
#### AWSIpv6CidrBlock
Representation of an [AWS CidrBlock used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html).
The `AWSCidrBlock` defines the base label
type for `AWSIpv4CidrBlock` and `AWSIpv6CidrBlock`

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|cidr\_block| The CIDR block|
|block\_state| The state of the block|
|association\_id| the association id if the block is associated to a VPC
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Unique identifier defined with the VPC association and the cidr\_block

#### Relationships
- `AWSVpc` association
  ```
  (AWSVpc)-[BLOCK_ASSOCIATION]->(AWSCidrBlock)
  ```
- Peering connection where `AWSCidrBlock` is an accepter or requester cidr.
  ```
  (AWSCidrBlock)<-[REQUESTER_CIDR]-(AWSPeeringConnection)
  (AWSCidrBlock)<-[ACCEPTER_CIDR]-(AWSPeeringConnection)
  ```

  Example of high level view of peering (without security group permissions)
  ```
  MATCH p=(:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(:AWSCidrBlock)<-[:RESOURCE|BLOCK_ASSOCIATION*..]-(:AWSAccount)
  RETURN p
  ```

  Exploring detailed inbound peering rules
  ```
  MATCH (outbound_account:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)<-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(inbound_block:AWSCidrBlock)<-[:BLOCK_ASSOCIATION]-(inbound_vpc:AWSVpc)<-[:RESOURCE]-(inbound_account:AWSAccount)
  WITH inbound_vpc, inbound_block, outbound_account, inbound_account
  MATCH (inbound_range:IpRange{id: inbound_block.cidr_block})-[:MEMBER_OF_IP_RULE]->(inbound_rule:IpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(inbound_group:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(inbound_vpc)
  RETURN outbound_account.name, inbound_account.name, inbound_range.range, inbound_rule.fromport, inbound_rule.toport, inbound_rule.protocol, inbound_group.name, inbound_vpc.id
  ```

### AWSGroup

Representation of AWS [IAM Groups](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Group.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
|path | The path to the group (IAM identifier, see linked docs above for details)|
| groupid| Unique string identifying the group |
|name | The friendly name that identifies the group|
| createdate| ISO 8601 date-time string when the group was created|
|**arn** | The AWS-global identifier for this group|

#### Relationships
- Objects part of an AWSGroup may assume AWSRoles.

    ```cypher
    (:AWSGroup)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)
    ```

- AWSUsers and AWSPrincipals can be members of AWSGroups.

    ```cypher
    (:AWSUser, :AWSPrincipal)-[:MEMBER_AWS_GROUP]->(:AWSGroup)
    ```

- AWSGroups belong to AWSAccounts.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSGroup)
    ```

### AWSInspectorFinding

Representation of an AWS [Inspector Finding](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)

| Field | Description | Required|
|-------|-------------|------|
|arn|The AWS ARN|yes|
|id|Reuses the AWS ARN since it's unique|yes|
|region|AWS region the finding is from|yes|
|awsaccount|AWS account the finding is from|yes|
|name|The finding name|
|instanceid|The instance ID of the EC2 instance with the issue|
|ecrimageid|The image ID of the ECR image with the issue|
|ecrrepositoryid|The repository ID of the ECR repository with the issue|
|severity|The finding severity|
|firstobservedat|Date the finding was first identified|
|updatedat|Date the finding was last updated|
|description|The finding description|
|type|The finding type|
|cvssscore|CVSS score of the finding|
|protocol|Network protocol for network findings|
|portrange|Port range affected for network findings|
|portrangebegin|Beginning of the port range affected for network findings|
|portrangeend|End of the port range affected for network findings|
|vulnerabilityid|Vulnerability ID associdated with the finding for package findings|
|referenceurls|Reference URLs for the found vulnerabilities|
|relatedvulnerabilities|A list of any related vulnerabilities|
|source|Source for the vulnerability|
|sourceurl|URL for the vulnerability source|
|vendorcreatedat|Date the vulnerability notice was created by the vendor|
|vendorseverity|Vendor chosen issue severity|
|vendorupdatedat|Date the vendor information was last updated|
|vulnerablepackageids|IDs for any related packages|

#### Relationships

- AWSInspectorFinding may affect EC2 Instances

    ```cypher
    (:AWSInspectorFinding)-[:AFFECTS]->(:EC2Instance)
    ```

- AWSInspectorFinding may affect ECR Repositories

    ```cypher
    (:AWSInspectorFinding)-[:AFFECTS]->(:ECRRepository)
    ```

- AWSInspectorFinding may affect ECR Images

    ```cypher
    (:AWSInspectorFinding)-[:AFFECTS]->(:ECRImage)
    ```

- AWSInspectorFindings managed by AWSAccount.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSInspectorFinding)
    ```

- AWSInspectorFinding was found at an AWSAccounts. `MEMBER` accounts are where the finding is attached to, while `RESOURCE` accounts can be a delegated administrator. [Understanding the delegated administrator account and member account in Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/user/admin-member-relationship.html) .

    ```cypher
    (:AWSAccount)-[:MEMBER]->(:AWSInspectorFinding)
    ```


### AWSInspectorPackage

Representation of an AWS [Inspector Finding Package](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)

| Field | Description | Required|
|-------|-------------|------|
|**arn**|The AWS ARN|yes|
|id|Uses the format of `name|arch|version|release|epoch` to uniqulely identify packages|yes|
|region|AWS region the finding is from|yes|
|awsaccount|AWS account the finding is from|yes|
|findingarn|The AWS ARN for a related finding|yes|
|name|The finding name|
|arch|Architecture for the package|
|version|Version of the package|
|release|Release of the package
|epoch|Package epoch|
|manager|Related package manager|
|filepath|Path to the file or package|
|fixedinversion|Version the related finding was fixed in|
|sourcelayerhash|Source layer hash for container images|


#### Relationships

- AWSInspectorFindings have AWSInspectorPackages.

    ```cypher
    (:AWSInspectorFindings)-[:HAS]->(:AWSInspectorPackages)
    ```

- AWSInspectorPackages belong to AWSAccounts.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSInspectorPackages)
    ```


### AWSInstanceProfile

Representation of an AWS [IAM Instance Profile](https://docs.aws.amazon.com/IAM/latest/APIReference/API_InstanceProfile.html)


| Field                 | Description                                        |
|-----------------------|----------------------------------------------------|
| firstseen             | Timestamp of when a sync job first discovered this node |
| lastupdated           | Timestamp of the last time the node was updated    |
| **arn**               | The arn                                            |
| **id**                | The arn                                            |
| instance_profile_id   | The instance profile id                            |
| instance_profile_name | The instance profile name                          |
| path                  | e.g. '/'                                           |


#### Relationships

- AWSInstanceProfiles belong to accounts
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSInstanceProfile)
    ```

- Instance profiles can be associated with one or more IAM roles.
    ```cypher
    (:AWSRole)<-[:ASSOCIATED_WITH]-(:AWSInstanceProfile)
    ```

- Instance profiles can be associated with one or more EC2 instances.
    ```cypher
    (:EC2Instance)-[:INSTANCE_PROFILE]->(:AWSInstanceProfile)
    ```


### AWSLambda

Representation of an AWS [Lambda Function](https://docs.aws.amazon.com/lambda/latest/dg/API_FunctionConfiguration.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function|
| name |  The name of the lambda function |
| modifieddate |  Timestamp of the last time the function was last updated |
| runtime |  The runtime environment for the Lambda function |
| description |  The description of the Lambda function |
| timeout |  The amount of time in seconds that Lambda allows a function to run before stopping it |
| memory |  The memory that's allocated to the function |
| codesize |  The size of the function's deployment package, in bytes. |
| handler |  The function that Lambda calls to begin executing your function. |
| version |  The version of the Lambda function. |
| tracingconfigmode | The function's AWS X-Ray tracing configuration mode. |
| revisionid | The latest updated revision of the function or alias. |
| state | The current state of the function. |
| statereason | The reason for the function's current state. |
| statereasoncode | The reason code for the function's current state. |
| lastupdatestatus | The status of the last update that was performed on the function. |
| lastupdatestatusreason |  The reason for the last update that was performed on the function.|
| lastupdatestatusreasoncode | The reason code for the last update that was performed on the function. |
| packagetype |  The type of deployment package. |
| signingprofileversionarn | The ARN of the signing profile version. |
| signingjobarn | The ARN of the signing job. |
| codesha256 | The SHA256 hash of the function's deployment package. |
| architectures | The instruction set architecture that the function supports. Architecture is a string array with one of the valid values. |
| masterarn | For Lambda@Edge functions, the ARN of the main function. |
| kmskeyarn | The KMS key that's used to encrypt the function's environment variables. This key is only returned if you've configured a customer managed key. |

#### Relationships

- AWSLambda function are resources in an AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AWSLambda)
    ```

- AWSLambda functions may act as AWSPrincipals via role assumption.
    ```
    (:AWSLambda)-[:STS_ASSUME_ROLE_ALLOW]->(:AWSPrincipal)
    ```

- AWSLambda functions may also have aliases.
    ```
    (:AWSLambda)-[:KNOWN_AS]->(:AWSLambdaFunctionAlias)
    ```

- AWSLambda functions may have the resource AWSLambdaEventSourceMapping.
    ```
    (:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
    ```

- AWSLambda functions has AWS Lambda Layers.
    ```
    (:AWSLambda)-[:HAS]->(:AWSLambdaLayer)
    ```

- AWSLambda functions has AWS ECR Images.
    ```
    (:AWSLambda)-[:HAS]->(:ECRImage)
    ```

### AWSLambdaFunctionAlias
Representation of an [AWSLambdaFunctionAlias](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function alias|
| name |  The name of the lambda function alias |
| functionversion | The function version that the alias invokes.|
| revisionid |  A unique identifier that changes when you update the alias. |
| description |  The description of the alias. |

#### Relationships

- AWSLambda functions may also have aliases.

        ```
        (AWSLambda)-[KNOWN_AS]->(AWSLambdaFunctionAlias)
        ```

### AWSLambdaEventSourceMapping

Representation of an [AWSLambdaEventSourceMapping](https://docs.aws.amazon.com/lambda/latest/dg/API_ListEventSourceMappings.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the event source mapping|
| batchsize | The maximum number of items to retrieve in a single batch. |
| startingposition | The position in a stream from which to start reading. |
| startingpositiontimestamp |  The time from which to start reading. |
| parallelizationfactor |  The number of batches to process from each shard concurrently. |
| maximumbatchingwindowinseconds | The maximum amount of time to gather records before invoking the function, in seconds.|
| eventsourcearn |The Amazon Resource Name (ARN) of the event source.|
| lastmodified |The date that the event source mapping was last updated, or its state changed.|
| state | The state of the event source mapping. |
| maximumrecordage | Discard records older than the specified age. |
| bisectbatchonfunctionerror | If the function returns an error, split the batch in two and retry. |
| maximumretryattempts | Discard records after the specified number of retries. |
| tumblingwindowinseconds | The duration in seconds of a processing window. |
| lastprocessingresult |The result of the last AWS Lambda invocation of your Lambda function. |

#### Relationships

- AWSLambda functions may have the resource AWSLambdaEventSourceMapping.

    ```cypher
    (AWSLambda)-[RESOURCE]->(AWSLambdaEventSourceMapping)
    ```

### AWSLambdaLayer

Representation of an [AWSLambdaLayer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function layer|
| codesize | The size of the layer archive in bytes.|
| signingprofileversionarn | The Amazon Resource Name (ARN) for a signing profile version.|
| signingjobarn | The Amazon Resource Name (ARN) of a signing job. |

#### Relationships

- AWSLambda functions has AWS Lambda Layers.

    ```cypher
    (AWSLambda)-[HAS]->(AWSLambdaLayer)
    ```

### AWSPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The friendly name (not ARN) identifying the policy |
| createdate | ISO 8601 date-time when the policy was created|
| type | "inline" or "managed" - the type of policy it is|
| arn | The arn for this object |
| **id** | The unique identifer for a policy. If the policy is managed this will be the Arn. If the policy is inline this will calculated as _AWSPrincipal_/inline_policy/_PolicyName_|


#### Relationships

- `AWSPrincipal` contains `AWSPolicy`

    ```cypher
    (AWSPrincipal)-[POLICY]->(AWSPolicy)
    ```

- `AWSPolicy` contains `AWSPolicyStatement`

    ```cypher
    (AWSPolicy)-[STATEMENTS]->(AWSPolicyStatement)
    ```

### AWSPolicyStatement

Representation of an [AWS Policy Statement](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Statement.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated|
| resources | (array) The resources the statement is applied to. Can contain wildcards |
| actions | (array) The permissions allowed or denied by the statement. Can contain wildcards |
| notactions | (array) The permission explicitly not matched by the statement |
| effect | "Allow" or "Deny" - the effect of this statement |
| **id** | The unique identifier for a statement. <br>If the statement has an Sid the id will be calculated as _AWSPolicy.id_/statements/_Sid_. <br>If the statement has no Sid the id will be calculated as  _AWSPolicy.id_/statements/_index of statement in statement list_ |


#### Relationships

- `AWSPolicy` contains `AWSPolicyStatement`

    ```cypher
    (AWSPolicy)-[STATEMENTS]->(AWSPolicyStatement)
    ```


### AWSPrincipal
Representation of an [AWSPrincipal](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| path | The path to the principal |
| name | The friendly name of the principal |
| createdate | ISO 8601 date-time when the principal was created |
| **arn** | AWS-unique identifier for this object |
| userid | The stable and unique string identifying the principal.  |
| passwordlastused | Datetime when this principal's password was last used


#### Relationships

- AWS Principals can be members of AWS Groups.

    ```cypher
    (AWSPrincipal)-[MEMBER_AWS_GROUP]->(AWSGroup)
    ```

- This AccountAccessKey is used to authenticate to this AWSPrincipal.

    ```cypher
    (AWSPrincipal)-[AWS_ACCESS_KEY]->(AccountAccessKey)
    ```

- AWS Roles can trust AWS Principals.

    ```cypher
    (AWSRole)-[TRUSTS_AWS_PRINCIPAL]->(AWSPrincipal)
    ```

- AWS Accounts contain AWS Principals.

    ```cypher
    (AWSAccount)-[RESOURCE]->(AWSPrincipal)
    ```

- Redshift clusters may assume IAM roles. See [this article](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html).

    ```
    (RedshiftCluster)-[STS_ASSUMEROLE_ALLOW]->(AWSPrincipal)
    ```

### AWSPrincipal::AWSUser
Representation of an [AWSUser](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).  An AWS User is a type of AWS Principal.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| path | The path to the user |
| name | The friendly name of the user |
| createdate | ISO 8601 date-time when the user was created |
| **arn** | AWS-unique identifier for this object |
| userid | The stable and unique string identifying the user.  |
| passwordlastused | Datetime when this user's password was last used

#### Relationships
- AWS Users can be members of AWS Groups.

    ```cypher
    (AWSUser)-[MEMBER_AWS_GROUP]->(AWSGroup)
    ```

- AWS Users can assume AWS Roles.

    ```cypher
    (AWSUser)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- This AccountAccessKey is used to authenticate to this AWSUser

    ```cypher
    (AWSUser)-[AWS_ACCESS_KEY]->(AccountAccessKey)
    ```

- AWS Accounts contain AWS Users.

    ```cypher
    (AWSAccount)-[RESOURCE]->(AWSUser)
    ```


### AWSPrincipal::AWSRole

Representation of an AWS [IAM Role](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Role.html). An AWS Role is a type of AWS Principal.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| roleid | The stable and unique string identifying the role.  |
| name | The friendly name that identifies the role.|
| createdate| The date and time, in ISO 8601 date-time format, when the role was created. |
| **arn** | AWS-unique identifier for this object |


#### Relationships

- Some AWS Groups, Users, Principals, and EC2 Instances can assume AWS Roles.

    ```cypher
    (AWSGroup, AWSUser, EC2Instance)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- Some AWS Roles can assume other AWS Roles.

    ```cypher
    (AWSRole)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- Some AWS Roles trust AWS Principals.

    ```cypher
    (AWSRole)-[TRUSTS_AWS_PRINCIPAL]->(AWSPrincipal)
    ```

- Members of an Okta group can assume associated AWS roles if Okta SAML is configured with AWS.

    ```cypher
    (AWSRole)-[ALLOWED_BY]->(OktaGroup)
    ```

- An IamInstanceProfile can be associated with a role.

    ```cypher
    (AWSRole)<-[ASSOCIATED_WITH]-(AWSInstanceProfile)
    ```

- AWS Roles are defined in AWS Accounts.

    ```cypher
    (AWSAccount)-[RESOURCE]->(AWSRole)
    ```

### AWSTransitGateway
Representation of an [AWS Transit Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGateway.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|owner\_id| The ID of the AWS account that owns the transit gateway|
|description| Transit Gateway description|
|state| Can be one of ``pending \| available \| modifying \| deleting \| deleted``|
|tgw_id| Unique identifier of the Transit Gateway|
|**id**| Unique identifier of the Transit Gateway|
| **arn** | AWS-unique identifier for this object (same as `id`) |

#### Relationships
- Transit Gateways belong to one `AWSAccount`...
    ```cypher
    (AWSAccount)-[RESOURCE]->(AWSTransitGateway)
    ```

- ... and can be shared with other accounts
    ```cypher
    (AWSAccount)<-[SHARED_WITH]-(AWSTransitGateway)
    ```

- `AWSTag`
    ```cypher
    (AWSTransitGateway)-[TAGGED]->(AWSTag)
    ```

### AWSTransitGatewayAttachment
Representation of an [AWS Transit Gateway Attachment](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayAttachment.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|resource\_type| Can be one of ``vpc \| vpn \| direct-connect-gateway \| tgw-peering`` |
|state| Can be one of ``initiating \| pendingAcceptance \| rollingBack \| pending \| available \| modifying \| deleting \| deleted \| failed \| rejected \| rejecting \| failing``
|**id**| Unique identifier of the Transit Gateway Attachment |

#### Relationships
- `AWSAccount`
    ```cypher
    (AWSAccount)-[RESOURCE]->(AWSTransitGatewayAttachment)
    ```
- `AWSVpc` (for VPC attachments)
    ```cypher
    (AWSVpc)-[RESOURCE]->(AWSTransitGatewayAttachment {resource_type: 'vpc'})
    ```
- `AWSTransitGateway` attachment
    ```cypher
    (AWSTransitGateway)<-[ATTACHED_TO]-(AWSTransitGatewayAttachment)
    ```
- `AWSTag`
    ```cypher
    (AWSTransitGatewayAttachment)-[TAGGED]->(AWSTag)
    ```

### AWSVpc
Representation of an [AWS CidrBlock used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html).
More information on https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|vpcid| The VPC unique identifier|
|primary\_cidr\_block|The primary IPv4 CIDR block for the VPC.|
|instance\_tenancy| The allowed tenancy of instances launched into the VPC.|
|state| The current state of the VPC.|
|region| (optional) the region of this VPC.  This field is only available on VPCs in your account.  It is not available on VPCs that are external to your account and linked via a VPC peering relationship.
|**id**| Unique identifier defined VPC node (vpcid)

#### Relationships
- `AWSAccount` resource
  ```
  (AWSAccount)-[RESOURCE]->(AWSVpc)
  ```
- `AWSVpc` and `AWSCidrBlock` association
  ```
  (AWSVpc)-[BLOCK_ASSOCIATION]->(AWSCidrBlock)
  ```
- `AWSVpc` and `EC2SecurityGroup` membership association
  ```
  (AWSVpc)<-[MEMBER_OF_EC2_SECURITY_GROUP]-(EC2SecurityGroup)
  ```
-  AWS VPCs can be tagged with AWSTags.
    ```
        (AWSVpc)-[TAGGED]->(AWSTag)
        ```
- Redshift clusters can be members of AWSVpcs.
    ```
    (RedshiftCluster)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```
- Peering connection where `AWSVpc` is an accepter or requester vpc.
  ```
  (AWSVpc)<-[REQUESTER_VPC]-(AWSPeeringConnection)
  (AWSVpc)<-[ACCEPTER_VPC]-(AWSPeeringConnection)
  ```


### Tag::AWSTag

Representation of an AWS [Tag](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_Tag.html). AWS Tags can be applied to many objects.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | This tag's unique identifier of the format `{TagKey}:{TagValue}`. We fabricated this ID. |
| key | One part of a key-value pair that makes up a tag.|
| value | One part of a key-value pair that makes up a tag. |
| region | The region where this tag was discovered.|

#### Relationships
-  AWS VPCs, DB Subnet Groups, EC2 Instances, EC2 SecurityGroups, EC2 Subnets, EC2 Network Interfaces, RDS Instances, and S3 Buckets can be tagged with AWSTags.
    ```
    (AWSVpc, DBSubnetGroup, EC2Instance, EC2SecurityGroup, EC2Subnet, NetworkInterface, RDSInstance, S3Bucket)-[TAGGED]->(AWSTag)
    ```

### AccountAccessKey

Representation of an AWS [Access Key](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AccessKey.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated
| createdate | Date when access key was created |
| status | Active: valid for API calls.  Inactive: not valid for API calls|
| lastuseddate | Date when the key was last used |
| lastusedservice | The service that was last used with the access key |
| lastusedregion | The region where the access key was last used |
| **accesskeyid** | The ID for this access key|

#### Relationships
- Account Access Keys may authenticate AWS Users and AWS Principal objects.
    ```
    (AWSUser, AWSPrincipal)-[AWS_ACCESS_KEY]->(AccountAccessKey)
    ```

### CloudTrailTrail

Representation of an AWS [CloudTrail Trail](https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_Trail.html).

| Field | Description |
|-------|-------------|
| cloudwatch_logs_log_group_arn | The ARN identifier representing the log group where the CloudTrailTrail delivers logs. |
| cloudwatch_logs_role_arn | The role ARN that the CloudTrailTrail's CloudWatch Logs endpoint assumes. |
| has_custom_event_selectors | Indicates if the CloudTrailTrail has custom event selectors. |
| has_insight_selectors | Indicates if the CloudTrailTrail has insight types specified. |
| home_region | The Region where the CloudTrailTrail was created. |
| include_global_service_events | Indicates if the CloudTrailTrail includes AWS API calls from global services. |
| is_multi_region_trail | Indicates if the CloudTrailTrail exists in one or all Regions. |
| is_organization_trail | Indicates if the CloudTrailTrail is an organization trail. |
| kms_key_id | The AWS KMS key ID that encrypts the CloudTrailTrail's delivered logs. |
| log_file_validation_enabled | Indicates if log file validation is enabled for the CloudTrailTrail. |
| name | The name of the CloudTrailTrail. |
| s3_bucket_name | The Amazon S3 bucket name where the CloudTrailTrail delivers files. |
| s3_key_prefix | The S3 key prefix used after the bucket name for the CloudTrailTrail's log files. |
| sns_topic_arn | The ARN of the SNS topic used by the CloudTrailTrail for delivery notifications. |

#### Relationships
- CloudTrail Trails can be configured to log to S3 Buckets
    ```
    (:CloudTrailTrail)-[:LOGS_TO]->(:S3Bucket)
    ```

### CloudWatchLogGroup
Representation of an AWS [CloudWatch Log Group](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_LogGroup.html)

| Field | Description |
|-------|-------------|
| id | The ARN of the SNS log group |
| arn | The Amazon Resource Name (ARN) of the log group |
| creationTime | The creation time of the log group, expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC. |
| dataProtectionStatus | Displays whether this log group has a protection policy, or whether it had one in the past. |
| inheritedProperties | Displays all the properties that this log group has inherited from account-level settings. |
| kmsKeyId | The Amazon Resource Name (ARN) of the AWS KMS key to use when encrypting log data. |
| logGroupArn | The Amazon Resource Name (ARN) of the log group. |
| logGroupClass | This specifies the log group class for this log group. |
| logGroupName | The name of the log group. |
| metricFilterCount | The number of metric filters. |
| retentionInDays | The number of days to retain the log events in the specified log group. |
| storedBytes | The number of bytes stored. |
#### Relationships
- CLoudWatch LogGroups are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CloudWatchLogGroup)
    ```

### DBSubnetGroup

Representation of an RDS [DB Subnet Group](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSubnetGroup.html).  For more information on how RDS instances interact with these, please see [this article](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|id| The ARN of the DBSubnetGroup|
|name | The name of DBSubnetGroup |
|lastupdated| Timestamp of the last time the node was updated|
|description| Description of the DB Subnet Group|
|status| The status of the group |
|vpc\_id| The ID of the VPC (Virtual Private Cloud) that this DB Subnet Group is associated with.|
|value| The IP address that the DNSRecord points to|

#### Relationships

- RDS Instances are part of DB Subnet Groups
    ```
    (RDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(DBSubnetGroup)
    ```

- DB Subnet Groups consist of EC2 Subnets
    ```
    (DBSubnetGroup)-[:RESOURCE]->(EC2Subnet)
    ```

-  DB Subnet Groups can be tagged with AWSTags.
    ```
    (DBSubnetGroup)-[TAGGED]->(AWSTag)
    ```


### DNSRecord

Representation of a generic DNSRecord.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|name| The name of the DNSRecord|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The name of the DNSRecord concatenated with the record type|
|type| The record type of the DNS record|
|value| The IP address that the DNSRecord points to|

#### Relationships

- DNSRecords can point to IP addresses.
    ```
    (DNSRecord)-[DNS_POINTS_TO]->(Ip)
    ```


- DNSRecords/AWSDNSRecords can point to each other.
    ```
    (AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(AWSDNSRecord, DNSRecord)
    ```


- DNSRecords can point to LoadBalancers.
    ```
    (DNSRecord)-[DNS_POINTS_TO]->(LoadBalancer)
    ```


- DNSRecords can be members of DNSZones.
    ```
    (DNSRecord)-[MEMBER_OF_DNS_ZONE]->(DNSZone)
    ```


### DNSRecord::AWSDNSRecord
Representation of an AWS DNS [ResourceRecordSet](https://docs.aws.amazon.com/Route53/latest/APIReference/API_ResourceRecordSet.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node |
|name| The name of the DNSRecord|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The zoneid for the record, the value of the record, and the type concatenated together|
|type| The record type of the DNS record|
|value| If it is an A, ALIAS, or CNAME record, this is the IP address that the DNSRecord points to. If it is an NS record, the `name` is used here.|

#### Relationships
- DNSRecords/AWSDNSRecords can point to each other.
    ```
    (AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(AWSDNSRecord, DNSRecord)
    ```


- AWSDNSRecords can point to LoadBalancers.
    ```
    (AWSDNSRecord)-[DNS_POINTS_TO]->(LoadBalancer, ESDomain)
    ```


- AWSDNSRecords can be members of AWSDNSZones.
    ```
    (AWSDNSRecord)-[MEMBER_OF_DNS_ZONE]->(AWSDNSZone)
    ```


### DNSZone
Representation of a generic DNS Zone.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
|**name**| the name of the DNS zone|
| comment | Comments about the zone |


#### Relationships

- DNSRecords can be members of DNSZones.
    ```
    (DNSRecord)-[MEMBER_OF_DNS_ZONE]->(DNSZone)
    ```


### DNSZone::AWSDNSZone

Representation of an AWS DNS [HostedZone](https://docs.aws.amazon.com/Route53/latest/APIReference/API_HostedZone.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
|**name**| the name of the DNS zone|
| zoneid| The zoneid defined by Amazon Route53|
| lastupdated|  Timestamp of the last time the node was updated |
| comment| Comments about the zone |
| privatezone | Whether or not this is a private DNS zone |

#### Relationships

- AWSDNSZones and DNSZones can be part of AWSAccounts.
    ```
    (AWSAccount)-[RESOURCE]->(AWSDNSZone)
    ```

- AWSDNSRecords can be members of AWSDNSZones.
    ```
    (AWSDNSRecord)-[MEMBER_OF_DNS_ZONE]->(AWSDNSZone)
    ```

- AWSDNSZone can have subzones hosted by another AWSDNSZone
    ```
    (AWSDNSZone)<-[SUBZONE]-(AWSDNSZone)
    ```


### DynamoDBTable

Representation of an AWS [DynamoDBTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_ListTables.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the table |
| **id** | The ARN of the table |
| region | The AWS region of the table |
| **arn** | The AWS-unique identifier

#### Relationships
- DynamoDBTables belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(DynamoDBTable)
    ```


### EC2Instance

Our representation of an AWS [EC2 Instance](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as `instanceid` below. |
| instanceid | The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203) |
| publicdnsname | The public DNS name assigned to the instance |
| publicipaddress | The public IPv4 address assigned to the instance if applicable |
| privateipaddress | The private IPv4 address assigned to the instance |
| imageid | The ID of the [Amazon Machine Image](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) used to launch the instance |
| subnetid | The ID of the EC2Subnet associated with this instance |
| instancetype | The instance type.  See API docs linked above for specifics. |
| iaminstanceprofile | The IAM instance profile associated with the instance, if applicable. |
| launchtime | The time the instance was launched |
| monitoringstate | Whether monitoring is enabled.  Valid Values: disabled, disabling, enabled,  pending. |
| state | The [current state](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html) of the instance.
| launchtimeunix | The time the instance was launched in unix time |
| region | The AWS region this Instance is running in|
| exposed\_internet |  The `exposed_internet` flag on an EC2 instance is set to `True` when (1) the instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet or (2) the instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`. |
| availabilityzone | The Availability Zone of the instance.|
| tenancy | The tenancy of the instance.|
| hostresourcegrouparn | The ARN of the host resource group in which to launch the instances.|
| platform | The value is `Windows` for Windows instances; otherwise blank.|
| architecture | The architecture of the image.|
| ebsoptimized | Indicates whether the instance is optimized for Amazon EBS I/O. |
| bootmode | The boot mode of the instance.|
| instancelifecycle | Indicates whether this is a Spot Instance or a Scheduled Instance.|
| hibernationoptions | Indicates whether the instance is enabled for hibernation.|


#### Relationships

- EC2 Instances can be part of subnets
    ```
    (EC2Instance)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- EC2 Instances can have NetworkInterfaces connected to them
    ```
    (EC2Instance)-[NETWORK_INTERFACE]->(NetworkInterface)
    ```

- EC2 Instances may be members of EC2 Reservations
    ```
    (EC2Instance)-[MEMBER_OF_EC2_RESERVATION]->(EC2Reservation)
    ```

- EC2 Instances can be part of EC2 Security Groups
    ```
    (EC2Instance)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- Load Balancers can expose (be connected to) EC2 Instances
    ```
    (LoadBalancer)-[EXPOSE]->(EC2Instance)
    ```

- Package and Dependency nodes can be deployed in EC2 Instances.
    ```
    (Package, Dependency)-[DEPLOYED]->(EC2Instance)
    ```

- AWS Accounts contain EC2 Instances.
    ```
    (AWSAccount)-[RESOURCE]->(EC2Instance)
    ```

-  EC2 Instances can be tagged with AWSTags.
    ```
    (EC2Instance)-[TAGGED]->(AWSTag)
    ```

- AWS EBS Volumes are attached to an EC2 Instance
    ```
    (EBSVolume)-[ATTACHED_TO]->(EC2Instance)
    ```

- Instance profiles can be associated with one or more EC2 instances.
    ```
    (EC2Instance)-[INSTANCE_PROFILE]->(AWSInstanceProfile)
    ```

-  EC2 Instances can assume IAM Roles (due to their IAM instance profiles).
    ```
    (EC2Instance)-[STS_ASSUMEROLE_ALLOW]->(AWSRole)
    ```

- EC2Instances can have SSMInstanceInformation
    ```
    (EC2Instance)-[HAS_INFORMATION]->(SSMInstanceInformation)
    ```

- EC2Instances can have SSMInstancePatches
    ```
    (EC2Instance)-[HAS_PATCH]->(SSMInstancePatch)
    ```

### EC2KeyPair

Representation of an AWS [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_KeyPairInfo.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| keyname | The name of the key pair |
| keyfingerprint | The fingerprint of the public key |
| region| The AWS region |
| **arn** | AWS-unique identifier for this object |
| id | same as `arn` |
| user_uploaded | `user_uploaded` is set to `True` if the the KeyPair was uploaded to AWS. Uploaded KeyPairs will have 128-bit MD5 hashed `keyfingerprint`, and KeyPairs from AWS will have 160-bit SHA-1 hashed `keyfingerprint`s. |
| duplicate_keyfingerprint | `duplicate_keyfingerprint` is set to `True` if the KeyPair has the same `keyfingerprint` as another KeyPair. |

#### Relationships

- EC2 key pairs are contained in AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(EC2KeyPair)
    ```

- EC2 key pairs can be used to log in to AWS EC2 isntances.
    ```
    (EC2KeyPair)-[SSH_LOGIN_TO]->(EC2Instance)
    ```

- EC2 key pairs have matching `keyfingerprint`.
    ```
    (EC2KeyPair)-[MATCHING_FINGERPRINT]->(EC2KeyPair)
    ```

### EC2PrivateIp
Representation of an AWS EC2 [InstancePrivateIpAddress](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstancePrivateIpAddress.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| network_interface_id   | id of the network interface with which the IP is associated with  |
| primary   |  Indicates whether this IPv4 address is the primary private IP address of the network interface.  |
| private_ip_address   |  The private IPv4 address of the network interface. |
| public_ip   |  The public IP address or Elastic IP address bound to the network interface. |
| ip_owner_id  | Id of the owner, e.g. `amazon-elb` for ELBs  |

#### Relationships

- EC2PrivateIps are connected with NetworkInterfaces.
    ```
    (NetworkInterface)-[PRIVATE_IP_ADDRESS]->(EC2PrivateIp)
    ```


### EC2Reservation
Representation of an AWS EC2 [Reservation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Reservation.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| requesterid | The ID of the requester that launched the instances on your behalf |
| **reservationid** | The ID of the reservation. |
| region| The AWS region |
| ownerid | The ID of the AWS account that owns the reservation. |

#### Relationships

- EC2 reservations are contained in AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(EC2Reservation)
    ```

- EC2 Instances are members of EC2 reservations.
    ```
    (EC2Instance)-[MEMBER_OF_EC2_RESERVATION]->(EC2Reservation)
    ```


### EC2SecurityGroup
Representation of an AWS EC2 [Security Group](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_SecurityGroup.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| groupid | The ID of the security group|
| name | The name of the security group|
| description | A description of the security group|
| **id** | Same as `groupid` |
| region | The AWS region this security group is installed in|


#### Relationships

- EC2 Instances, Network Interfaces, Load Balancers, Elastic Search Domains, IP Rules, IP Permission Inbound nodes, and RDS Instances can be members of EC2 Security Groups.
    ```
    (EC2Instance,
        NetworkInterface,
        LoadBalancer,
        ESDomain,
        IpRule,
        IpPermissionInbound,
        RDSInstance,
        AWSVpc)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- Load balancers can define inbound [Source Security Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-security-groups.html).
    ```
    (LoadBalancer)-[SOURCE_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- AWS Accounts contain EC2 Security Groups.
    ```
    (AWSAccount)-[RESOURCE]->(EC2SecurityGroup)
    ```

-  EC2 SecurityGroups can be tagged with AWSTags.
    ```
    (EC2SecurityGroup)-[TAGGED]->(AWSTag)
    ```

- Redshift clusters can be members of EC2 Security Groups.
    ```
    (RedshiftCluster)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```


### EC2Subnet

Representation of an AWS EC2 [Subnet](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Subnet.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **subnetid** | The ID of the subnet|
| **id** | same as subnetid |
| region| The AWS region the subnet is installed on|
| name | The IPv4 CIDR block assigned to the subnet|
| cidr_block | The IPv4 CIDR block assigned to the subnet|
| available_ip_address_count | The number of unused private IPv4 addresses in the subnet. The IPv4 addresses for any stopped instances are considered unavailable |
| default_for_az | Indicates whether this is the default subnet for the Availability Zone. |
| map_customer_owned_ip_on_launch | Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives a customer-owned IPv4 address |
| map_public_ip_on_launch | Indicates whether instances launched in this subnet receive a public IPv4 address |
| subnet_arn | The Amazon Resource Name (ARN) of the subnet |
| availability_zone | The Availability Zone of the subnet |
| availability_zone_id | The AZ ID of the subnet |
| state | The current state of the subnet. |
| assignipv6addressoncreation | Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives an IPv6 address. |


#### Relationships

- A Network Interface can be part of an EC2 Subnet.
    ```
    (NetworkInterface)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- An EC2 Instance can be part of an EC2 Subnet.
    ```
    (EC2Instance)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- A LoadBalancer can be part of an EC2 Subnet.
    ```
    (LoadBalancer)-[SUBNET]->(EC2Subnet)
    ```

- A LoadBalancer can be part of an EC2 Subnet.
    ```
    (LoadBalancer)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- A LoadBalancerV2 can be part of an EC2 Subnet.
    ```
    (LoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
    ```


- DB Subnet Groups consist of EC2 Subnets
    ```
    (DBSubnetGroup)-[RESOURCE]->(EC2Subnet)
    ```


-  EC2 Subnets can be tagged with AWSTags.
    ```
    (EC2Subnet)-[TAGGED]->(AWSTag)
    ```

-  EC2 Subnets are member of a VPC.
    ```
    (EC2Subnet)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```

-  EC2 Subnets belong to AWS Accounts
    ```
    (AWSAccount)-[RESOURCE]->(EC2Subnet)
    ```

-  EC2PrivateIps are connected with NetworkInterfaces.
    ```
    (NetworkInterface)-[PRIVATE_IP_ADDRESS]->(EC2PrivateIp)
    ```

- EC2RouteTableAssociation is associated with a subnet.
    ```
    (EC2RouteTableAssociation)-[ASSOCIATED_SUBNET]->(EC2Subnet)
    ```


### AWSInternetGateway

 Representation of an AWS [Interent Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InternetGateway.html).

 | Field | Description |
 |--------|-----------|
 | **id** | Internet gateway ID |
 | arn | Amazon Resource Name |
 | region | The region of the gateway |


#### Relationships

 -  Internet Gateways are attached to a VPC.
    ```
    (AWSInternetGateway)-[ATTACHED_TO]->(AWSVpc)
    ```

 -  Internet Gateways belong to AWS Accounts
    ```
    (AWSAccount)-[RESOURCE]->(AWSInternetGateway)
    ```

- EC2RouteTableAssociation is associated with an internet gateway. In this configuration, AWS uses this given route table to decide how to route packets that arrive through the given IGW.
    ```
    (EC2RouteTableAssociation)-[ASSOCIATED_IGW_FOR_INGRESS]->(AWSInternetGateway)
    ```

- EC2Route routes to an AWSInternetGateway. In most cases this tells AWS "to reach the internet, use this IGW".
    ```
    (EC2Route)-[ROUTES_TO_GATEWAY]->(AWSInternetGateway)
    ```


### ECRRepository

Representation of an AWS Elastic Container Registry [Repository](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_Repository.html).

| Field | Description |
|--------|-----------|
| **id** | Same as ARN |
| arn | The ARN of the repository |
| name | The name of the repository |
| region | The region of the repository |
| created_at | Date and time when the repository was created |

#### Relationships

- An ECRRepository contains ECRRepositoryImages:
    ```
    (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage)
    ```


### EC2NetworkAcl

 Representation of an AWS [EC2 Network ACL](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAcl.html)

 | Field          | Description                                                    |
 |----------------|----------------------------------------------------------------|
 | **id**         | The arn of the network ACL                                     |
 | **arn**        | Amazon Resource Name                                           |
 | network_acl_id | The ID of the network ACL                                      |
 | is_default     | Indicates whether this is the default network ACL for the VPC. |
 | vpc_id         | The ID of the VPC this ACL is associated with                  |
 | region         | The region                                                     |


#### Relationships

-  EC2 Network ACLs have ingress and egress rules
    ```
    (:EC2NetworkAcl)-[:MEMBER_OF_NACL]->(:EC2NetworkAclRule:IpPermissionInbound)
    ```

    ```
    (:EC2NetworkAcl)-[:MEMBER_OF_NACL]->(:EC2NetworkAclRule:IpPermissionEgress)
    ```

- EC2 Network ACLs define egress and ingress rules on subnets
    ```
    (:EC2NetworkAcl)-[:PART_OF_SUBNET]->(:EC2Subnet)
    ```

- EC2 Network ACLs are attached to VPCs.
    ```
    (:EC2NetworkAcl)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)
    ```

- EC2 Network ACLs belong to AWS Accounts
    ```
    (:AWSAccount)-[:RESOURCE]->(:EC2NetworkAcl)
    ```


### EC2NetworkAclRule :: IpPermissionInbound / IpPermissionEgress

Representation of an AWS [EC2 Network ACL Rule Entry](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAclEntry.html)
For additional explanation see https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html.

| Field          | Description                                                                                                                  |
|----------------|------------------------------------------------------------------------------------------------------------------------------|
| **id**         | The ID of this rule: `{network_acl_id}/{egress or inbound}/{rule_number}`                                                    |
| network_acl_id | The ID of the network ACL that this belongs to                                                                               |
| protocol       | Indicates whether this is the default network ACL for the VPC.                                                               |
| fromport       | First port in the range that this rule applies to                                                                            |
| toport         | Last port in the range that this rule applies to                                                                             |
| cidrblock      | The IPv4 network range to allow or deny, in CIDR notation.                                                                   |
| ipv6cidrblock  | The IPv6 network range to allow or deny, in CIDR notation. You must specify an IPv4 CIDR block or an IPv6 CIDR block.        |
| egress         | Indicates whether the rule is an egress rule (applied to traffic leaving the subnet).                                        |
| rulenumber     | The rule number for the entry. ACL entries are processed in ascending order by rule number.                                  |
| ruleaction     | Indicates whether to `allow` or `den` the traffic that matches the rule.                                                     |
| region         | The region                                                                                                                   |


#### Relationships

-  EC2 Network ACLs have ingress and egress rules
    ```
    (:EC2NetworkAcl)-[:MEMBER_OF_NACL]->(:EC2NetworkAclRule:IpPermissionInbound)
    ```

    ```
    (:EC2NetworkAcl)-[:MEMBER_OF_NACL]->(:EC2NetworkAclRule:IpPermissionEgress)
    ```

 -  EC2 Network ACL Ruless belong to AWS Accounts
    ```
    (:AWSAccount)-[:RESOURCE]->(:EC2NetworkAclRule)
    ```


### ECRRepositoryImage

An ECR image may be referenced and tagged by more than one ECR Repository. To best represent this, we've created an
`ECRRepositoryImage` node as a layer of indirection between the repo and the image.

More concretely explained, we run
[`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html), and then
store the image tag on an `ECRRepositoryImage` node and the image digest hash on a separate `ECRImage` node.

This way, more than one `ECRRepositoryImage` can reference/be connected to the same `ECRImage`.

| Field | Description |
|--------|-----------|
| tag | The tag applied to the repository image, e.g. "latest" |
| uri | The URI where the repository image is stored |
| **id** | same as uri |
| image_size_bytes | The size of the image in bytes |
| image_pushed_at | The date and time the image was pushed to the repository |
| image_manifest_media_type | The media type of the image manifest, see [opencontainers image spec](https://github.com/opencontainers/image-spec/blob/main/media-types.md) |
| artifact_media_type | The media type of the image artifact |
| last_recorded_pull_time | The date and time the image was last pulled |

#### Relationships

- An ECRRepository contains ECRRepositoryImages:
    ```
    (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage)
    ```

- ECRRepositoryImages reference ECRImages
    ```
    (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage)
    ```


### ECRImage

Representation of an ECR image identified by its digest (e.g. a SHA hash). Specifically, this is the "digest part" of
[`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html). Also see
ECRRepositoryImage.

| Field | Description |
|--------|-----------|
| digest | The hash of this ECR image |
| **id** | Same as digest |

#### Relationships

- ECRRepositoryImages reference ECRImages
    ```
    (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage)
    ```

- Software packages are a part of ECR Images
    ```
    (:Package)-[:DEPLOYED]->(:ECRImage)
    ```


### Package

Representation of a software package, as found by an AWS ECR vulnerability scan.

| Field | Description |
|-------|-------------|
| **id** | Concatenation of ``{version}\|{name}`` |
| version | The version of the package, includes the Linux distro that it was built for |
| name | The name of the package |

#### Relationships

- Software packages are a part of ECR Images
    ```
    (:Package)-[:DEPLOYED]->(:ECRImage)
    ```

- AWS ECR scans yield ECRScanFindings that affect software packages
    ```
    (:ECRScanFindings)-[:AFFECTS]->(:Package)
    ```


### ECRScanFinding (:Risk:CVE)

Representation of a scan finding from AWS ECR. This is the result output of [`ecr.describe_image_scan_findings()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_DescribeImageScanFindings.html).

| Field | Description |
|--------|-----------|
| name | The name of the ECR scan finding, e.g. a CVE name |
| **id** | Same as name |
| severity | The severity of the risk |
| uri | A URI link to a descriptive article on the risk |

#### Relationships

- AWS ECR scans yield ECRScanFindings that affect software packages
    ```
    (:ECRScanFindings)-[:AFFECTS]->(:Package)
    ```



### EKSCluster

Representation of an AWS [EKS Cluster](https://docs.aws.amazon.com/eks/latest/APIReference/API_Cluster.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| created_at | The date and time the cluster was created |
| region | The AWS region |
| **arn** | AWS-unique identifier for this object |
| id | same as `arn` |
| name | Name of the EKS Cluster |
| endpoint | The endpoint for the Kubernetes API server. |
| endpoint_public_access | Indicates whether the Amazon EKS public API server endpoint is enabled |
| exposed_internet | Set to True if the EKS Cluster public API server endpoint is enabled |
| rolearn | The ARN of the IAM role that provides permissions for the Kubernetes control plane to make calls to AWS API |
| version | Kubernetes version running |
| platform_version | Version of EKS |
| status | Status of the cluster. Valid Values: creating, active, deleting, failed, updating |
| audit_logging | Whether audit logging is enabled |

#### Relationships

- EKS Clusters belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(EKSCluster)
    ```

### EMRCluster

Representation of an AWS [EMR Cluster](https://docs.aws.amazon.com/emr/latest/APIReference/API_Cluster.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| region | The AWS region |
| **arn** | AWS-unique identifier for this object |
| id | The Id of the EMR Cluster. |
| instance\_collection\_type | The instance group configuration of the cluster. A value of INSTANCE\_GROUP indicates a uniform instance group configuration. A value of INSTANCE\_FLEET indicates an instance fleets configuration. |
| log\_encryption\_kms\_key\_id | The KMS key used for encrypting log files. |
| requested\_ami\_version | The AMI version requested for this cluster. |
| running\_ami\_version | The AMI version running on this cluster. |
| release\_label | The Amazon EMR release label, which determines the version of open-source application packages installed on the cluster. |
| auto\_terminate | Specifies whether the cluster should terminate after completing all steps. |
| termination\_protected | Indicates whether Amazon EMR will lock the cluster to prevent the EC2 instances from being terminated by an API call or user intervention, or in the event of a cluster error. |
| visible\_to\_all\_users | Indicates whether the cluster is visible to IAM principals in the Amazon Web Services account associated with the cluster. |
| master\_public\_dns\_name | The DNS name of the master node. If the cluster is on a private subnet, this is the private DNS name. On a public subnet, this is the public DNS name. |
| security\_configuration | The name of the security configuration applied to the cluster. |
| autoscaling\_role | An IAM role for automatic scaling policies. |
| scale\_down\_behavior | The way that individual Amazon EC2 instances terminate when an automatic scale-in activity occurs or an instance group is resized. |
| custom\_ami\_id | The ID of a custom Amazon EBS-backed Linux AMI if the cluster uses a custom AMI. |
| repo\_upgrade\_on\_boot | Specifies the type of updates that are applied from the Amazon Linux AMI package repositories when an instance boots using the AMI. |
| outpost\_arn | The Amazon Resource Name (ARN) of the Outpost where the cluster is launched. |
| log\_uri | The path to the Amazon S3 location where logs for this cluster are stored. |
| servicerole | Service Role of the EMR Cluster |


#### Relationships

- EMR Clusters belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(EMRCluster)
    ```


### ESDomain

Representation of an AWS [ElasticSearch Domain](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-configuration-api.html#es-configuration-api-datatypes) (see ElasticsearchDomainConfig).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| elasticsearch\_cluster\_config\_instancetype | The instancetype |
| elasticsearch\_version | The version of elasticsearch |
| elasticsearch\_cluster\_config\_zoneawarenessenabled | Indicates whether multiple Availability Zones are enabled.  |
| elasticsearch\_cluster\_config\_dedicatedmasterenabled | Indicates whether dedicated master nodes are enabled for the cluster. True if the cluster will use a dedicated master node. False if the cluster will not.  |
| elasticsearch\_cluster\_config\_dedicatedmastercount |Number of dedicated master nodes in the cluster.|
| elasticsearch\_cluster\_config\_dedicatedmastertype | Amazon ES instance type of the dedicated master nodes in the cluster.|
| domainid | Unique identifier for an Amazon ES domain. |
| encryption\_at\_rest\_options\_enabled | Specify true to enable encryption at rest. |
| deleted | Status of the deletion of an Amazon ES domain. True if deletion of the domain is complete. False if domain deletion is still in progress. |
| **id** | same as `domainid` |
| **arn** |Amazon Resource Name (ARN) of an Amazon ES domain. |
| exposed\_internet | `exposed_internet` is set to `True` if the ElasticSearch domain has a policy applied to it that makes it internet-accessible.  This policy determination is made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  The code for this augmentation is implemented at `cartography.intel.aws.elasticsearch._process_access_policy()`. |

#### Relationships

- Elastic Search domains can be members of EC2 Security Groups.
    ```
    (ESDomain)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- Elastic Search domains belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(ESDomain)
    ```

- DNS Records can point to Elastic Search domains.
    ```
    (DNSRecord)-[DNS_POINTS_TO]->(ESDomain)
    ```

### Endpoint

Representation of a generic network endpoint.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint |
| port | The port of this endpoint |


#### Relationships

- Endpoints can be installed load balancers, though more specifically we would refer to these Endpoint nodes as [ELBListeners](#endpoint::elblistener).
    ```
    (LoadBalancer)-[ELB_LISTENER]->(Endpoint)
    ```


### Endpoint::ELBListener

Representation of an AWS Elastic Load Balancer [Listener](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_Listener.html).  Here, an ELBListener is a more specific type of Endpoint.  Here'a [good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint |
| port | The port of this endpoint |
| policy\_names | A list of SSL policy names set on the listener.
| **id** | The ELB ID.  This is a concatenation of the DNS name, port, and protocol. |
| instance\_port | The port open on the EC2 instance that this listener is connected to |
| instance\_protocol | The protocol defined on the EC2 instance that this listener is connected to |


#### Relationships

- A ELBListener is installed on a load balancer.
    ```
    (LoadBalancer)-[ELB_LISTENER]->(ELBListener)
    ```

- A ELBListener is associated with an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(ELBListener)
    ```

### Endpoint::ELBV2Listener

Representation of an AWS Elastic Load Balancer V2 [Listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol of this endpoint - One of `'HTTP''HTTPS''TCP''TLS''UDP''TCP_UDP'` |
| port | The port of this endpoint |
| ssl\_policy | Only set for HTTPS or TLS listener. The security policy that defines which protocols and ciphers are supported. |
| targetgrouparn | The ARN of the Target Group, if the Action type is `forward`. |


#### Relationships

- A ELBV2Listener is installed on a LoadBalancerV2.
    ```
    (elbv2)-[r:ELBV2_LISTENER]->(ELBV2Listener)
    ```


### Ip

Represents a generic IP address.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **ip** | The IPv4 address |
| **id** | Same as `ip` |


#### Relationships

- DNSRecords can point to IP addresses.
    ```
    (DNSRecord)-[DNS_POINTS_TO]->(Ip)
    ```


### IpRule

Represents a generic IP rule.  The creation of this node is currently derived from ingesting AWS [EC2 Security Group](#ec2securitygroup) rules.

| Field | Description |
|-------|-------------|
| **ruleid** | `{group_id}/{rule_type}/{from_port}{to_port}{protocol}` |
| groupid | The groupid of the EC2 Security Group that this was derived from |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol this rule applies to |
| fromport | Lowest port in the range defined by this rule|
| toport | Highest port in the range defined by this rule|


#### Relationships

- IpRules are defined from EC2SecurityGroups.
    ```
    (IpRule, IpPermissionInbound)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```


### IpRule::IpPermissionInbound

An IpPermissionInbound node is a specific type of IpRule.  It represents a generic inbound IP-based rules.  The creation of this node is currently derived from ingesting AWS [EC2 Security Group](#ec2securitygroup) rules.

| Field | Description |
|-------|-------------|
| **ruleid** | `{group_id}/{rule_type}/{from_port}{to_port}{protocol}` |
| groupid |  The groupid of the EC2 Security Group that this was derived from |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol this rule applies to |
| fromport | Lowest port in the range defined by this rule|
| toport | Highest port in the range defined by this rule|

#### Relationships

- IpPermissionInbound rules are defined from EC2SecurityGroups.
    ```
    (IpRule, IpPermissionInbound)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```


### LoadBalancer

Represents a classic [AWS Elastic Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).  See [spec for details](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| scheme|  The type of load balancer. Valid only for load balancers in a VPC. If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| name| The name of the load balancer|
| **dnsname** | The DNS name of the load balancer. |
| canonicalhostedzonename| The DNS name of the load balancer |
| **id** |  Currently set to the `dnsname` of the load balancer. |
| region| The region of the load balancer |
|createdtime | The date and time the load balancer was created. |
|canonicalhostedzonenameid| The ID of the Amazon Route 53 hosted zone for the load balancer. |
| exposed\_internet | The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. |


#### Relationships

- LoadBalancers can be connected to EC2Instances and therefore expose them.
    ```
    (LoadBalancer)-[EXPOSE]->(EC2Instance)
    ```

- LoadBalancers can have [source security groups](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_SourceSecurityGroup.html) configured.
    ```
    (LoadBalancer)-[SOURCE_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- LoadBalancers can be part of EC2SecurityGroups.
    ```
    (LoadBalancer)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- LoadBalancers can be part of EC2 Subnets
    ```
    (LoadBalancer)-[SUBNET]->(EC2Subnet)
    ```


- LoadBalancers can be part of EC2 Subnets
    ```
    (LoadBalancer)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- LoadBalancers can have listeners configured to accept connections from clients ([good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html)).
    ```
    (LoadBalancer)-[ELB_LISTENER]->(Endpoint, ELBListener)
    ```

- LoadBalancers are part of AWSAccounts.
    ```
    (AWSAccount)-[RESOURCE]->(LoadBalancer)
    ```

- AWSDNSRecords and DNSRecords point to LoadBalancers.
    ```
    (AWSDNSRecord, DNSRecord)-[DNS_POINTS_TO]->(LoadBalancer)
    ```

### LoadBalancerV2
Represents an Elastic Load Balancer V2 ([Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) or [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html).) API reference [here](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancer.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| scheme|  The type of load balancer.  If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| name| The name of the load balancer|
| **dnsname** | The DNS name of the load balancer. |
| exposed_internet | The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. |
| **id** |  Currently set to the `dnsname` of the load balancer. |
| type | Can be `application` or `network` |
| region| The region of the load balancer |
|createdtime | The date and time the load balancer was created. |
|canonicalhostedzonenameid| The ID of the Amazon Route 53 hosted zone for the load balancer. |


#### Relationships


- LoadBalancerV2's can be connected to EC2Instances and therefore expose them.
    ```
    (LoadBalancerV2)-[EXPOSE]->(EC2Instance)
    ```
`EXPOSE` relationshiohip also holds the protocol, port and TargetGroupArn the load balancer points to.

- LoadBalancerV2's can be part of EC2SecurityGroups but only if their `type` = "application". NLBs don't have SGs.
    ```
    (LoadBalancerV2)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- LoadBalancerV2's can be part of EC2 Subnets
    ```
    (LoadBalancerV2)-[SUBNET]->(EC2Subnet)
    ```

- LoadBalancerV2's can be part of EC2 Subnets
    ```
    (LoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- LoadBalancerV2's have [listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html):
    ```
    (LoadBalancerV2)-[ELBV2_LISTENER]->(ELBV2Listener)
    ```

### Nameserver

Represents a DNS nameserver.
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The address of the nameserver|
| name |  The name or address of the nameserver|

#### Relationships

- Nameservers are nameservers for to DNSZone.
    ```
    (Nameserver)-[NAMESERVER]->(DNSZone)
    ```

### NetworkInterface

Representation of a generic Network Interface.  Currently however, we only create NetworkInterface nodes from AWS [EC2 Instances](#ec2instance).  The spec for an AWS EC2 network interface is [here](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceNetworkInterface.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| mac\_address| The MAC address of the network interface|
| description |  Description of the network interface|
| private\_ip\_address| The primary IPv4 address of the network interface within the subnet |
| **id** | The ID of the network interface.  (known as `networkInterfaceId` in EC2) |
| private\_dns\_name| The private DNS name |
| status | Status of the network interface.  Valid Values: ``available \| associated \| attaching \| in-use \| detaching `` |
| subnetid | The ID of the subnet |
| interface_type  |  Describes the type of network interface. Valid values: `` interface \| efa `` |
| requester_id  | Id of the requester, e.g. `amazon-elb` for ELBs |
| requester_managed  |  Indicates whether the interface is managed by the requester |
| source_dest_check   | Indicates whether to validate network traffic to or from this network interface.  |
| public_ip   | Public IPv4 address attached to the interface  |


#### Relationships

-  EC2 Network Interfaces belong to AWS accounts.

        (NetworkInterface)<-[:RESOURCE]->(:AWSAccount)

- Network interfaces can be connected to EC2Subnets.
    ```
    (NetworkInterface)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- Network interfaces can be members of EC2SecurityGroups.
    ```
    (NetworkInterface)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- EC2Instances can have NetworkInterfaces connected to them.
    ```
    (EC2Instance)-[NETWORK_INTERFACE]->(NetworkInterface)
    ```

- LoadBalancers can have NetworkInterfaces connected to them.
    ```
    (LoadBalancer)-[NETWORK_INTERFACE]->(NetworkInterface)
    ```

- LoadBalancerV2s can have NetworkInterfaces connected to them.
    ```
    (LoadBalancerV2)-[NETWORK_INTERFACE]->(NetworkInterface)
    ```

- EC2PrivateIps are connected to a NetworkInterface.
    ```
    (NetworkInterface)-[PRIVATE_IP_ADDRESS]->(EC2PrivateIp)
    ```

-  EC2 Network Interfaces can be tagged with AWSTags.
    ```
    (NetworkInterface)-[TAGGED]->(AWSTag)
    ```

### AWSPeeringConnection

Representation of an AWS [PeeringConnection](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) implementing an AWS [VpcPeeringConnection](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcPeeringConnection.html) object.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | vpcPeeringConnectionId, The ID of the VPC peering connection. |
| allow_dns_resolution_from_remote_vpc | Indicates whether a local VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC. |
| allow_egress_from_local_classic_link_to_remote_vpc | Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection.  |
| allow_egress_from_local_vpc_to_remote_classic_link | Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection. |
| requester_region | Peering requester region |
| accepter_region | Peering accepter region |
| status_code | The status of the VPC peering connection. |
| status_message | A message that provides more information about the status, if applicable. |

#### Relationships

- `AWSVpc` is an accepter or requester vpc.
  ```
  (AWSVpc)<-[REQUESTER_VPC]-(AWSPeeringConnection)
  (AWSVpc)<-[ACCEPTER_VPC]-(AWSPeeringConnection)
  ```

- `AWSCidrBlock` is an accepter or requester cidr.
  ```
  (AWSCidrBlock)<-[REQUESTER_CIDR]-(AWSPeeringConnection)
  (AWSCidrBlock)<-[ACCEPTER_CIDR]-(AWSPeeringConnection)
  ```

### RedshiftCluster

Representation of an AWS [RedshiftCluster](https://docs.aws.amazon.com/redshift/latest/APIReference/API_Cluster.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **arn** | The Amazon Resource Name (ARN) for the Redshift cluster |
| **id** | Same as arn |
| availability\_zone | Specifies the name of the Availability Zone the cluster is located in |
| cluster\_create\_time | Provides the date and time the cluster was created |
| cluster\_identifier | The unique identifier of the cluster. |
| cluster_revision_number | The specific revision number of the database in the cluster. |
| db_name | The name of the initial database that was created when the cluster was created. This same name is returned for the life of the cluster. If an initial database was not specified, a database named devdev was created by default. |
| encrypted | Specifies whether the cluster has encryption enabled |
| cluster\_status | The current state of the cluster. |
| endpoint\_address | DNS name of the Redshift cluster endpoint |
| endpoint\_port | The port that the Redshift cluster's endpoint is listening on  |
| master\_username | The master user name for the cluster. This name is used to connect to the database that is specified in the DBName parameter. |
| node_type | The node type for the nodes in the cluster. |
| number\_of\_nodes | The number of compute nodes in the cluster. |
| publicly_accessible | A boolean value that, if true, indicates that the cluster can be accessed from a public network. |
| vpc_id | The identifier of the VPC the cluster is in, if the cluster is in a VPC. |


#### Relationships

- Redshift clusters are part of AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(RedshiftCluster)
    ```

- Redshift clusters can be members of EC2 Security Groups.
    ```
    (RedshiftCluster)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- Redshift clusters may assume IAM roles. See [this article](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html).
    ```
    (RedshiftCluster)-[STS_ASSUMEROLE_ALLOW]->(AWSPrincipal)
    ```

- Redshift clusters can be members of AWSVpcs.
    ```
    (RedshiftCluster)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```

### RDSCluster

Representation of an AWS Relational Database Service [DBCluster](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBCluster.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the DB cluster. |
| **allocated\_storage** | For all database engines except Amazon Aurora, AllocatedStorage specifies the allocated storage size in gibibytes (GiB). For Aurora, AllocatedStorage always returns 1, because Aurora DB cluster storage size isn't fixed, but instead automatically adjusts as needed. |
| **availability\_zones** | Provides the list of Availability Zones (AZs) where instances in the DB cluster can be created. |
| **backup\_retention\_period** | Specifies the number of days for which automatic DB snapshots are retained. |
| **character\_set\_name** | If present, specifies the name of the character set that this cluster is associated with. |
| **database\_name** | Contains the name of the initial database of this DB cluster that was provided at create time, if one was specified when the DB cluster was created. This same name is returned for the life of the DB cluster. |
| **db\_cluster\_identifier** | Contains a user-supplied DB cluster identifier. This identifier is the unique key that identifies a DB cluster. |
| **db\_parameter\_group** | Specifies the name of the DB cluster parameter group for the DB cluster. |
| **status** | Specifies the current state of this DB cluster. |
| **earliest\_restorable\_time** | The earliest time to which a database can be restored with point-in-time restore. |
| **endpoint** | Specifies the connection endpoint for the primary instance of the DB cluster. |
| **reader\_endpoint** | The reader endpoint for the DB cluster. The reader endpoint for a DB cluster load-balances connections across the Aurora Replicas that are available in a DB cluster. As clients request new connections to the reader endpoint, Aurora distributes the connection requests among the Aurora Replicas in the DB cluster. This functionality can help balance your read workload across multiple Aurora Replicas in your DB cluster. If a failover occurs, and the Aurora Replica that you are connected to is promoted to be the primary instance, your connection is dropped. To continue sending your read workload to other Aurora Replicas in the cluster, you can then reconnect to the reader endpoint. |
| **multi\_az** | Specifies whether the DB cluster has instances in multiple Availability Zones. |
| **engine** | The name of the database engine to be used for this DB cluster. |
| **engine\_version** | Indicates the database engine version. |
| **latest\_restorable\_time** | Specifies the latest time to which a database can be restored with point-in-time restore. |
| **port** | Specifies the port that the database engine is listening on. |
| **master\_username** | Contains the master username for the DB cluster. |
| **preferred\_backup\_window** | Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod. |
| **preferred\_maintenance\_window** | Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC). |
| **hosted\_zone\_id** | Specifies the ID that Amazon Route 53 assigns when you create a hosted zone. |
| **storage\_encrypted** | Specifies whether the DB cluster is encrypted. |
| **kms\_key\_id** | If StorageEncrypted is enabled, the AWS KMS key identifier for the encrypted DB cluster. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the AWS KMS customer master key (CMK). |
| **db\_cluster\_resource\_id** | The AWS Region-unique, immutable identifier for the DB cluster. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS CMK for the DB cluster is accessed. |
| **clone\_group\_id** | Identifies the clone group to which the DB cluster is associated. |
| **cluster\_create\_time** | Specifies the time when the DB cluster was created, in Universal Coordinated Time (UTC). |
| **earliest\_backtrack\_time** | The earliest time to which a DB cluster can be backtracked. |
| **backtrack\_window** | The target backtrack window, in seconds. If this value is set to 0, backtracking is disabled for the DB cluster. Otherwise, backtracking is enabled. |
| **backtrack\_consumed\_change\_records** | The number of change records stored for Backtrack. |
| **capacity** | The current capacity of an Aurora Serverless DB cluster. The capacity is 0 (zero) when the cluster is paused. |
| **engine\_mode** | The DB engine mode of the DB cluster, either provisioned, serverless, parallelquery, global, or multimaster. |
| **scaling\_configuration\_info\_min\_capacity** | The minimum capacity for the Aurora DB cluster in serverless DB engine mode. |
| **scaling\_configuration\_info\_max\_capacity** | The maximum capacity for an Aurora DB cluster in serverless DB engine mode. |
| **scaling\_configuration\_info\_auto\_pause** | A value that indicates whether automatic pause is allowed for the Aurora DB cluster in serverless DB engine mode. |
| **deletion\_protection** | Indicates if the DB cluster has deletion protection enabled. The database can't be deleted when deletion protection is enabled. |

#### Relationships

- RDS Clusters are part of AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(RDSCluster)
    ```

- Some RDS instances are cluster members.
    ```
    (replica:RDSInstance)-[IS_CLUSTER_MEMBER_OF]->(source:RDSCluster)
    ```

### RDSInstance

Representation of an AWS Relational Database Service [DBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBInstance.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the DB instance. |
| **db\_instance_identifier**           | Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| availability\_zone                | Specifies the name of the Availability Zone the DB instance is located in.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| backup\_retention\_period          | Specifies the number of days for which automatic DB snapshots are retained.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| preferred\_backup\_window          | Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ca\_certificate\_identifier        | The identifier of the CA certificate for this DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| db\_cluster\_identifier            | If the DB instance is a member of a DB cluster, contains the name of the DB cluster that the DB instance is a member of.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| db\_instance\_class                | Contains the name of the compute and memory capacity class of the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| db\_instance\_port                 | Specifies the port that the DB instance listens on.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| dbi\_resource\_id                  | The AWS Region-unique, immutable identifier for the DB instance. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS key for the DB instance is accessed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| db\_name                          | The meaning of this parameter differs according to the database engine you use. For example, this value returns MySQL, MariaDB, or PostgreSQL information when returning values from CreateDBInstanceReadReplica since Read Replicas are only supported for these engines.<br><br>**MySQL, MariaDB, SQL Server, PostgreSQL:** Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created. This same name is returned for the life of the DB instance.<br><br>**Oracle:** Contains the Oracle System ID (SID) of the created DB instance. Not shown when the returned parameters do not apply to an Oracle DB instance. |
| engine                           | Provides the name of the database engine to be used for this DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| engine\_version                   | Indicates the database engine version.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| enhanced\_monitoring\_resource\_arn | The Amazon Resource Name (ARN) of the Amazon CloudWatch Logs log stream that receives the Enhanced Monitoring metrics data for the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| instance\_create\_time             | Provides the date and time the DB instance was created.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| kms\_key\_id                       | If StorageEncrypted is true, the AWS KMS key identifier for the encrypted DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| master\_username                  | Contains the master username for the DB instance.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| monitoring\_role\_arn              | The ARN for the IAM role that permits RDS to send Enhanced Monitoring metrics to Amazon CloudWatch Logs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| multi\_az                         | Specifies if the DB instance is a Multi-AZ deployment.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| performance\_insights\_enabled     | True if Performance Insights is enabled for the DB instance, and otherwise false.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| preferred\_maintenance\_window     | Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| publicly\_accessible              | Specifies the accessibility options for the DB instance. A value of true specifies an Internet-facing instance with a publicly resolvable DNS name, which resolves to a public IP address. A value of false specifies an internal instance with a DNS name that resolves to a private IP address.                                                                                                                                                                                                                                                                                                                                                                                    |
| storage\_encrypted                | Specifies whether the DB instance is encrypted.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| endpoint\_address                 | DNS name of the RDS instance|
| endpoint\_port                    | The port that the RDS instance is listening on |
| endpoint\_hostedzoneid            | The AWS DNS Zone ID that is associated with the RDS instance's DNS entry |
| auto\_minor\_version\_upgrade       | Specifies whether minor version upgrades are applied automatically to the DB instance during the maintenance window |
| iam\_database\_authentication\_enabled       | Specifies if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled |



#### Relationships

- RDS Instances are part of AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(RDSInstance)
    ```

- Some RDS instances are Read Replicas.
    ```
    (replica:RDSInstance)-[IS_READ_REPLICA_OF]->(source:RDSInstance)
    ```

- RDS Instances can be members of EC2 Security Groups.
    ```
    (RDSInstance)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- RDS Instances are connected to DB Subnet Groups.
    ```
    (RDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(DBSubnetGroup)
    ```

-  RDS Instances can be tagged with AWSTags.
    ```
    (RDSInstance)-[TAGGED]->(AWSTag)
    ```

### RDSSnapshot

Representation of an AWS Relational Database Service [DBSnapshot](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSnapshot.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the DB snapshot. |
| **db\_snapshot\_identifier** | Specifies the identifier for the DB snapshot. |
| db\_instance\_identifier | Specifies the DB instance identifier of the DB instance this DB snapshot was created from. |
| snapshot\_create\_time | Specifies when the snapshot was taken in Coordinated Universal Time (UTC). Changes for the copy when the snapshot is copied. |
| engine | Specifies the name of the database engine. |
| allocated\_storage | Specifies the allocated storage size in gibibytes (GiB). |
| status | Specifies the status of this DB snapshot. |
| port | Specifies the port that the database engine was listening on at the time of the snapshot. |
| availability\_zone | Specifies the name of the Availability Zone the DB instance was located in at the time of the DB snapshot. |
| vpc\_id | Provides the VPC ID associated with the DB snapshot. |
| instance\_create\_time | Specifies the time in Coordinated Universal Time (UTC) when the DB instance, from which the snapshot was taken, was created. |
| master\_username | Provides the master username for the DB snapshot. |
| engine\_version | Specifies the version of the database engine. |
| license\_model | License model information for the restored DB instance. |
| snapshot\_type | Provides the type of the DB snapshot. |
| iops | Specifies the Provisioned IOPS (I/O operations per second) value of the DB instance at the time of the snapshot. |
| option\_group\_name | Provides the option group name for the DB snapshot. |
| percent\_progress | The percentage of the estimated data that has been transferred. |
| source\_region | The AWS Region that the DB snapshot was created in or copied from. |
| source\_db\_snapshot\_identifier | The DB snapshot Amazon Resource Name (ARN) that the DB snapshot was copied from. It only has a value in the case of a cross-account or cross-Region copy. |
| storage\_type | Specifies the storage type associated with DB snapshot. |
| tde\_credential\_arn | The ARN from the key store with which to associate the instance for TDE encryption. |
| encrypted | Specifies whether the DB snapshot is encrypted. |
| kms\_key\_id | If Encrypted is true, the AWS KMS key identifier for the encrypted DB snapshot. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the KMS key. |
| timezone | The time zone of the DB snapshot. In most cases, the Timezone element is empty. Timezone content appears only for snapshots taken from Microsoft SQL Server DB instances that were created with a time zone specified. |
| iam\_database\_authentication\_enabled | True if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled, and otherwise false. |
| processor\_features | The number of CPU cores and the number of threads per core for the DB instance class of the DB instance when the DB snapshot was created. |
| dbi\_resource\_id | The identifier for the source DB instance, which can't be changed and which is unique to an AWS Region. |
| original\_snapshot\_create\_time | Specifies the time of the CreateDBSnapshot operation in Coordinated Universal Time (UTC). Doesn't change when the snapshot is copied. |
| snapshot\_database\_time | The timestamp of the most recent transaction applied to the database that you're backing up. Thus, if you restore a snapshot, SnapshotDatabaseTime is the most recent transaction in the restored DB instance. In contrast, originalSnapshotCreateTime specifies the system time that the snapshot completed. If you back up a read replica, you can determine the replica lag by comparing SnapshotDatabaseTime with originalSnapshotCreateTime. For example, if originalSnapshotCreateTime is two hours later than SnapshotDatabaseTime, then the replica lag is two hours. |
| snapshot\_target | Specifies where manual snapshots are stored: AWS Outposts or the AWS Region. |
| storage\_throughput |  |
| region | The AWS region of the snapshot |



#### Relationships

- RDS Snapshots are part of AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(RDSSnapshot)
    ```

- RDS Snapshots are connected to DB Instances.
    ```
    (RDSSnapshot)-[:IS_SNAPSHOT_SOURCE]->(RDSInstance)
    ```

-  RDS Snapshots can be tagged with AWSTags.
    ```
    (RDSSnapshot)-[TAGGED]->(AWSTag)
    ```

### S3Acl

Representation of an AWS S3 [Access Control List](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3AccessControlList.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| granteeid | The ID of the grantee as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3Grantee.html) |
| displayname | Optional display name for the ACL |
| permission | Valid values: ``FULL_CONTROL \| READ \| WRITE \| READ_ACP \| WRITE_ACP`` (ACP = Access Control Policy)|
| **id** | The ID of this ACL|
| type |  The type of the [grantee](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Grantee.html).  Either ``CanonicalUser \| AmazonCustomerByEmail \| Group``. |
| ownerid| The ACL's owner ID as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3ObjectOwner.html)|


#### Relationships


- S3 Access Control Lists apply to S3 buckets.
    ```
    (S3Acl)-[APPLIES_TO]->(S3Bucket)
    ```

### S3Bucket

Representation of an AWS S3 [Bucket](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Bucket.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| creationdate | Date-time when the bucket was created |
| **id** | Same as `name`, as seen below |
| name | The name of the bucket.  This is guaranteed to be [globally unique](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets) |
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the bucket.  This list is taken by running [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse#internet-accessible-policy) on the policy that applies to the bucket.   |
| anonymous\_access | True if this bucket has a policy applied to it that allows anonymous access or if it is open to the internet.  These policy determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.  |
| region | The region that the bucket is in. Only defined if the S3 bucket has a [location constraint](https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro) |
| default\_encryption | True if this bucket has [default encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html) enabled. |
| encryption\_algorithm | The encryption algorithm used for default encryption. Only defined if the S3 bucket has default encryption enabled. |
| encryption\_key\_id | The KMS key ID used for default encryption. Only defined if the S3 bucket has SSE-KMS enabled as the default encryption method. |
| bucket\_key\_enabled | True if a bucket key is enabled, when using SSE-KMS as the default encryption method. |
| versioning\_status | The versioning state of the bucket. |
| mfa\_delete | Specifies whether MFA delete is enabled in the bucket versioning configuration. |
| block\_public\_acls | Specifies whether Amazon S3 should block public access control lists (ACLs) for this bucket and objects in this bucket. |
| ignore\_public\_acls | Specifies whether Amazon S3 should ignore public ACLs for this bucket and objects in this bucket. |
| block\_public\_acls | Specifies whether Amazon S3 should block public bucket policies for this bucket. |
| restrict\_public\_buckets | Specifies whether Amazon S3 should restrict public bucket policies for this bucket. |
| object_ownership | The bucket's [Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html) setting. `BucketOwnerEnforced` indicates that ACLs on the bucket and its objects are ignored. `BucketOwnerPreferred` and `ObjectWriter` indicate that ACLs still function; see [the AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html#object-ownership-overview) for details.|

#### Relationships

- S3Buckets are resources in an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(S3Bucket)
    ```

- S3 Access Control Lists apply to S3 buckets.
    ```
    (S3Acl)-[APPLIES_TO]->(S3Bucket)
    ```

-  S3 Buckets can be tagged with AWSTags.
    ```
    (S3Bucket)-[TAGGED]->(AWSTag)
    ```

### S3PolicyStatement

Representation of an AWS S3 [Bucket Policy Statements](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html) for controlling ownership of objects and ACLs of the bucket.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| policy_id | Optional string "Id" for the bucket's policy |
| policy_version| Version of the bucket's policy |
| **id** | The unique identifier for a bucket policy statement. <br>If the statement has an Sid the id will be calculated as _S3Bucket.id_/policy_statement/_index of statement in statement_/_Sid_. <br>If the statement has no Sid the id will be calculated as  _S3Bucket.id_/policy_statement/_index of statement in statement_/  |
| effect | Specifies "Deny" or "Allow" for the policy statement |
| action | Specifies permissions that policy statement applies to, as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-actions.html) |
| resource | Specifies the resource the bucket policy statement is based on |
| condition | Specifies conditions where permissions are granted: [examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html) |
| sid | Optional string to label the specific bucket policy statement |

#### Relationships

- S3PolicyStatements define the policy for S3 Buckets.
    ```
    (:S3Bucket)-[:POLICY_STATEMENT]->(:S3PolicyStatement)
    ```


### KMSKey

Representation of an AWS [KMS Key](https://docs.aws.amazon.com/kms/latest/APIReference/API_KeyListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the key|
| name |  The name of the key |
| description |  The description of the key |
| enabled |  Whether the key is enabled |
| region | The region where key is created|
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the key. |
| anonymous\_access | True if this key has a policy applied to it that allows anonymous access or if it is open to the internet. |

#### Relationships

- AWS KMS Keys are resources in an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(KMSKey)
    ```

- AWS KMS Key may also be refered as KMSAlias via aliases.
    ```
    (KMSKey)-[KNOWN_AS]->(KMSAlias)
    ```

- AWS KMS Key may also have KMSGrant based on grants.
    ```
    (KMSGrant)-[APPLIED_ON]->(KMSKey)
    ```

### KMSAlias

Representation of an AWS [KMS Key Alias](https://docs.aws.amazon.com/kms/latest/APIReference/API_AliasListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the alias|
| aliasname |  The name of the alias |
| targetkeyid |  The kms key id associated via this alias |

#### Relationships

- AWS KMS Key may also be refered as KMSAlias via aliases.
    ```
    (KMSKey)-[KNOWN_AS]->(KMSAlias)
    ```

### KMSGrant

Representation of an AWS [KMS Key Grant](https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the key grant|
| name |  The name of the key grant |
| granteeprincipal |  The principal associated with the key grant |
| creationdate | ISO 8601 date-time string when the grant was created |

#### Relationships

- AWS KMS Key may also have KMSGrant based on grants.
    ```
    (KMSGrant)-[APPLIED_ON]->(KMSKey)
    ```

### APIGatewayRestAPI

Representation of an AWS [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the REST API|
| createddate |  The timestamp when the REST API was created |
| version |  The version identifier for the API |
| minimumcompressionsize | A nullable integer that is used to enable or disable the compression of the REST API |
| disableexecuteapiendpoint | Specifies whether clients can invoke your API by using the default `execute-api` endpoint |
| region | The region where the REST API is created |
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the API. |
| anonymous\_access | True if this API has a policy applied to it that allows anonymous access or if it is open to the internet. |

#### Relationships

- AWS API Gateway REST APIs are resources in an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(APIGatewayRestAPI)
    ```

- AWS API Gateway REST APIs may be associated with an API Gateway Stage.
    ```
    (APIGatewayRestAPI)-[ASSOCIATED_WITH]->(APIGatewayStage)
    ```

- AWS API Gateway REST APIs may also have API Gateway Resource resources.
    ```
    (APIGatewayRestAPI)-[RESOURCE]->(APIGatewayResource)
    ```

### APIGatewayStage

Representation of an AWS [API Gateway Stage](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-stages.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The name of the API Gateway Stage|
| createddate |  The timestamp when the stage was created |
| deploymentid |  The identifier of the Deployment that the stage points to. |
| clientcertificateid | The identifier of a client certificate for an API stage. |
| cacheclusterenabled | Specifies whether a cache cluster is enabled for the stage. |
| cacheclusterstatus | The status of the cache cluster for the stage, if enabled. |
| tracingenabled | Specifies whether active tracing with X-ray is enabled for the Stage |
| webaclarn | The ARN of the WebAcl associated with the Stage |

#### Relationships

- AWS API Gateway REST APIs may be associated with an API Gateway Stage.
    ```
    (APIGatewayRestAPI)-[ASSOCIATED_WITH]->(APIGatewayStage)
    ```

- AWS API Gateway Stage may also contain a Client Certificate.
    ```
    (APIGatewayStage)-[HAS_CERTIFICATE]->(APIGatewayClientCertificate)
    ```

### APIGatewayClientCertificate

Representation of an AWS [API Gateway Client Certificate](https://docs.aws.amazon.com/apigateway/api-reference/resource/client-certificate/).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The identifier of the client certificate |
| createddate |  The timestamp when the client certificate was created |
| expirationdate |  The timestamp when the client certificate will expire |

#### Relationships

- AWS API Gateway Stage may also contain a Client Certificate.
    ```
    (APIGatewayStage)-[HAS_CERTIFICATE]->(APIGatewayClientCertificate)
    ```

### APIGatewayResource

Representation of an AWS [API Gateway Resource](https://docs.aws.amazon.com/apigateway/api-reference/resource/resource/).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the REST API|
| path |  The timestamp when the REST API was created |
| pathpart |  The version identifier for the API |
| parentid | A nullable integer that is used to enable or disable the compression of the REST API |

#### Relationships

- AWS API Gateway REST APIs may also have API Gateway Resource resources.
    ```
    (APIGatewayRestAPI)-[RESOURCE]->(APIGatewayResource)
    ```

### AutoScalingGroup

Representation of an AWS [Auto Scaling Group Resource](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **arn** | The ARN of the Auto Scaling Group|
| name |  The name of the Auto Scaling group. |
| createdtime | The date and time the group was created. |
| launchconfigurationname | The name of the associated launch configuration. |
| launchtemplatename | The name of the launch template. |
| launchtemplateid | The ID of the launch template. |
| launchtemplateversion | The version number of the launch template. |
| maxsize | The maximum size of the group.|
| minsize | The minimum size of the group.|
| defaultcooldown | The duration of the default cooldown period, in seconds. |
| desiredcapacity | The desired size of the group. |
| healthchecktype | The service to use for the health checks. |
| healthcheckgraceperiod | The amount of time, in seconds, that Amazon EC2 Auto Scaling waits before checking the health status of an EC2 instance that has come into service.|
| status | The current state of the group when the DeleteAutoScalingGroup operation is in progress. |
| newinstancesprotectedfromscalein | Indicates whether newly launched instances are protected from termination by Amazon EC2 Auto Scaling when scaling in.|
| maxinstancelifetime | The maximum amount of time, in seconds, that an instance can be in service. |
| capacityrebalance | Indicates whether Capacity Rebalancing is enabled. |
| region | The region of the auto scaling group. |


[Link to API Documentation](https://docs.aws.amazon.com/autoscaling/ec2/APIReference/API_AutoScalingGroup.html) of AWS Auto Scaling Groups

#### Relationships

- AWS Auto Scaling Groups are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AutoScalingGroup)
    ```

- AWS Auto Scaling Groups has one or more subnets/vpc identifiers.
    ```
    (AutoScalingGroup)-[VPC_IDENTIFIER]->(EC2Subnet)
    ```

- AWS EC2 Instances are members of one or more AWS Auto Scaling Groups.
    ```
    (EC2Instance)-[MEMBER_AUTO_SCALE_GROUP]->(AutoScalingGroup)
    ```

- AWS Auto Scaling Groups have Launch Configurations
    ```
    (AutoScalingGroup)-[HAS_LAUNCH_CONFIG]->(LaunchConfiguration)
    ```

- AWS Auto Scaling Groups have Launch Templates
    ```
    (AutoScalingGroup)-[HAS_LAUNCH_TEMPLATE]->(LaunchTemplate)
    ```

### EC2Image

Representation of an AWS [EC2 Images (AMIs)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the AMI.|
| name | The name of the AMI that was provided during image creation. |
| creationdate | The date and time the image was created. |
| architecture | The architecture of the image. |
| location | The location of the AMI.|
| type | The type of image.|
| ispublic | Indicates whether the image has public launch permissions. |
| platform | This value is set to `windows` for Windows AMIs; otherwise, it is blank. |
| usageoperation | The operation of the Amazon EC2 instance and the billing code that is associated with the AMI.  |
| state | The current state of the AMI.|
| description | The description of the AMI that was provided during image creation.|
| enasupport | Specifies whether enhanced networking with ENA is enabled.|
| hypervisor | The hypervisor type of the image.|
| rootdevicename | The device name of the root device volume (for example, `/dev/sda1` ). |
| rootdevicetype | The type of root device used by the AMI. |
| virtualizationtype | The type of virtualization of the AMI. |
| bootmode | The boot mode of the image. |
| region | The region of the image. |


[Link to API Documentation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Image.html) of EC2 Images

#### Relationships

- AWS EC2 Images (AMIs) are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EC2Image)
    ```

### EC2ReservedInstance

Representation of an AWS [EC2 Reserved Instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-reserved-instances.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the Reserved Instance.|
| availabilityzone | The Availability Zone in which the Reserved Instance can be used. |
| duration | The duration of the Reserved Instance, in seconds. |
| end | The time when the Reserved Instance expires. |
| start | The date and time the Reserved Instance started.|
| count | The number of reservations purchased.|
| type | The instance type on which the Reserved Instance can be used. |
| productdescription | The Reserved Instance product platform description. |
| state | The state of the Reserved Instance purchase.  |
| currencycode | The currency of the Reserved Instance. It's specified using ISO 4217 standard currency codes.|
| instancetenancy | The tenancy of the instance.|
| offeringclass | The offering class of the Reserved Instance.|
| offeringtype | The Reserved Instance offering type.|
| scope | The scope of the Reserved Instance.|
| fixedprice | The purchase price of the Reserved Instance. |
| region | The region of the reserved instance. |

#### Relationships

- AWS EC2 Reserved Instances are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EC2ReservedInstance)
    ```

### SecretsManagerSecret

Representation of an AWS [Secrets Manager Secret](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_SecretListEntry.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the secret. |
| created\_date | The date and time when a secret was created. |
| deleted\_date | The date and time the deletion of the secret occurred. Not present on active secrets. The secret can be recovered until the number of days in the recovery window has passed, as specified in the RecoveryWindowInDays parameter of the DeleteSecret operation. |
| description | The user-provided description of the secret. |
| kms\_key\_id | The ARN or alias of the AWS KMS customer master key (CMK) used to encrypt the SecretString and SecretBinary fields in each version of the secret. If you don't provide a key, then Secrets Manager defaults to encrypting the secret fields with the default KMS CMK, the key named awssecretsmanager, for this account. |
| last\_accessed\_date | The last date that this secret was accessed. This value is truncated to midnight of the date and therefore shows only the date, not the time. |
| last\_changed\_date | The last date and time that this secret was modified in any way. |
| last\_rotated\_date | The most recent date and time that the Secrets Manager rotation process was successfully completed. This value is null if the secret hasn't ever rotated. |
| name | The friendly name of the secret. You can use forward slashes in the name to represent a path hierarchy. For example, /prod/databases/dbserver1 could represent the secret for a server named dbserver1 in the folder databases in the folder prod. |
| owning\_service | Returns the name of the service that created the secret. |
| primary\_region | The Region where Secrets Manager originated the secret. |
| rotation\_enabled | Indicates whether automatic, scheduled rotation is enabled for this secret. |
| rotation\_lambda\_arn | The ARN of an AWS Lambda function invoked by Secrets Manager to rotate and expire the secret either automatically per the schedule or manually by a call to RotateSecret. |
| rotation\_rules\_automatically\_after\_days | Specifies the number of days between automatic scheduled rotations of the secret. |

#### Relationships

- AWS Secrets Manager Secrets are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SecretsManagerSecret)
    ```

### EBSVolume

Representation of an AWS [EBS Volume](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volumes.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the EBS Volume.|
| availabilityzone | The Availability Zone for the volume. |
| createtime | The time stamp when volume creation was initiated. |
| encrypted | Indicates whether the volume is encrypted. |
| size | The size of the volume, in GiBs.|
| state | The volume state.|
| outpostarn | The Amazon Resource Name (ARN) of the Outpost. |
| snapshotid | The snapshot ID. |
| iops | The number of I/O operations per second (IOPS).  |
| type | The volume type.|
| fastrestored | Indicates whether the volume was created using fast snapshot restore.|
| multiattachenabled |Indicates whether Amazon EBS Multi-Attach is enabled.|
| throughput | The throughput that the volume supports, in MiB/s.|
| kmskeyid | The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the volume.|
| deleteontermination | Indicates whether the volume is deleted on instance termination. |
| region | The region of the volume. |

#### Relationships

- AWS EBS Volumes are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EBSVolume)
    ```

- AWS EBS Snapshots are created using EBS Volumes
    ```
    (EBSSnapshot)-[CREATED_FROM]->(EBSVolume)
    ```

- AWS EBS Volumes are attached to an EC2 Instance
    ```
    (EBSVolume)-[ATTACHED_TO_EC2_INSTANCE]->(EC2Instance)
    ```

- `AWSTag`
    ```
    (EBSVolume)-[TAGGED]->(AWSTag)
    ```

### EBSSnapshot

Representation of an AWS [EBS Snapshot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the EBS Snapshot.|
| description | The description of the snapshot. |
| progress | The progress of the snapshot, as a percentage. |
| encrypted |Indicates whether the snapshot is encrypted. |
| starttime | The time stamp when the snapshot was initiated.|
| state | The snapshot state.|
| statemessage | Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the error occurred. This parameter is only returned by DescribeSnapshots .|
| volumeid | The volume ID. |
| volumesize | The size of the volume, in GiB.|
| outpostarn | The ARN of the AWS Outpost on which the snapshot is stored. |
| dataencryptionkeyid | The data encryption key identifier for the snapshot.|
| kmskeyid | The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the parent volume.|
| region | The region of the snapshot. |

#### Relationships

- AWS EBS Snapshots are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EBSSnapshot)
    ```

- AWS EBS Snapshots are created using EBS Volumes
    ```
    (EBSSnapshot)-[CREATED_FROM]->(EBSVolume)
    ```

### SQSQueue

Representation of an AWS [SQS Queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_GetQueueAttributes.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the sqs queue. |
| created\_timestamp | The time when the queue was created in seconds |
| delay\_seconds | The default delay on the queue in seconds. |
| last\_modified\_timestamp | The time when the queue was last changed in seconds. |
| maximum\_message\_size | The limit of how many bytes a message can contain before Amazon SQS rejects it. |
| message\_retention\_period | he length of time, in seconds, for which Amazon SQS retains a message. |
| policy | The IAM policy of the queue. |
| arn | The arn of the sqs queue. |
| receive\_message\_wait\_time\_seconds | The length of time, in seconds, for which the ReceiveMessage action waits for a message to arrive. |
| redrive\_policy\_dead\_letter\_target\_arn | The Amazon Resource Name (ARN) of the dead-letter queue to which Amazon SQS moves messages after the value of maxReceiveCount is exceeded. |
| redrive\_policy\_max\_receive\_count | The number of times a message is delivered to the source queue before being moved to the dead-letter queue. When the ReceiveCount for a message exceeds the maxReceiveCount for a queue, Amazon SQS moves the message to the dead-letter-queue. |
| visibility\_timeout | The visibility timeout for the queue. |
| kms\_master\_key\_id | The ID of an AWS managed customer master key (CMK) for Amazon SQS or a custom CMK. |
| kms\_data\_key\_reuse\_period\_seconds | The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again. |
| fifo\_queue | Whether or not the queue is FIFO. |
| content\_based\_deduplication | Whether or not content-based deduplication is enabled for the queue. |
| deduplication\_scope | Specifies whether message deduplication occurs at the message group or queue level. |
| fifo\_throughput\_limit | Specifies whether the FIFO queue throughput quota applies to the entire queue or per message group. |

#### Relationships

- AWS SQS Queues are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SQSQueue)
    ```

- AWS SQS Queues can have other SQS Queues configured as dead letter queues
    ```
    (SQSQueue)-[HAS_DEADLETTER_QUEUE]->(SQSQueue)
    ```

### SecurityHub

Representation of the configuration of AWS [Security Hub](https://docs.aws.amazon.com/securityhub/1.0/APIReference/API_DescribeHub.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the hub resource. |
| subscribed\_at | The date and time when Security Hub was enabled in the account. |
| auto\_enable\_controls | Whether to automatically enable new controls when they are added to standards that are enabled. |

#### Relationships

- AWS Security Hub nodes are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SecurityHub)
    ```

### AWSConfigurationRecorder

Representation of an AWS [Config Configuration Recorder](https://docs.aws.amazon.com/config/latest/APIReference/API_ConfigurationRecorder.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | A combination of name:account\_id:region |
| name | The name of the recorder. |
| role\_arn | Amazon Resource Name (ARN) of the IAM role used to describe the AWS resources associated with the account. |
| recording\_group\_all\_supported | Specifies whether AWS Config records configuration changes for every supported type of regional resource. |
| recording\_group\_include\_global\_resource\_types | Specifies whether AWS Config includes all supported types of global resources (for example, IAM resources) with the resources that it records. |
| recording\_group\_resource\_types | A comma-separated list that specifies the types of AWS resources for which AWS Config records configuration changes (for example, AWS::EC2::Instance or AWS::CloudTrail::Trail). |
| region | The region of the configuration recorder. |

#### Relationships

- AWS Configuration Recorders are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSConfigurationRecorder)
    ```

### AWSConfigDeliveryChannel

Representation of an AWS [Config Delivery Channel](https://docs.aws.amazon.com/config/latest/APIReference/API_DeliveryChannel.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | A combination of name:account\_id:region |
| name | The name of the delivery channel. |
| s3\_bucket\_name | The name of the Amazon S3 bucket to which AWS Config delivers configuration snapshots and configuration history files. |
| s3\_key\_prefix | The prefix for the specified Amazon S3 bucket. |
| s3\_kms\_key\_arn | The Amazon Resource Name (ARN) of the AWS Key Management Service (KMS) customer managed key (CMK) used to encrypt objects delivered by AWS Config. Must belong to the same Region as the destination S3 bucket. |
| sns\_topic\_arn | The Amazon Resource Name (ARN) of the Amazon SNS topic to which AWS Config sends notifications about configuration changes. |
| config\_snapshot\_delivery\_properties\_delivery\_frequency | The frequency with which AWS Config delivers configuration snapshots. |
| region | The region of the delivery channel. |

#### Relationships

- AWS Config Delivery Channels are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSConfigDeliveryChannel)
    ```

### AWSConfigRule

Representation of an AWS [Config Rule](https://docs.aws.amazon.com/config/latest/APIReference/API_DeliveryChannel.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the config rule. |
| name | The name of the delivery channel. |
| description | The description that you provide for the AWS Config rule. |
| arn | The ARN of the config rule. |
| rule\_id | The ID of the AWS Config rule. |
| scope\_compliance\_resource\_types | The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId. |
| scope\_tag\_key | The tag key that is applied to only those AWS resources that you want to trigger an evaluation for the rule. |
| scope\_tag\_value | The tag value applied to only those AWS resources that you want to trigger an evaluation for the rule. If you specify a value for TagValue, you must also specify a value for TagKey. |
| scope\_tag\_compliance\_resource\_id | The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId. |
| source\_owner | Indicates whether AWS or the customer owns and manages the AWS Config rule. |
| source\_identifier | For AWS Config managed rules, a predefined identifier from a list. For example, IAM\_PASSWORD\_POLICY is a managed rule. |
| source\_details | Provides the source and type of the event that causes AWS Config to evaluate your AWS resources. |
| input\_parameters | A string, in JSON format, that is passed to the AWS Config rule Lambda function. |
| maximum\_execution\_frequency | The maximum frequency with which AWS Config runs evaluations for a rule. |
| created\_by | Service principal name of the service that created the rule. |
| region | The region of the delivery channel. |

#### Relationships

- AWS Config Rules are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSConfigRule)
    ```

### LaunchConfiguration

Representation of an AWS [Launch Configuration](https://docs.aws.amazon.com/autoscaling/ec2/APIReference/API_LaunchConfiguration.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the launch configuration. |
| name | The name of the launch configuration. |
| arn | The ARN of the launch configuration. |
| created\_time| The creation date and time for the launch configuration. |
| image\_id | The ID of the Amazon Machine Image (AMI) to use to launch your EC2 instances. |
| key\_name | The name of the key pair. |
| security\_groups | A list that contains the security groups to assign to the instances in the Auto Scaling group. |
| instance\_type | The instance type for the instances. |
| kernel\_id | The ID of the kernel associated with the AMI. |
| ramdisk\_id | The ID of the RAM disk associated with the AMI. |
| instance\_monitoring\_enabled | If true, detailed monitoring is enabled. Otherwise, basic monitoring is enabled. |
| spot\_price | The maximum hourly price to be paid for any Spot Instance launched to fulfill the request. |
| iam\_instance\_profile | The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instance. |
| ebs\_optimized | Specifies whether the launch configuration is optimized for EBS I/O (true) or not (false). |
| associate\_public\_ip\_address | For Auto Scaling groups that are running in a VPC, specifies whether to assign a public IP address to the group's instances. |
| placement\_tenancy | The tenancy of the instance, either default or dedicated. An instance with dedicated tenancy runs on isolated, single-tenant hardware and can only be launched into a VPC. |
| region | The region of the launch configuration. |

#### Relationships

- Launch Configurations are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(LaunchConfiguration)
    ```

### LaunchTemplate

Representation of an AWS [Launch Template](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_LaunchTemplate.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the launch template. |
| name | The name of the launch template. |
| create\_time | The time launch template was created. |
| created\_by | The principal that created the launch template. |
| default\_version\_number | The version number of the default version of the launch template. |
| latest\_version\_number | The version number of the latest version of the launch template. |
| region | The region of the launch template. |

#### Relationships

- Launch Templates are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(LaunchTemplate)
    ```

- Launch templates have Launch Template Versions
    ```
    (LaunchTemplate)-[VERSION]->(LaunchTemplateVersion)
    ```

### LaunchTemplateVersion

Representation of an AWS [Launch Template Version](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_LaunchTemplateVersion.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the launch template version (ID-version). |
| name | The name of the launch template. |
| create\_time | The time the version was created. |
| created\_by | The principal that created the version. |
| default\_version | Indicates whether the version is the default version. |
| version\_number | The version number. |
| version\_description | The description of the version. |
| kernel\_id | The ID of the kernel, if applicable. |
| ebs\_optimized | Indicates whether the instance is optimized for Amazon EBS I/O. |
| iam\_instance\_profile\_arn | The Amazon Resource Name (ARN) of the instance profile. |
| iam\_instance\_profile\_name | The name of the instance profile. |
| image\_id | The ID of the AMI that was used to launch the instance. |
| instance\_type | The instance type. |
| key\_name | The name of the key pair. |
| monitoring\_enabled | Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled. |
| ramdisk\_id | The ID of the RAM disk, if applicable. |
| disable\_api\_termination | If set to true, indicates that the instance cannot be terminated using the Amazon EC2 console, command line tool, or API. |
| instance\_initiated\_shutdown\_behavior | Indicates whether an instance stops or terminates when you initiate shutdown from the instance (using the operating system command for system shutdown). |
| security\_group\_ids | The security group IDs. |
| security\_groups | The security group names. |
| region | The region of the launch template. |

#### Relationships

- Launch Template Versions are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(LaunchTemplateVersion)
    ```

- Launch templates have Launch Template Versions
    ```
    (LaunchTemplate)-[VERSION]->(LaunchTemplateVersion)
    ```

### ElasticIPAddress

Representation of an AWS EC2 [Elastic IP address](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Address.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The Elastic IP address |
| instance\_id | The ID of the instance that the address is associated with (if any). |
| public\_ip | The Elastic IP address. |
| allocation\_id | The ID representing the allocation of the address for use with EC2-VPC. |
| association\_id | The ID representing the association of the address with an instance in a VPC. |
| domain | Indicates whether this Elastic IP address is for use with instances in EC2-Classic (standard) or instances in a VPC (vpc). |
| network\_interface\_id | The ID of the network interface. |
| private\_ip\_address | The private IP address associated with the Elastic IP address. |
| public\_ipv4\_pool | The ID of an address pool. |
| network\_border\_group | The name of the unique set of Availability Zones, Local Zones, or Wavelength Zones from which AWS advertises IP addresses. |
| customer\_owned\_ip | The customer-owned IP address. |
| customer\_owned\_ipv4\_pool | The ID of the customer-owned address pool. |
| carrier\_ip | The carrier IP address associated. This option is only available for network interfaces which reside in a subnet in a Wavelength Zone (for example an EC2 instance). |
| region | The region of the IP. |

#### Relationships

- Elastic IPs are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(ElasticIPAddress)
    ```

- Elastic IPs can be attached to EC2 instances
    ```
    (EC2Instance)-[ELASTIC_IP_ADDRESS]->(ElasticIPAddress)
    ```

- Elastic IPs can be attached to NetworkInterfaces
    ```
    (NetworkInterface)-[ELASTIC_IP_ADDRESS]->(ElasticIPAddress)
    ```

### ECSCluster

Representation of an AWS ECS [Cluster](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Cluster.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the cluster |
| region | The region of the cluster. |
| name | A user-generated string that you use to identify your cluster. |
| arn | The ARN of the cluster |
| ecc\_kms\_key\_id | An AWS Key Management Service key ID to encrypt the data between the local client and the container. |
| ecc\_logging | The log setting to use for redirecting logs for your execute command results. |
| ecc\_log\_configuration\_cloud\_watch\_log\_group\_name | The name of the CloudWatch log group to send logs to. |
| ecc\_log\_configuration\_cloud\_watch\_encryption\_enabled | Determines whether to enable encryption on the CloudWatch logs. |
| ecc\_log\_configuration\_s3\_bucket\_name | The name of the S3 bucket to send logs to. |
| ecc\_log\_configuration\_s3\_encryption\_enabled | Determines whether to use encryption on the S3 logs. |
| ecc\_log\_configuration\_s3\_key\_prefix | An optional folder in the S3 bucket to place logs in. |
| status | The status of the cluster |
| settings\_container\_insights | If enabled is specified, CloudWatch Container Insights will be enabled for the cluster, otherwise it will be disabled unless the containerInsights account setting is enabled. |
| capacity\_providers | The capacity providers associated with the cluster. |
| attachments\_status | The status of the capacity providers associated with the cluster. |

#### Relationships

- ECSClusters are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(ECSCluster)
    ```

### ECSContainerInstance

Representation of an AWS ECS [Container Instance](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerInstance.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the container instance |
| region | The region of the container instance. |
| ec2\_instance\_id | The ID of the container instance. For Amazon EC2 instances, this value is the Amazon EC2 instance ID. For external instances, this value is the AWS Systems Manager managed instance ID. |
| arn | The ARN of the container instance |
| capacity\_provider\_name | The capacity provider that's associated with the container instance. |
| version | The version counter for the container instance. |
| version\_info\_agent\_version | The version number of the Amazon ECS container agent. |
| version\_info\_agent\_hash | The Git commit hash for the Amazon ECS container agent build on the amazon-ecs-agent  GitHub repository. |
| version\_info\_agent\_docker\_version | The Docker version that's running on the container instance. |
| status | The status of the container instance. |
| status\_reason | The reason that the container instance reached its current status. |
| agent\_connected | This parameter returns true if the agent is connected to Amazon ECS. Registered instances with an agent that may be unhealthy or stopped return false. |
| agent\_update\_status | The status of the most recent agent update. If an update wasn't ever requested, this value is NULL. |
| registered\_at | The Unix timestamp for the time when the container instance was registered. |

#### Relationships

- An ECSCluster has ECSContainerInstances
    ```
    (ECSCluster)-[HAS_CONTAINER_INSTANCE]->(ECSContainerInstance)
    ```

- ECSContainerInstances have ECSTasks
    ```
    (ECSContainerInstance)-[HAS_TASK]->(ECSTask)
    ```

### ECSService

Representation of an AWS ECS [Service](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Service.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the service |
| region | The region of the service. |
| name | The name of your service. |
| arn | The ARN of the service |
| cluster_arn | The Amazon Resource Name (ARN) of the cluster that hosts the service. |
| status | The status of the service. |
| desired\_count | The desired number of instantiations of the task definition to keep running on the service. |
| running\_count | The number of tasks in the cluster that are in the RUNNING state. |
| pending\_count | The number of tasks in the cluster that are in the PENDING state. |
| launch\_type | The launch type the service is using. |
| platform\_version | The platform version to run your service on. A platform version is only specified for tasks that are hosted on AWS Fargate. |
| platform\_family | The operating system that your tasks in the service run on. A platform family is specified only for tasks using the Fargate launch type. |
| task\_definition | The task definition to use for tasks in the service. |
| deployment\_config\_circuit\_breaker\_enable | Determines whether to enable the deployment circuit breaker logic for the service. |
| deployment\_config\_circuit\_breaker\_rollback | Determines whether to enable Amazon ECS to roll back the service if a service deployment fails. |
| deployment\_config\_maximum\_percent | If a service is using the rolling update (ECS) deployment type, the maximum percent parameter represents an upper limit on the number of tasks in a service that are allowed in the RUNNING or PENDING state during a deployment, as a percentage of the desired number of tasks (rounded down to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type. |
| deployment\_config\_minimum\_healthy\_percent | If a service is using the rolling update (ECS) deployment type, the minimum healthy percent represents a lower limit on the number of tasks in a service that must remain in the RUNNING state during a deployment, as a percentage of the desired number of tasks (rounded up to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type. |
| role\_arn | The ARN of the IAM role that's associated with the service. |
| created\_at | The Unix timestamp for the time when the service was created. |
| health\_check\_grace\_period\_seconds | The period of time, in seconds, that the Amazon ECS service scheduler ignores unhealthy Elastic Load Balancing target health checks after a task has first started. |
| created\_by | The principal that created the service. |
| enable\_ecs\_managed\_tags | Determines whether to enable Amazon ECS managed tags for the tasks in the service. |
| propagate\_tags | Determines whether to propagate the tags from the task definition or the service to the task. |
| enable\_execute\_command | Determines whether the execute command functionality is enabled for the service. |

#### Relationships

- An ECSCluster has ECSService
    ```
    (ECSCluster)-[HAS_SERVICE]->(ECSService)
    ```

- An ECSCluster has ECSContainerInstances
    ```
    (ECSCluster)-[HAS_CONTAINER_INSTANCE]->(ECSContainerInstance)
    ```

### ECSTaskDefinition

Representation of an AWS ECS [Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_TaskDefinition.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the task definition |
| region | The region of the task definition. |
| family | The name of a family that this task definition is registered to. |
| task\_role\_arn | The short name or full Amazon Resource Name (ARN) of the AWS Identity and Access Management role that grants containers in the task permission to call AWS APIs on your behalf. |
| execution\_role\_arn | The Amazon Resource Name (ARN) of the task execution role that grants the Amazon ECS container agent permission to make AWS API calls on your behalf. |
| network\_mode | The Docker networking mode to use for the containers in the task. The valid values are none, bridge, awsvpc, and host. If no network mode is specified, the default is bridge. |
| revision | The revision of the task in a particular family. |
| status | The status of the task definition. |
| compatibilities | The task launch types the task definition validated against during task definition registration. |
| runtime\_platform\_cpu\_architecture | The CPU architecture. |
| runtime\_platform\_operating\_system\_family | The operating system. |
| requires\_compatibilities | The task launch types the task definition was validated against. |
| cpu | The number of cpu units used by the task. |
| memory | The amount (in MiB) of memory used by the task. |
| pid\_mode | The process namespace to use for the containers in the task. |
| ipc\_mode | The IPC resource namespace to use for the containers in the task. |
| proxy\_configuration\_type | The proxy type. |
| proxy\_configuration\_container\_name | The name of the container that will serve as the App Mesh proxy. |
| registered\_at | The Unix timestamp for the time when the task definition was registered. |
| deregistered\_at | The Unix timestamp for the time when the task definition was deregistered. |
| registered\_by | The principal that registered the task definition. |
| ephemeral\_storage\_size\_in\_gib | The total amount, in GiB, of ephemeral storage to set for the task. |

#### Relationships

- ECSTaskDefinition are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(ECSTaskDefinition)
    ```

- An ECSTask has an ECSTaskDefinition.
    ```
    (ECSTask)-[HAS_TASK_DEFINITION]->(ECSTaskDefinition)
    ```

### ECSContainerDefinition

Representation of an AWS ECS [Container Definition](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerDefinition.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the task definition, plus the container definition name |
| region | The region of the container definition. |
| name | The name of a container. |
| image | The image used to start a container. This string is passed directly to the Docker daemon. |
| cpu | The number of cpu units reserved for the container. |
| memory | The amount (in MiB) of memory to present to the container. |
| memory\_reservation | The soft limit (in MiB) of memory to reserve for the container. |
| links | The links parameter allows containers to communicate with each other without the need for port mappings. |
| essential | If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped. |
| entry\_point | The entry point that's passed to the container. |
| command | The command that's passed to the container. |
| start\_timeout | Time duration (in seconds) to wait before giving up on resolving dependencies for a container. |
| stop\_timeout | Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own. |
| hostname | The hostname to use for your container. |
| user | The user to use inside the container. |
| working\_directory | The working directory to run commands inside the container in. |
| disable\_networking | When this parameter is true, networking is disabled within the container. |
| privileged | When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user). |
| readonly\_root\_filesystem | When this parameter is true, the container is given read-only access to its root file system. |
| dns\_servers | A list of DNS servers that are presented to the container. |
| dns\_search\_domains | A list of DNS search domains that are presented to the container. |
| docker\_security\_options | A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. This field isn't valid for containers in tasks using the Fargate launch type. |
| interactive | When this parameter is true, you can deploy containerized applications that require stdin or a tty to be allocated. |
| pseudo\_terminal | When this parameter is true, a TTY is allocated. |

#### Relationships

- ECSTaskDefinitions have ECSContainerDefinitions
    ```
    (ECSTaskDefinition)-[HAS_CONTAINER_DEFINITION]->(ECSContainerDefinition)
    ```

### ECSTask

Representation of an AWS ECS [Task](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Task.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the task |
| region | The region of the task. |
| arn | The arn of the task. |
| availability\_zone | The Availability Zone for the task. |
| capacity\_provider\_name | The capacity provider that's associated with the task. |
| cluster\_arn | The ARN of the cluster that hosts the task. |
| connectivity | The connectivity status of a task. |
| connectivity\_at | The Unix timestamp for the time when the task last went into CONNECTED status. |
| container\_instance\_arn | The ARN of the container instances that host the task. |
| cpu | The number of CPU units used by the task as expressed in a task definition. |
| created\_at | The Unix timestamp for the time when the task was created. More specifically, it's for the time when the task entered the PENDING state. |
| desired\_status | The desired status of the task. |
| enable\_execute\_command | Determines whether execute command functionality is enabled for this task. |
| execution\_stopped\_at | The Unix timestamp for the time when the task execution stopped. |
| group | The name of the task group that's associated with the task. |
| health\_status | The health status for the task. |
| last\_status | The last known status for the task. |
| launch\_type | The infrastructure where your task runs on. |
| memory | The amount of memory (in MiB) that the task uses as expressed in a task definition. |
| platform\_version | The platform version where your task runs on. |
| platform\_family | The operating system that your tasks are running on. |
| pull\_started\_at | The Unix timestamp for the time when the container image pull began. |
| pull\_stopped\_at | The Unix timestamp for the time when the container image pull completed. |
| started\_at | The Unix timestamp for the time when the task started. More specifically, it's for the time when the task transitioned from the PENDING state to the RUNNING state. |
| started\_by | The tag specified when a task is started. If an Amazon ECS service started the task, the startedBy parameter contains the deployment ID of that service. |
| stop\_code | The stop code indicating why a task was stopped. |
| stopped\_at | The Unix timestamp for the time when the task was stopped. More specifically, it's for the time when the task transitioned from the RUNNING state to the STOPPED state. |
| stopped\_reason | The reason that the task was stopped. |
| stopping\_at | The Unix timestamp for the time when the task stops. More specifically, it's for the time when the task transitions from the RUNNING state to STOPPED. |
| task\_definition\_arn | The ARN of the task definition that creates the task. |
| version | The version counter for the task. |
| ephemeral\_storage\_size\_in\_gib | The total amount, in GiB, of ephemeral storage to set for the task. |

#### Relationships

- ECSClusters have ECSTasks
    ```
    (ECSCluster)-[HAS_TASK]->(ECSTask)
    ```

- ECSContainerInstances have ECSTasks
    ```
    (ECSContainerInstance)-[HAS_TASK]->(ECSTask)
    ```

- ECSTasks have ECSTaskDefinitions
    ```
    (ECSTask)-[HAS_TASK_DEFINITION]->(ECSTaskDefinition)
    ```

### ECSContainer

Representation of an AWS ECS [Container](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Container.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the container |
| region | The region of the container. |
| arn | The arn of the container. |
| task\_arn | The ARN of the task. |
| name | The name of the container. |
| image | The image used for the container. |
| image\_digest | The container image manifest digest. |
| runtime\_id | The ID of the Docker container. |
| last\_status | The last known status of the container. |
| exit\_code | The exit code returned from the container. |
| reason | A short (255 max characters) human-readable string to provide additional details about a running or stopped container. |
| health\_status | The health status of the container. |
| cpu | The number of CPU units set for the container. |
| memory | The hard limit (in MiB) of memory set for the container. |
| memory\_reservation | The soft limit (in MiB) of memory set for the container. |
| gpu\_ids | The IDs of each GPU assigned to the container. |

#### Relationships

- ECSTasks have ECSContainers
    ```
    (ECSTask)-[HAS_CONTAINER]->(ECSContainer)
    ```
### SNSTopic
Representation of an AWS [SNS Topic](https://docs.aws.amazon.com/sns/latest/api/API_Topic.html)
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the SNS topic |
| **arn** | The Amazon Resource Name (ARN) of the topic |
| name | The name of the topic |
| displayname | The display name of the topic |
| owner | The AWS account ID of the topic's owner |
| subscriptionspending | The number of subscriptions pending confirmation |
| subscriptionsconfirmed | The number of confirmed subscriptions |
| subscriptionsdeleted | The number of deleted subscriptions |
| deliverypolicy | The JSON serialization of the topic's delivery policy |
| effectivedeliverypolicy | The JSON serialization of the effective delivery policy |
| kmsmasterkeyid | The ID of an AWS managed customer master key (CMK) for Amazon SNS or a custom CMK |
| region | The AWS region where the topic is located |
#### Relationships
- SNS Topics are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SNSTopic)
    ```
### S3AccountPublicAccessBlock
Representation of an AWS [S3 Account Public Access Block](https://docs.aws.amazon.com/AmazonS3/latest/dev/access-control-block-public-access.html) configuration, which provides account-level settings to block public access to S3 resources.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier in the format: `{account_id}:{region}` |
| account_id | The AWS account ID |
| region | The AWS region |
| block_public_acls | Whether Amazon S3 blocks public access control lists (ACLs) for this bucket and objects |
| ignore_public_acls | Whether Amazon S3 ignores public ACLs for this bucket and objects |
| block_public_policy | Whether Amazon S3 blocks public bucket policies for this bucket |
| restrict_public_buckets | Whether Amazon S3 restricts public policies for this bucket |

#### Relationships
- S3AccountPublicAccessBlock is a resource of an AWS Account.
    ```
    (AWSAccount)-[:RESOURCE]->(S3AccountPublicAccessBlock)
    ```

### SSMInstanceInformation

Representation of an AWS SSM [InstanceInformation](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_InstanceInformation.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the instance information |
| region | The region of the instance information. |
| instance\_id | The managed node ID. |
| ping\_status | Connection status of SSM Agent. |
| last\_ping\_date\_time | The date and time when the agent last pinged the Systems Manager service. |
| agent\_version | The version of SSM Agent running on your Linux managed node. |
| is\_latest\_version | Indicates whether the latest version of SSM Agent is running on your Linux managed node. This field doesn't indicate whether or not the latest version is installed on Windows managed nodes, because some older versions of Windows Server use the EC2Config service to process Systems Manager requests. |
| platform\_type | The operating system platform type. |
| platform\_name | The name of the operating system platform running on your managed node. |
| platform\_version | The version of the OS platform running on your managed node. |
| activation\_id | The activation ID created by AWS Systems Manager when the server or virtual machine (VM) was registered. |
| iam\_role | The AWS Identity and Access Management (IAM) role assigned to the on-premises Systems Manager managed node. This call doesn't return the IAM role for Amazon Elastic Compute Cloud (Amazon EC2) instances. |
| registration\_date | The date the server or VM was registered with AWS as a managed node. |
| resource\_type | The type of instance. Instances are either EC2 instances or managed instances. |
| name | The name assigned to an on-premises server, edge device, or virtual machine (VM) when it is activated as a Systems Manager managed node. The name is specified as the DefaultInstanceName property using the CreateActivation command. |
| ip\_address | The IP address of the managed node. |
| computer\_name | The fully qualified host name of the managed node. |
| association\_status | The status of the association. |
| last\_association\_execution\_date | The date the association was last run. |
| last\_successful\_association\_execution\_date | The last date the association was successfully run. |
| source\_id | The ID of the source resource. For AWS IoT Greengrass devices, SourceId is the Thing name. |
| source\_type | The type of the source resource. For AWS IoT Greengrass devices, SourceType is AWS::IoT::Thing. |

#### Relationships

- SSMInstanceInformation is a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SSMInstanceInformation)
    ```

- SSMInstanceInformation is a resource of an EC2Instance
    ```
    (EC2Instance)-[HAS_INFORMATION]->(SSMInstanceInformation)
    ```

### SSMInstancePatch

Representation of an AWS SSM [PatchComplianceData](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_PatchComplianceData.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the instance patch |
| region | The region of the instance patch. |
| instance\_id | The managed node ID. |
| title | The title of the patch. |
| kb\_id | The operating system-specific ID of the patch. |
| classification | The classification of the patch, such as SecurityUpdates, Updates, and CriticalUpdates. |
| severity | The severity of the patch such as Critical, Important, and Moderate. |
| state | The state of the patch on the managed node, such as INSTALLED or FAILED. |
| installed\_time | The date/time the patch was installed on the managed node. Not all operating systems provide this level of information. |
| cve\_ids | The IDs of one or more Common Vulnerabilities and Exposure (CVE) issues that are resolved by the patch. |

#### Relationships

- SSMInstancePatch is a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SSMInstancePatch)
    ```

- EC2Instances have SSMInstancePatches
    ```
    (EC2Instance)-[HAS_INFORMATION]->(SSMInstancePatch)
    ```

### SSMParameter

Representation of an AWS Systems Manager Parameter as returned by the [`describe_parameters` API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/describe_parameters.html).

| Field | Description |
|-------|-------------|
| **firstseen**| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the parameter |
| region | The region of the parameter. |
| arn | The Amazon Resource Name (ARN) of the parameter. |
| name | The parameter name. |
| description | Description of the parameter actions. |
| type | The type of parameter. Valid parameter types include String, StringList, and SecureString. |
| keyid | The alias or ARN of the Key Management Service (KMS) key used to encrypt the parameter. Applies to SecureString parameters only. |
| version | The parameter version. |
| lastmodifieddate | Date the parameter was last changed or updated (stored as epoch time). |
| tier | The parameter tier. |
| lastmodifieduser | Amazon Resource Name (ARN) of the AWS user who last changed the parameter. |
| datatype | The data type of the parameter, such as text or aws:ec2:image. |
| allowedpattern | A regular expression that defines the constraints on the parameter value. |
| policies_json | A JSON string representation of the list of policies associated with the parameter. |

#### Relationships

- SSMParameter is a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SSMParameter)
    ```

- SecureString SSMParameters may be encrypted by an AWS KMS Key.
    ```
    (SSMParameter)-[ENCRYPTED_BY]->(KMSKey)
    ```

### AWSIdentityCenter

Representation of an AWS Identity Center.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the Identity Center instance |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| identity_store_id | The identity store ID of the Identity Center instance |
| instance_status | The status of the Identity Center instance |
| created_date | The date the Identity Center instance was created |
| last_modified_date | The date the Identity Center instance was last modified |

#### Relationships
- AWSIdentityCenter is part of an AWSAccount.
    ```
    (AWSAccount)-[RESOURCE]->(AWSIdentityCenter)
    ```

- AWSIdentityCenter has permission sets.
    ```
    (AWSIdentityCenter)-[HAS_PERMISSION_SET]->(AWSPermissionSet)
    ```

### AWSSSOUser

Representation of an AWS SSO User.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the SSO user |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| user_name | The username of the SSO user |
| external_id | The external ID of the SSO user |
| identity_store_id | The identity store ID of the SSO user |

#### Relationships
- AWSSSOUser is part of an AWSAccount.
    ```
    (AWSAccount)-[RESOURCE]->(AWSSSOUser)
    ```

- AWSSSOUser can have roles assigned.
    ```
    (AWSSSOUser)<-[ALLOWED_BY]-(AWSRole)
    ```

- UserAccount can be assumed by AWSSSOUser.
    ```
    (UserAccount)-[CAN_ASSUME_IDENTITY]->(AWSSSOUser)
    ```

### AWSPermissionSet

Representation of an AWS Identity Center Permission Set.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the Permission Set |

| name | The name of the Permission Set |
| arn | The Amazon Resource Name (ARN) of the Permission Set |
| description | The description of the Permission Set |
| session_duration | The session duration of the Permission Set |
| instance_arn | The ARN of the Identity Center instance the Permission Set belongs to |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- AWSPermissionSet is part of an AWSIdentityCenter.
    ```
    (AWSIdentityCenter)<-[HAS_PERMISSION_SET]-(AWSPermissionSet)
    ```

- AWSPermissionSet can be assigned to roles.
    ```
    (AWSPermissionSet)-[ASSIGNED_TO_ROLE]->(AWSRole)
    ```

### EC2RouteTable

Representation of an AWS [EC2 Route Table](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RouteTable.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The ID of the route table|
|route_table_id| The ID of the route table (same as id)|
|main|If True, this route table is the main route table for VPC, meaning that any subnets in this VPC not explicitly associated with another route table will use this route table.|
|vpc_id| The ID of the VPC the route table is associated with|
|owner_id| The AWS account ID of the route table owner|
|region| The AWS region the route table is in|

#### Relationships
- EC2RouteTable belongs to an AWSAccount.
    ```
    (AWSAccount)-[RESOURCE]->(EC2RouteTable)
    ```

- EC2RouteTable is associated with a VPC.
    ```
    (EC2RouteTable)-[MEMBER_OF_AWS_VPC]->(AWSVpc)
    ```

- EC2RouteTable contains EC2Routes.
    ```
    (EC2RouteTable)-[ROUTE]->(EC2Route)
    ```

- EC2RouteTable has EC2RouteTableAssociations.
    ```
    (EC2RouteTable)-[ASSOCIATION]->(EC2RouteTableAssociation)
    ```

### EC2RouteTableAssociation

Representation of an AWS [EC2 Route Table Association](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RouteTableAssociation.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The ID of the route table association|
|target||
|route_table_association_id| The ID of the route table association (same as id)|
|route_table_id| The ID of the route table|
|subnet_id| The ID of the subnet (if associated with a subnet)|
|gateway_id| The ID of the gateway (if associated with a gateway)|
|main| Whether this is the main route table association|
|association_state| The state of the association|
|association_state_message| The message describing the state of the association|
|region| The AWS region the association is in|

#### Relationships
- EC2RouteTableAssociation belongs to an AWSAccount.
    ```
    (AWSAccount)-[RESOURCE]->(EC2RouteTableAssociation)
    ```

- EC2RouteTableAssociation is associated with a subnet.
    ```
    (EC2RouteTableAssociation)-[ASSOCIATED_SUBNET]->(EC2Subnet)
    ```

- EC2RouteTableAssociation is associated with an internet gateway. In this configuration, AWS uses this given route table to decide how to route packets that arrive through the given IGW.
    ```
    (EC2RouteTableAssociation)-[ASSOCIATED_IGW_FOR_INGRESS]->(AWSInternetGateway)
    ```

### EC2Route

Representation of an AWS [EC2 Route](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Route.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The ID of the route, formatted as `route_table_id|destination_cidr|target_components` where target components are prefixed with their type (e.g., gw-, nat-, pcx-) and joined with underscores.|
|route_id| The ID of the route (same as id)|
|target|The ID of the route association's target -- either 'Main', or a subnet ID or a gateway ID. This is an invented field that we created to have an ID because the underlying EC2 route association is a "union" data structure of many different possible targets.|
|destination_cidr_block| The IPv4 CIDR block used for the destination match|
|destination_ipv6_cidr_block| The IPv6 CIDR block used for the destination match|
|destination_prefix_list_id| The ID of the prefix list used for the destination match|
|carrier_gateway_id| The ID of the carrier gateway|
|core_network_arn| The Amazon Resource Name (ARN) of the core network|
|egress_only_internet_gateway_id| The ID of the egress-only internet gateway|
|gateway_id| The ID of the gateway|
|instance_id| The ID of the instance|
|instance_owner_id| The owner ID of the instance|
|local_gateway_id| The ID of the local gateway|
|nat_gateway_id| The ID of the NAT gateway|
|network_interface_id| The ID of the network interface|
|origin| How the route was created|
|state| The state of the route|
|transit_gateway_id| The ID of the transit gateway|
|vpc_peering_connection_id| The ID of the VPC peering connection|
|region| The AWS region the route is in|

#### Relationships
- EC2Route belongs to an AWSAccount.
    ```
    (AWSAccount)-[RESOURCE]->(EC2Route)
    ```

- EC2Route is contained in an EC2RouteTable.
    ```
    (EC2RouteTable)-[ROUTE]->(EC2Route)
    ```

- EC2Route routes to an AWSInternetGateway. In most cases this tells AWS "to reach the internet, use this IGW".
    ```
    (EC2Route)-[ROUTES_TO_GATEWAY]->(AWSInternetGateway)
    ```

### SecretsManagerSecretVersion

Representation of an AWS [Secrets Manager Secret Version](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_SecretVersionListEntry.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the secret version. |
| arn | The ARN of the secret version. |
| secret_id | The ARN of the secret that this version belongs to. |
| version_id | The unique identifier of this version of the secret. |
| version_stages | A list of staging labels that are currently attached to this version of the secret. |
| created_date | The date and time that this version of the secret was created. |
| region | The AWS region where the secret version exists. |

#### Relationships

- AWS Secrets Manager Secret Versions are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SecretsManagerSecretVersion)
    ```
- Secret Versions belong to a Secret.
    ```
    (SecretsManagerSecretVersion)-[VERSION_OF]->(SecretsManagerSecret)
    ```
- If the secret version is encrypted with a KMS key, it has a relationship to that key.
    ```
    (SecretsManagerSecretVersion)-[ENCRYPTED_BY]->(AWSKMSKey)
    ```
