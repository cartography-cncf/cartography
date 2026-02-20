## AWS Schema


### AWSAccount

Representation of an AWS Account.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).

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
                                :AWSLambdaEventSourceMapping,
                                :AWSLambdaFunctionAlias,
                                :AWSLambdaLayer,
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
                                :GuardDutyDetector,
                                :GuardDutyFinding,
                                :KMSAlias,
                                :LaunchConfiguration,
                                :LaunchTemplate,
                                :LaunchTemplateVersion,
                                :LoadBalancer,
                                :RDSCluster,
                                :RDSInstance,
                                :RDSSnapshot,
                                :RDSEventSubscription,
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

### AWSCidrBlock:AWSIpv4CidrBlock:AWSIpv6CidrBlock
Representation of an [AWS CidrBlock used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html).
The `AWSCidrBlock` defines the base label
type for `AWSIpv4CidrBlock` and `AWSIpv6CidrBlock`

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|**id**| Unique identifier defined with the VPC association and the cidr\_block|
|vpcid| The ID of the VPC this CIDR block is associated with|
|association\_id| the association id if the block is associated to a VPC|
|cidr\_block| The CIDR block|
|block\_state| The state of the block|
|block\_state\_message| A message about the status of the CIDR block, if applicable|
|lastupdated| Timestamp of the last time the node was updated|

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

### AWSPrincipal::AWSGroup

Representation of AWS [IAM Groups](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Group.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
|**id** | Same as arn |
|path | The path to the group (IAM identifier, see linked docs above for details)|
| groupid| Unique string identifying the group |
|name | The friendly name that identifies the group|
| createdate| ISO 8601 date-time string when the group was created|
|**arn** | The AWS-global identifier for this group|
| last_accessed_service_name | The name of the most recently accessed AWS service |
| last_accessed_service_namespace | The namespace of the most recently accessed service (e.g., "s3") |
| last_authenticated | ISO 8601 date-time when the service was last accessed |
| last_authenticated_entity | The ARN of the entity that last accessed the service |
| last_authenticated_region | The region where the service was last accessed |

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

- AWSGroups can be assigned AWSPolicies.

    ```cypher
    (:AWSGroup)-[:POLICY]->(:AWSPolicy)
    ```

- AWS Groups can be tagged with AWSTags.

    ```cypher
    (AWSGroup)-[TAGGED]->(AWSTag)
    ```

### GuardDutyDetector

Representation of an AWS [GuardDuty Detector](https://docs.aws.amazon.com/guardduty/latest/APIReference/API_GetDetector.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the GuardDuty detector |
| accountid | The AWS Account ID the detector belongs to |
| region | The AWS Region where the detector is deployed |
| status | Whether the detector is enabled or disabled |
| findingpublishingfrequency | Frequency with which GuardDuty publishes findings |
| service_role | IAM service role used by GuardDuty |
| createdat | Timestamp when the detector was created |
| updatedat | Timestamp when the detector was last updated |

#### Relationships

- AWS Accounts can enable GuardDuty detectors
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:GuardDutyDetector)
    ```

- GuardDuty detectors generate GuardDuty findings
    ```cypher
    (:GuardDutyDetector)<-[:DETECTED_BY]-(:GuardDutyFinding)
    ```

- "What regions have GuardDuty enabled?"
    ```cypher
    MATCH (a:AWSAccount)-[:RESOURCE]->(d:GuardDutyDetector)
    RETURN DISTINCT a.name, d.region
    ```

- "Which EC2 instances are not covered by an enabled GuardDuty detector?"
    ```cypher
    MATCH (a:AWSAccount)-[:RESOURCE]->(i:EC2Instance)
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(d:GuardDutyDetector{status: "ENABLED"})
        WHERE d.region = i.region
    }
    RETURN a.name, i.instanceid, i.region
    ORDER BY a.name, i.region
    ```

### GuardDutyFinding::Risk

Representation of an AWS [GuardDuty Finding](https://docs.aws.amazon.com/guardduty/latest/APIReference/API_Finding.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the GuardDuty finding |
| arn | The Amazon Resource Name (ARN) of the finding |
| type | The type of finding (e.g., "UnauthorizedAccess:EC2/MaliciousIPCaller.Custom") |
| severity | The severity score of the finding (0.1 to 8.9 for medium/high findings) |
| confidence | The confidence level that GuardDuty has in the accuracy of the finding |
| title | A short description of the finding |
| description | A more detailed description of the finding |
| eventfirstseen | Timestamp when the activity that prompted GuardDuty to generate this finding was first observed |
| eventlastseen | Timestamp when the activity that prompted GuardDuty to generate this finding was last observed |
| accountid | The ID of the AWS account in which the finding was generated |
| region | The AWS Region where the finding was generated |
| detectorid | The ID of the detector that generated the finding |
| resource_type | The type of AWS resource affected (Instance, S3Bucket, AccessKey, etc.) |
| resource_id | The identifier of the affected resource (instance ID, bucket name, etc.) |
| archived | Whether the finding has been archived |

#### Relationships

- GuardDuty findings belong to AWS Accounts
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:GuardDutyFinding)
    ```

- GuardDuty findings link back to the detector that produced them
    ```cypher
    (:GuardDutyFinding)-[:DETECTED_BY]->(:GuardDutyDetector)
    ```

- GuardDuty findings may affect EC2 Instances
    ```cypher
    (:GuardDutyFinding)-[:AFFECTS]->(:EC2Instance)
    ```

- GuardDuty findings may affect S3 Buckets
    ```cypher
    (:GuardDutyFinding)-[:AFFECTS]->(:S3Bucket)
    ```

### AWSInspectorFinding

Representation of an AWS [Inspector Finding](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)

| Field | Description | Required|
|-------|-------------|------|
|firstseen|Timestamp of when a sync job first discovered this node|no|
|lastupdated|Timestamp of the last time the node was updated|no|
|**arn**|The AWS ARN|yes|
|id|Reuses the AWS ARN since it's unique|yes|
|region|AWS region the finding is from|yes|
|awsaccount|AWS account the finding is from|yes|
|name|The finding name||
|status|The status of the finding||
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
|firstseen|Timestamp of when a sync job first discovered this node|no|
|lastupdated|Timestamp of the last time the node was updated|no|
|id|Uses the format of `name|epoch:version-release.arch` to uniquely identify packages|yes|
|**name**|The package name||
|arch|Architecture for the package|
|version|Version of the package|
|release|Release of the package
|epoch|Package epoch|
|manager|Related package manager|


#### Relationships

- AWSInspectorFindings have AWSInspectorPackages.

    ```cypher
    (:AWSInspectorFindings)-[:HAS]->(:AWSInspectorPackages)

    ```
    - `HAS` attributes

| Field | Description | Required|
|-------|-------------|------|
|filepath|Path to the file or package|
|sourcelayerhash|Source layer hash for container images|
|sourcelambdalayerarn|ARN of the AWS Lambda function affected|
|fixedinversion|Version the related finding was fixed in|
|remediation|Remediation steps|
|_sub_resource_label|Resource label to do relationships clean-up. Always `AWSAccount`
|_sub_resource_id|Resource id to do relationships clean-up. Always ID of the AWS `RESOURCE` account.


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

> **Ontology Mapping**: This node has the extra label `Function` and normalized `_ont_*` properties for cross-platform serverless function queries. See [Function](../../ontology/schema.md#function).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function|
| **arn** | The Amazon Resource Name (ARN) of the lambda function |
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
| anonymous_actions |  List of anonymous internet accessible actions that may be run on the function. |
| anonymous_access | True if this function has a policy applied to it that allows anonymous access or if it is open to the internet. |
| region | The AWS region where the Lambda function is deployed. |

#### Relationships

- AWSLambda function are resources in an AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AWSLambda)
    ```

- AWSLambda functions may act as AWSPrincipals via role assumption.
    ```
    (:AWSLambda)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)
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
| **arn** | The arn of the lambda function alias|
| functionarn | The ARN of the Lambda function this alias points to |
| aliasname |  The name of the lambda function alias |
| functionversion | The function version that the alias invokes.|
| revisionid |  A unique identifier that changes when you update the alias. |
| description |  The description of the alias. |

#### Relationships

- AWSLambdaFunctionAlias belong to AWS Accounts.
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSLambdaFunctionAlias)
    ```

- AWSLambda functions may also have aliases.
    ```cypher
    (:AWSLambda)-[:KNOWN_AS]->(:AWSLambdaFunctionAlias)
    ```

### AWSLambdaEventSourceMapping

Representation of an [AWSLambdaEventSourceMapping](https://docs.aws.amazon.com/lambda/latest/dg/API_ListEventSourceMappings.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the event source mapping|
| functionarn | The ARN of the Lambda function |
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

- AWSLambdaEventSourceMapping belong to AWS Accounts.
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
    ```

- AWSLambda functions may have the resource AWSLambdaEventSourceMapping.
    ```cypher
    (:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
    ```

### AWSLambdaLayer

Representation of an [AWSLambdaLayer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the lambda function layer|
| **arn** | The arn of the lambda function layer|
| functionarn | The ARN of the Lambda function this layer belongs to |
| codesize | The size of the layer archive in bytes.|
| signingprofileversionarn | The Amazon Resource Name (ARN) for a signing profile version.|
| signingjobarn | The Amazon Resource Name (ARN) of a signing job. |

#### Relationships

- AWSLambdaLayer belong to AWS Accounts
    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSLambdaLayer)
    ```

- AWSLambda functions has AWS Lambda Layers.
    ```cypher
    (:AWSLambda)-[:HAS]->(:AWSLambdaLayer)
    ```


### AWSPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html). There are two types of policies: inline and managed.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The friendly name (not ARN) identifying the policy |
| type | "inline" or "managed" - the type of policy it is|
| arn | The arn for this object |
| **id** | The unique identifer for a policy. If the policy is managed this will be the Arn. If the policy is inline this will calculated as _AWSPrincipal_/inline_policy/_PolicyName_|


#### Relationships

- `AWSPrincipal` contains `AWSPolicy`

    ```cypher
    (:AWSPrincipal)-[:POLICY]->(:AWSPolicy)
    ```

- `AWSPolicy` contains `AWSPolicyStatement`

    ```cypher
    (:AWSPolicy)-[:STATEMENT]->(:AWSPolicyStatement)
    ```

### AWSPolicy::AWSInlinePolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html) of type "inline". An inline policy is a policy that is defined on a principal. Inline policies cannot be shared across principals.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| name | The friendly name (not ARN) identifying the policy |
| type | "inline" |
| **arn** | The arn for this object |
| **id** | The unique identifer for a policy. Calculated as _AWSPrincipal_/inline_policy/_PolicyName_|


#### Relationships

- `AWSPrincipal` contains `AWSInlinePolicy`

    ```cypher
    (:AWSPrincipal)-[:POLICY]->(:AWSInlinePolicy)
    ```

- An `AWSInlinePolicy` is scoped to the AWSAccount of the principal it is attached to.

    ```cypher
    (:AWSInlinePolicy)-[:RESOURCE]->(:AWSAccount)
    ```

- `AWSInlinePolicy` contains `AWSPolicyStatement`

    ```cypher
    (:AWSInlinePolicy)-[:STATEMENT]->(:AWSPolicyStatement)
    ```


### AWSPolicy::AWSManagedPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html) of type "managed". A managed policy is a built-in policy created and maintained by AWS. Managed policies are shared across principals, and as such are not associated with a specific AWSAccount.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| name | The friendly name (not ARN) identifying the policy |
| type | "managed" |
| **arn** | The arn for this object |
| **id** | The arn of the policy |


#### Relationships

- An `AWSPrincipal` can be assigned to one or more `AWSManagedPolicy`s

    ```cypher
    (:AWSPrincipal)-[:POLICY]->(:AWSManagedPolicy)
    ```

- An `AWSManagedPolicy` contains one or more `AWSPolicyStatement`s

    ```cypher
    (:AWSManagedPolicy)-[:STATEMENT]->(:AWSPolicyStatement)
    ```

### AWSPolicyStatement

Representation of an [AWS Policy Statement](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Statement.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated|
| **id** | The unique identifier for a statement. <br>If the statement has an Sid the id will be calculated as _AWSPolicy.id_/statements/_Sid_. <br>If the statement has no Sid the id will be calculated as  _AWSPolicy.id_/statements/_index of statement in statement list_ |
| effect | "Allow" or "Deny" - the effect of this statement |
| action | (array) The permissions allowed or denied by the statement. Can contain wildcards |
| notaction | (array) The permissions explicitly not matched by the statement |
| resource | (array) The resources the statement is applied to. Can contain wildcards |
| notresource | (array) The resources explicitly not matched by the statement |
| condition | Conditions under which the statement applies |
| sid | Statement ID - an optional identifier for the policy statement |


#### Relationships

- `AWSPolicy`s contain one or more `AWSPolicyStatement`s

    ```cypher
    (:AWSPolicy, :AWSInlinePolicy, :AWSManagedPolicy)-[:STATEMENT]->(:AWSPolicyStatement)
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

- AWSPrincipals with appropriate permissions can read from S3 buckets. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).

    ```cypher
    (AWSPrincipal)-[CAN_READ]->(S3Bucket)
    ```

- AWSPrincipals with appropriate permissions can write to S3 buckets. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).

    ```cypher
    (AWSPrincipal)-[CAN_WRITE]->(S3Bucket)
    ```

- AWSPrincipals with appropriate permissions can query DynamoDB tables. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).

    ```cypher
    (AWSPrincipal)-[CAN_QUERY]->(DynamoDBTable)
    ```

- AWSPrincipals with appropriate permissions can administer Redshift clusters. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).

    ```cypher
    (AWSPrincipal)-[CAN_ADMINISTER]->(RedshiftCluster)
    ```

### AWSPrincipal::AWSUser
Representation of an [AWSUser](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).  An AWS User is a type of AWS Principal.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., EntraUser, OktaUser).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The arn of the user |
| path | The path to the user |
| name | The friendly name of the user |
| createdate | ISO 8601 date-time when the user was created |
| **arn** | AWS-unique identifier for this object |
| userid | The stable and unique string identifying the user.  |
| passwordlastused | Datetime when this user's password was last used
| last_accessed_service_name | The name of the most recently accessed AWS service |
| last_accessed_service_namespace | The namespace of the most recently accessed service (e.g., "s3") |
| last_authenticated | ISO 8601 date-time when the service was last accessed |
| last_authenticated_entity | The ARN of the entity that last accessed the service |
| last_authenticated_region | The region where the service was last accessed |

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

- AWS Users can be assigned AWSPolicies.

    ```cypher
    (:AWSUser)-[:POLICY]->(:AWSPolicy)
    ```

- AWS Users can have MFA Devices.

    ```cypher
    (AWSUser)-[:MFA_DEVICE]->(AWSMfaDevice)
    ```

- AWS Users can be tagged with AWSTags.

    ```cypher
    (AWSUser)-[TAGGED]->(AWSTag)
    ```


### AWSPrincipal::AWSRole

Representation of an AWS [IAM Role](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Role.html). An AWS Role is a type of AWS Principal.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The arn of the role |
| roleid | The stable and unique string identifying the role.  |
| name | The friendly name that identifies the role.|
| path | The path to the role. |
| createdate| The date and time, in ISO 8601 date-time format, when the role was created. |
| **arn** | AWS-unique identifier for this object |
| last_accessed_service_name | The name of the most recently accessed AWS service |
| last_accessed_service_namespace | The namespace of the most recently accessed service (e.g., "s3") |
| last_authenticated | ISO 8601 date-time when the service was last accessed |
| last_authenticated_entity | The ARN of the entity that last accessed the service |
| last_authenticated_region | The region where the service was last accessed |


#### Relationships

- Some AWS Groups, Users, Principals, and EC2 Instances can assume AWS Roles.

    ```cypher
    (:AWSGroup, :AWSUser, :EC2Instance)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)
    ```

- Some AWS Roles can assume other AWS Roles.

    ```cypher
    (:AWSRole)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)
    ```

- Some AWS Roles trust AWS Principals.

    ```cypher
    (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSPrincipal)
    ```

- Members of an Okta group can assume associated AWS roles if Okta SAML is configured with AWS.

    ```cypher
    (:AWSRole)-[:ALLOWED_BY]->(:OktaGroup)
    ```

- An IamInstanceProfile can be associated with a role.

    ```cypher
    (:AWSRole)<-[:ASSOCIATED_WITH]-(:AWSInstanceProfile)
    ```

- AWS Roles are defined in AWS Accounts.

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSRole)
    ```

- AWS Roles can be tagged with AWSTags.

    ```cypher
    (AWSRole)-[TAGGED]->(AWSTag)
    ```

- ECSTaskDefinitions have task roles.
    ```cypher
    (:ECSTaskDefinition)-[:HAS_TASK_ROLE]->(:AWSRole)
    ```

- ECSTaskDefinitions have execution roles.
    ```cypher
    (:ECSTaskDefinition)-[:HAS_EXECUTION_ROLE]->(:AWSRole)
    ```

- If an AWSRole trusts an AWSRootPrincipal, all roles in the AWSRootPrincipal's account will be able to assume the role.

    ```cypher
    (:AWSRootPrincipal)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)
    ```

- AWSRoles set up trust relationships with AWSServicePrincipals like "ec2.amazonaws.com" to enable use of those services.

    ```cypher
    (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSServicePrincipal)
    ```

- AWSRoles set up trust relationships with AWSFederatedPrincipals to enable use of those services.

    ```cypher
    (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSFederatedPrincipal)
    ```

- Cartography records assumerole events between AWS principals

    ```cypher
    (:AWSPrincipal)-[:ASSUMED_ROLE {times_used, first_seen, last_seen, lastused}]->(:AWSRole)
    ```

- Cartography records SAML-based role assumptions from CloudTrail management events. This tracks when AWSSSOUsers (federated from identity providers like Okta or Entra) actually assume AWS roles.
    ```cypher
    (AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML {times_used, first_seen_in_time_window, last_used, lastupdated}]->(AWSRole)
    ```
    See [AWSSSOUser](#awsssouser) for more details on this relationship and the [Okta Schema](../okta/schema.md#cross-platform-integration-okta-to-aws) for the complete Okta → AWS SSO → AWS Role integration pattern.

- Cartography records GitHub Actions role assumptions from CloudTrail management events
    ```cypher
    (GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY {times_used, first_seen_in_time_window, last_used, lastupdated}]->(AWSRole)
    ```
    Note: Generic web identity providers are not currently implemented.

### AWSPrincipal::AWSRootPrincipal

Representation of the root principal for an AWS account.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **arn** | The arn of the root principal|
| **id** | Same as arn |


#### Relationships

- Every AWSAccount implicitly has a "root principal".

    ```cypher
    (:AWSAccount)-[:RESOURCE]->(:AWSRootPrincipal)
    ```

- If an AWSRole trusts an AWSRootPrincipal, all roles in the AWSRootPrincipal's account will be able to assume the role.

    ```cypher
    (:AWSRootPrincipal)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)
    ```

### AWSPrincipal::AWSServicePrincipal

Representation of a global AWS service principal e.g. "ec2.amazonaws.com"

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **arn** | The arn of the service principal|
| **id** | Same as arn |
| type | The type of the service principal |

#### Relationships

- We define trust relationships from AWS roles to AWSServicePrincipals like "ec2.amazonaws.com" to enable those services to use those roles.

    ```cypher
    (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSServicePrincipal)
    ```

### AWSPrincipal::AWSFederatedPrincipal

Representation of a federated principal e.g. "arn:aws:iam::123456789012:saml-provider/my-saml-provider". Federated principals are used for authentication to AWS using SAML or OpenID Connect. Federated principals are only discoverable from AWS role trust relationships.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **arn** | The arn of the federated principal|
| **id** | Same as arn |
| type | The type of the federated principal |

#### Relationships

- We can define trust relationships from AWS roles to AWSFederatedPrincipals like "arn:aws:iam::123456789012:saml-provider/my-saml-provider" so that other vendors and products can authenticate to AWS as those roles.

    ```cypher
    (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSFederatedPrincipal)
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
|lastupdated| Timestamp of the last time the node was updated|
|**id**| Unique identifier defined VPC node (vpcid)|
|**vpcid**| The VPC unique identifier|
|primary\_cidr\_block|The primary IPv4 CIDR block for the VPC.|
|instance\_tenancy| The allowed tenancy of instances launched into the VPC.|
|state| The current state of the VPC.|
|is\_default| Indicates whether the VPC is the default VPC.|
|dhcp\_options\_id| The ID of a set of DHCP options.|
|region| (optional) the region of this VPC.  This field is only available on VPCs in your account.  It is not available on VPCs that are external to your account and linked via a VPC peering relationship.|

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
  (AWSVpc)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
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
-  AWS VPCs, DB Subnet Groups, EC2 Instances, EC2 SecurityGroups, EC2 Subnets, EC2 Network Interfaces, RDS Instances, S3 Buckets, AWS Roles, AWS Users, and AWS Groups can be tagged with AWSTags.
    ```
    (AWSVpc, DBSubnetGroup, EC2Instance, EC2SecurityGroup, EC2Subnet, NetworkInterface, RDSInstance, S3Bucket, AWSRole, AWSUser, AWSGroup)-[TAGGED]->(AWSTag)
    ```

### AccountAccessKey

Representation of an AWS [Access Key](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AccessKey.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The access key ID (same as accesskeyid) |
| **accesskeyid** | The ID for this access key |
| createdate | Date when access key was created |
| status | Active: valid for API calls.  Inactive: not valid for API calls |
| lastuseddate | Date when the key was last used |
| lastusedservice | The service that was last used with the access key |
| lastusedregion | The region where the access key was last used |

#### Relationships
- Account Access Keys may authenticate AWS Users and AWS Principal objects.
    ```
    (:AWSUser, :AWSPrincipal)-[:AWS_ACCESS_KEY]->(:AccountAccessKey)
    ```

- Account Access Keys are a resource under the AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AccountAccessKey)
    ```

### AWSMfaDevice

Representation of an AWS [MFA Device](https://docs.aws.amazon.com/IAM/latest/APIReference/API_MFADevice.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The serial number of the MFA device (same as serialnumber) |
| **serialnumber** | The serial number that uniquely identifies the MFA device |
| username | The username of the IAM user associated with the MFA device |
| user_arn | The ARN of the IAM user associated with the MFA device |
| enabledate | ISO 8601 date-time string when the MFA device was enabled |
| enabledate_dt | DateTime object representing when the MFA device was enabled |

#### Relationships
- MFA Devices are associated with AWS Users.

    ```cypher
    (AWSUser)-[:MFA_DEVICE]->(AWSMfaDevice)
    ```

- MFA Devices are resources under the AWS Account.

    ```cypher
    (AWSAccount)-[:RESOURCE]->(AWSMfaDevice)
    ```

### CloudTrailTrail

Representation of an AWS [CloudTrail Trail](https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_Trail.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the trail (same as arn) |
| arn | The ARN of the trail |
| region | The AWS region |
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
| event_selectors | JSON array of event selectors configured for the CloudTrailTrail. |
| advanced_event_selectors | JSON array of advanced event selectors configured for the CloudTrailTrail. |
| name | The name of the CloudTrailTrail. |
| s3_bucket_name | The Amazon S3 bucket name where the CloudTrailTrail delivers files. |
| s3_key_prefix | The S3 key prefix used after the bucket name for the CloudTrailTrail's log files. |
| sns_topic_arn | The ARN of the SNS topic used by the CloudTrailTrail for delivery notifications. |

#### Relationships
- CloudTrail Trails can be configured to log to S3 Buckets
    ```
    (:CloudTrailTrail)-[:LOGS_TO]->(:S3Bucket)
    ```
- CloudTrail Trail can send logs to CloudWatchLogGroup.
    ```
    (:CloudTrailTrail)-[:SENDS_LOGS_TO_CLOUDWATCH]->(:CloudWatchLogGroup)
    ```

### CloudFrontDistribution

Representation of an AWS [CloudFront Distribution](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_DistributionSummary.html).

CloudFront is AWS's global content delivery network (CDN) service. CloudFront distributions are the primary resource that defines how content is cached and delivered to end users.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the CloudFront distribution |
| **arn** | The ARN of the CloudFront distribution |
| distribution_id | The unique identifier for the distribution (e.g., E1A2B3C4D5E6F7) |
| domain_name | The CloudFront domain name (e.g., d1234567890abc.cloudfront.net) |
| status | The current status of the distribution (e.g., Deployed, InProgress) |
| enabled | Whether the distribution is enabled |
| comment | Optional comment describing the distribution |
| price_class | The price class for the distribution (e.g., PriceClass_100, PriceClass_All) |
| http_version | The HTTP version supported (e.g., http2, http2and3) |
| is_ipv6_enabled | Whether IPv6 is enabled for the distribution |
| staging | Whether this is a staging distribution |
| etag | The entity tag for the distribution configuration |
| web_acl_id | The AWS WAF Web ACL ID associated with the distribution |
| aliases | List of CNAMEs (alternate domain names) for the distribution |
| viewer_protocol_policy | The viewer protocol policy from the default cache behavior |
| acm_certificate_arn | The ARN of the ACM certificate for HTTPS |
| cloudfront_default_certificate | Whether the default CloudFront certificate is used |
| minimum_protocol_version | The minimum TLS protocol version (e.g., TLSv1.2_2021) |
| ssl_support_method | The SSL/TLS support method (e.g., sni-only) |
| iam_certificate_id | The IAM certificate ID if using IAM certificates |
| geo_restriction_type | The type of geo restriction (none, whitelist, blacklist) |
| geo_restriction_locations | List of country codes for geo restrictions |

#### Relationships

- CloudFront Distributions are resources in an AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:CloudFrontDistribution)
    ```
- CloudFront Distributions can serve content from S3 Buckets.
    ```
    (:CloudFrontDistribution)-[:SERVES_FROM]->(:S3Bucket)
    ```
- CloudFront Distributions can use ACM Certificates for HTTPS.
    ```
    (:CloudFrontDistribution)-[:USES_CERTIFICATE]->(:ACMCertificate)
    ```
- CloudFront Distributions can use Lambda@Edge functions.
    ```
    (:CloudFrontDistribution)-[:USES_LAMBDA_EDGE]->(:AWSLambda)
    ```

### CloudWatchLogGroup
Representation of an AWS [CloudWatch Log Group](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_LogGroup.html)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the log group |
| **arn** | The Amazon Resource Name (ARN) of the log group |
| creation_time | The creation time of the log group, expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC |
| data_protection_status | Displays whether this log group has a protection policy, or whether it had one in the past |
| inherited_properties | Displays all the properties that this log group has inherited from account-level settings |
| kms_key_id | The Amazon Resource Name (ARN) of the AWS KMS key to use when encrypting log data |
| log_group_arn | The Amazon Resource Name (ARN) of the log group |
| log_group_class | This specifies the log group class for this log group |
| log_group_name | The name of the log group |
| metric_filter_count | The number of metric filters |
| retention_in_days | The number of days to retain the log events in the specified log group |
| stored_bytes | The number of bytes stored |
#### Relationships
- CLoudWatch LogGroups are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CloudWatchLogGroup)
    ```

### CloudWatchMetricAlarm
Representation of an AWS [CloudWatch Metric Alarm](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ARN of the CloudWatch Metric Alarm |
| **arn** | The ARN of the CloudWatch Metric Alarm |
| region | The region of the CloudWatch Metric Alarm |
| alarm_name | The name of the alarm |
| alarm_description | The description of the alarm |
| state_value | The state value for the alarm |
| state_reason | An explanation for the alarm state, in text format |
| actions_enabled | Indicates whether actions should be executed during any changes to the alarm state |
| comparison_operator | The arithmetic operation to use when comparing the specified statistic and threshold. The specified statistic value is used as the first operand |
#### Relationships
- CloudWatch Metric Alarms are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CloudWatchMetricAlarm)
    ```

### CloudWatchLogMetricFilter
Representation of an AWS [CloudWatch Log Metric Filter](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DescribeMetricFilters.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Ensures that the id field is a unique combination of logGroupName and filterName |
| **arn** | Ensures that the arn field is a unique combination of logGroupName and filterName |
| region | The region of the CloudWatch Log Metric Filter |
| filter_name | The name of the filter pattern used to extract metric data from log events |
| filter_pattern | The pattern used to extract metric data from CloudWatch log events |
| log_group_name | The name of the log group to which this metric filter is applied |
| metric_name | The name of the metric emitted by this filter |
| metric_namespace | The namespace of the metric emitted by this filter |
| metric_value | The value to publish to the CloudWatch metric when a log event matches the filter pattern |
#### Relationships
- CLoudWatch Log Metric Filters are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CloudWatchLogMetricFilter)
    ```
- CloudWatchLogMetricFilter associated with CloudWatchLogGroup via the METRIC_FILTER_OF relationship
    ```
    (CloudWatchLogMetricFilter)-[METRIC_FILTER_OF]->(CloudWatchLogGroup)
    ```

### GlueConnection
Representation of an AWS [Glue Connection](https://docs.aws.amazon.com/glue/latest/webapi/API_GetConnections.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The name of the Glue connection definition |
| **arn** | The name of the Glue connection definition |
| region | The region of the Glue Connection |
| description | The description of the connection |
| connection_type | The type of the connection. Currently, SFTP is not supported |
| status| The status of the connection. Can be one of: READY, IN_PROGRESS, or FAILED |
| status_reason | The reason for the connection status |
| authentication_type | A structure containing the authentication configuration |
| secret_arn | The secret manager ARN to store credentials |
#### Relationships
- Glue Connections are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(GlueConnection)
    ```

### GlueJob
Representation of an AWS [Glue Job](https://docs.aws.amazon.com/glue/latest/webapi/API_GetJobs.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The name you assign to this job definition |
| **arn** | The name you assign to this job definition |
| region | The region of the Glue job |
| description | The description of the job |
| profile_name | The name of an AWS Glue usage profile associated with the job |
| job_mode | A mode that describes how a job was created |
| connections | The connections used for this job |
#### Relationships
- Glue Jobs are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(GlueJob)
    ```
- Glue Jobs are used by Glue Connections.
    ```
    (GlueConnection)-[USES]->(GlueJob)
    ```


### CodeBuildProject
Representation of an AWS [CodeBuild Project](https://docs.aws.amazon.com/codebuild/latest/APIReference/API_Project.html)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The ARN of the CodeBuild Project |
| **arn** | The Amazon Resource Name (ARN) of the CodeBuild Project |
| region | The region of the codebuild project |
| created | The creation time of the CodeBuild Project |
| environment_variables | A list of environment variables used in the build environment. Each variable is represented as a string in the format `<NAME>=<VALUE>`. Variables of type `PLAINTEXT` retain their values (e.g., `ENV=prod`), while variables of type `PARAMETER_STORE`, `SECRETS_MANAGER`, etc., have values redacted as `<REDACTED>` (e.g., `SECRET_TOKEN=<REDACTED>`) |
| source_type | The type of repository that contains the source code to be built |
| source_location | Information about the location of the source code to be built |
#### Relationships
- CodeBuild Projects are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CodeBuildProject)
    ```

### CognitoIdentityPool
Representation of an AWS [Cognito Identity Pool](https://docs.aws.amazon.com/cognitoidentity/latest/APIReference/API_ListIdentityPools.html)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The id of Cognito Identity Pool |
| **arn** | The Amazon Resource Name (ARN) of the Cognito Identity Pool |
| region | The region of the Cognito Identity Pool |
| roles | list of aws roles associated with Cognito Identity Pool |
#### Relationships
- Cognito Identity Pools are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CognitoIdentityPool)
    ```
- Cognito Identity Pools are associated with AWS Roles.
    ```
    (CognitoIdentityPool)-[ASSOCIATED_WITH]->(AWSRole)
    ```

### CognitoUserPool
Representation of an AWS [Cognito User Pool](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUserPools.html)

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The id of Cognito User Pool |
| **arn** | The Amazon Resource Name (ARN) of the Cognito User Pool |
| region | The region of the Cognito User Pool |
| name | Name of Cognito User Pool |
| status | Status of User Pool |
#### Relationships
- Cognito User Pools are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(CognitoUserPool)
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
|region| The AWS region where the DB Subnet Group is located.|

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
|**name**| The name of the DNSRecord|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The zoneid for the record, the value of the record, and the type concatenated together|
|type| The record type of the DNS record (A, AAAA, ALIAS, CNAME, NS, etc.)|
|value| If it is an A or AAAA record, this is the IP address the DNSRecord resolves to. For CNAME or ALIAS records, this is the target hostname or AWS resource name. If it is an NS record, the `name` is used here.|

#### Relationships
- AWSDNSRecords can point to IP addresses.
    ```
    (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:Ip)
    ```

- DNSRecords/AWSDNSRecords can point to each other.
    ```
    (:AWSDNSRecord, :DNSRecord)-[:DNS_POINTS_TO]->(:AWSDNSRecord, :DNSRecord)
    ```


- AWSDNSRecords can point to LoadBalancers.
    ```
    (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:LoadBalancer, :ESDomain)
    ```

- AWSDNSRecords can point to ElasticIPAddresses.
    ```
    (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:ElasticIPAddress)
    ```

- AWSDNSRecords can be members of AWSDNSZones.
    ```
    (:AWSDNSRecord)-[:MEMBER_OF_DNS_ZONE]->(:AWSDNSZone)
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
|**id**| The zoneid defined by Amazon Route53 (same as zoneid)|
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


### NameServer

Representation of a DNS name server associated with an AWS Route53 hosted zone.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the name server (typically the fully qualified domain name) |
| **name** | The fully qualified domain name of the name server |
| zoneid | The ID of the Route53 hosted zone this name server belongs to |

#### Relationships

- NameServers belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(NameServer)
    ```

- NameServers are associated with AWSDNSZones.
    ```
    (AWSDNSZone)-[NAMESERVER]->(NameServer)
    ```


### DynamoDBTable::Database

Representation of an AWS [DynamoDBTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TableDescription.html).

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for database instances across different systems (e.g., AzureSQLDatabase, GCPBigtableInstance).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the table |
| **arn** | The AWS-unique identifier (ARN) |
| name | The name of the table |
| region | The AWS region of the table |
| rows | The number of items in the table |
| size | The size of the table in bytes |
| table_status | The current state of the table (e.g., ACTIVE, CREATING, DELETING) |
| creation_date_time | The date and time when the table was created |
| provisioned_throughput_read_capacity_units | The maximum number of reads consumed per second |
| provisioned_throughput_write_capacity_units | The maximum number of writes consumed per second |

#### Relationships
- DynamoDBTables belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBTable)
    ```

- DynamoDBTables have Global Secondary Indexes.
    ```cypher
    (DynamoDBTable)-[:GLOBAL_SECONDARY_INDEX]->(DynamoDBGlobalSecondaryIndex)
    ```

- DynamoDBTables have SSE (Server-Side Encryption) descriptions.
    ```cypher
    (DynamoDBTable)-[:HAS_SSE]->(DynamoDBSSEDescription)
    ```

- DynamoDBTables have billing mode summaries.
    ```cypher
    (DynamoDBTable)-[:HAS_BILLING]->(DynamoDBBillingModeSummary)
    ```

- DynamoDBTables have streams.
    ```cypher
    (DynamoDBTable)-[:LATEST_STREAM]->(DynamoDBStream)
    ```

- DynamoDBTables have archival summaries (for archived tables).
    ```cypher
    (DynamoDBTable)-[:HAS_ARCHIVAL]->(DynamoDBArchivalSummary)
    ```

- DynamoDBTables have restore summaries (for restored tables).
    ```cypher
    (DynamoDBTable)-[:HAS_RESTORE]->(DynamoDBRestoreSummary)
    ```


### DynamoDBGlobalSecondaryIndex

Representation of a DynamoDB [Global Secondary Index](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GlobalSecondaryIndexDescription.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the GSI |
| arn | The ARN of the GSI |
| name | The name of the GSI |
| region | The AWS region of the GSI |
| provisioned_throughput_read_capacity_units | The maximum number of reads consumed per second |
| provisioned_throughput_write_capacity_units | The maximum number of writes consumed per second |

#### Relationships
- DynamoDBGlobalSecondaryIndexes belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBGlobalSecondaryIndex)
    ```

- DynamoDBGlobalSecondaryIndexes belong to DynamoDBTables.
    ```cypher
    (DynamoDBTable)-[:GLOBAL_SECONDARY_INDEX]->(DynamoDBGlobalSecondaryIndex)
    ```


### DynamoDBSSEDescription

Representation of DynamoDB [Server-Side Encryption description](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_SSEDescription.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier (table ARN + "/sse") |
| sse_status | The current state of SSE (e.g., ENABLED, DISABLED) |
| sse_type | The server-side encryption type (AES256 or KMS) |
| kms_master_key_arn | The ARN of the KMS key used for encryption (if SSE type is KMS) |

#### Relationships
- DynamoDBSSEDescriptions belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBSSEDescription)
    ```

- DynamoDBSSEDescriptions belong to DynamoDBTables.
    ```cypher
    (DynamoDBTable)-[:HAS_SSE]->(DynamoDBSSEDescription)
    ```

- DynamoDBSSEDescriptions may use KMS keys for encryption.
    ```cypher
    (DynamoDBSSEDescription)-[:USES_KMS_KEY]->(KMSKey)
    ```


### DynamoDBBillingModeSummary

Representation of DynamoDB [Billing Mode Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BillingModeSummary.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier (table ARN + "/billing") |
| billing_mode | The billing mode (PROVISIONED or PAY_PER_REQUEST) |
| last_update_to_pay_per_request_date_time | When the table was last switched to PAY_PER_REQUEST mode |

#### Relationships
- DynamoDBBillingModeSummaries belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBBillingModeSummary)
    ```

- DynamoDBBillingModeSummaries belong to DynamoDBTables.
    ```cypher
    (DynamoDBTable)-[:HAS_BILLING]->(DynamoDBBillingModeSummary)
    ```


### DynamoDBStream

Representation of a DynamoDB [Stream](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_StreamSpecification.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the stream |
| arn | The ARN of the stream |
| stream_label | A timestamp used as the stream label |
| stream_enabled | Whether the stream is enabled |
| stream_view_type | What information is written to the stream (KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES) |

#### Relationships
- DynamoDBStreams belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBStream)
    ```

- DynamoDBStreams belong to DynamoDBTables.
    ```cypher
    (DynamoDBTable)-[:LATEST_STREAM]->(DynamoDBStream)
    ```


### DynamoDBArchivalSummary

Representation of DynamoDB [Archival Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_ArchivalSummary.html) for archived tables.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier (table ARN + "/archival") |
| archival_date_time | The date and time when table archival was initiated |
| archival_reason | The reason for archiving the table |
| archival_backup_arn | The ARN of the backup created when the table was archived |

#### Relationships
- DynamoDBArchivalSummaries belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBArchivalSummary)
    ```

- DynamoDBArchivalSummaries belong to DynamoDBTables.
    ```cypher
    (DynamoDBTable)-[:HAS_ARCHIVAL]->(DynamoDBArchivalSummary)
    ```

- DynamoDBArchivalSummaries reference the backup created during archival.
    ```cypher
    (DynamoDBArchivalSummary)-[:ARCHIVED_TO_BACKUP]->(DynamoDBBackup)
    ```


### DynamoDBRestoreSummary

Representation of DynamoDB [Restore Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_RestoreSummary.html) for restored tables.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier (table ARN + "/restore") |
| restore_date_time | Point in time or source backup time for the restore |
| restore_in_progress | Indicates whether a restore is currently in progress |
| source_backup_arn | The ARN of the backup from which the table was restored |
| source_table_arn | The ARN of the source table from which the table was restored |

#### Relationships
- DynamoDBRestoreSummaries belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBRestoreSummary)
    ```

- DynamoDBRestoreSummaries belong to DynamoDBTables (the restored table).
    ```cypher
    (DynamoDBTable)-[:HAS_RESTORE]->(DynamoDBRestoreSummary)
    ```

- DynamoDBRestoreSummaries reference the source backup.
    ```cypher
    (DynamoDBRestoreSummary)-[:RESTORED_FROM_BACKUP]->(DynamoDBBackup)
    ```

- DynamoDBRestoreSummaries reference the source table.
    ```cypher
    (DynamoDBRestoreSummary)-[:RESTORED_FROM_TABLE]->(DynamoDBTable)
    ```


### DynamoDBBackup

Representation of a DynamoDB [Backup](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BackupDetails.html). Currently a stub entity referenced by archival and restore summaries.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the backup |
| arn | The ARN of the backup |

#### Relationships
- DynamoDBBackups belong to AWS Accounts.
    ```cypher
    (AWSAccount)-[:RESOURCE]->(DynamoDBBackup)
    ```

- DynamoDBBackups are referenced by archival summaries.
    ```cypher
    (DynamoDBArchivalSummary)-[:ARCHIVED_TO_BACKUP]->(DynamoDBBackup)
    ```

- DynamoDBBackups are referenced by restore summaries.
    ```cypher
    (DynamoDBRestoreSummary)-[:RESTORED_FROM_BACKUP]->(DynamoDBBackup)
    ```

- AWSPrincipals with appropriate permissions can query DynamoDB tables. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).
    ```
    (AWSPrincipal)-[CAN_QUERY]->(DynamoDBTable)
    ```


### DynamoDBGlobalSecondaryIndex

Representation of a [DynamoDB Global Secondary Index](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GlobalSecondaryIndexDescription.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the global secondary index |
| arn | The Amazon Resource Name (ARN) of the global secondary index |
| name | The name of the global secondary index |
| region | The AWS region |
| provisioned_throughput_read_capacity_units | The maximum number of read capacity units for the global secondary index |
| provisioned_throughput_write_capacity_units | The maximum number of write capacity units for the global secondary index |

#### Relationships

- DynamoDBGlobalSecondaryIndex belongs to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(DynamoDBGlobalSecondaryIndex)
    ```

- DynamoDBGlobalSecondaryIndex belongs to DynamoDBTables.
    ```
    (DynamoDBTable)-[GLOBAL_SECONDARY_INDEX]->(DynamoDBGlobalSecondaryIndex)
    ```


### EC2Instance

Our representation of an AWS [EC2 Instance](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute resources across different systems (e.g., ScalewayInstance, DigitalOceanDroplet).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Same as `instanceid` below. |
| **instanceid** | The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203) |
| **publicdnsname** | The public DNS name assigned to the instance |
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
| exposed\_internet\_type | A list indicating the type(s) of internet exposure. Possible values are `direct` (directly exposed via security group), `elb` (exposed via classic LoadBalancer), or `elbv2` (exposed via AWSLoadBalancerV2). Set by the `aws_ec2_asset_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/aws_ec2_asset_exposure.json). |
| availabilityzone | The Availability Zone of the instance.|
| tenancy | The tenancy of the instance.|
| hostresourcegrouparn | The ARN of the host resource group in which to launch the instances.|
| platform | The value is `Windows` for Windows instances; otherwise blank.|
| architecture | The architecture of the image.|
| ebsoptimized | Indicates whether the instance is optimized for Amazon EBS I/O. |
| bootmode | The boot mode of the instance.|
| instancelifecycle | Indicates whether this is a Spot Instance or a Scheduled Instance.|
| hibernationoptions | Indicates whether the instance is enabled for hibernation.|
| eks_cluster_name | The name of the EKS cluster this instance belongs to, if applicable. Extracted from instance tags.|


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

- EC2Instances can be members of EKS Clusters
    ```
    (EC2Instance)-[MEMBER_OF_EKS_CLUSTER]->(EKSCluster)
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
| **id** | Unique identifier for the private IP |
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
| **id** | The ID of the reservation (same as reservationid) |
| **reservationid** | The ID of the reservation. |
| requesterid | The ID of the requester that launched the instances on your behalf |
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
| **id** | Same as `groupid` |
| **groupid** | The ID of the security group. Note that these are globally unique in AWS. |
| name | The name of the security group |
| description | A description of the security group |
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

- Security Groups can allow traffic from other security groups. This relationship can also be self-referential, meaning that a security group can allow traffic from itself (as security groups are default-deny). Relevant API docs: [IP Permission](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_IpPermission.html), [UserIdGroupPair](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_UserIdGroupPair.html).
    ```
    (:EC2SecurityGroup)-[:ALLOWS_TRAFFIC_FROM]->(:EC2SecurityGroup)
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
| **subnet_id** | The ID of the subnet|
| **id** | same as subnetid |
| region| The AWS region the subnet is installed on|
| vpc_id | The ID of the VPC this subnet belongs to |
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

- A AWSLoadBalancerV2 can be part of an EC2 Subnet.
    ```
    (AWSLoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
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

- EC2RouteTableAssociation links a subnet to a route table. The subnet uses this route table for egress routing decisions.
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

> **Ontology Mapping**: This node has the extra label `ContainerRegistry` to enable cross-platform queries for container registries across different systems (e.g., ECRRepository, GCPArtifactRegistryRepository, GitLabContainerRepository).

| Field | Description |
|--------|-----------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The ARN of the repository |
| **name** | The name of the repository |
| uri | The URI of the repository |
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

> **Ontology Mapping**: This node has the extra label `ImageTag` to enable cross-platform queries for image tags across different container registries.

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

- ECRRepositoryImages may be packaged from a source repository (cross-module relationship via VCS modules)
    ```
    (:ECRRepositoryImage)-[:PACKAGED_FROM]->(:GitHubRepository)
    ```

    Relationship properties:
    - **dockerfile_path**: Path to the Dockerfile in the repository
    - **confidence**: Confidence score of the match (0.0 to 1.0)
    - **matched_commands**: Number of commands that matched
    - **total_commands**: Total number of commands compared
    - **command_similarity**: Average similarity score

    This relationship links all images in an ECR repository to the source VCS repository via `repo_uri` matching.


### ECRImage

Representation of an ECR image identified by its digest (e.g. a SHA hash). Specifically, this is the "digest part" of
[`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html). Also see
ECRRepositoryImage.

For multi-architecture images, Cartography creates ECRImage nodes for the manifest list, each platform-specific image, and any attestations.

> **Ontology Mapping**: This node has conditional extra labels based on the `type` field: `Image` (when type="image"), `ImageAttestation` (when type="attestation"), or `ImageManifestList` (when type="manifest_list"). This enables cross-platform queries for container images across different registries.

| Field | Description |
|--------|-----------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Same as digest |
| **digest** | The hash of this ECR image |
| region | The AWS region |
| layer_diff_ids | Ordered list of image layer digests for this image. Only set for `type="image"` nodes. `null` for manifest lists and attestations. |
| type | Type of image: `"image"` (platform-specific or single-arch image), `"manifest_list"` (multi-arch index), or `"attestation"` (attestation manifest) |
| architecture | CPU architecture (e.g., `"amd64"`, `"arm64"`). Set to `"unknown"` for attestations, `null` for manifest lists. |
| os | Operating system (e.g., `"linux"`, `"windows"`). Set to `"unknown"` for attestations, `null` for manifest lists. |
| variant | Architecture variant (e.g., `"v8"` for ARM). Optional field. |
| attestation_type | For attestations only: the type of attestation (e.g., `"attestation-manifest"`). `null` for regular images. |
| attests_digest | For attestations only: the digest of the image this attestation is for. `null` for regular images. |
| media_type | The OCI/Docker media type of this manifest (e.g., `"application/vnd.oci.image.manifest.v1+json"`) |
| artifact_media_type | The artifact media type if this is an OCI artifact. Optional field. |
| child_image_digests | For manifest lists only: list of platform-specific image digests contained in this manifest list. Excludes attestations. `null` for regular images and attestations. |
| **source_uri** | Source repository URI extracted from SLSA provenance attestations (e.g., a GitLab project URL or GitHub repo URL). Indexed for cross-module matching. |
| source_revision | Source commit revision from SLSA provenance attestations. |
| **invocation_uri** | CI/CD invocation URI from SLSA provenance (e.g., GitHub repository URL). Indexed for cross-module matching. |
| **invocation_workflow** | CI/CD workflow path from SLSA provenance (e.g., `.github/workflows/build.yml`). Indexed for cross-module matching. |
| invocation_run_number | CI/CD run number from SLSA provenance (e.g., the GitHub Actions run number). |
| source_file | Dockerfile path from SLSA provenance (`configSource.entryPoint` prefixed with `vcs localdir:dockerfile` if present). |

#### Relationships

- ECRRepositoryImages reference ECRImages
    ```
    (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage)
    ```

- Software packages are a part of ECR Images
    ```
    (:Package)-[:DEPLOYED]->(:ECRImage)
    ```

- An ECRImage references its layers (only applies to `type="image"` nodes)
    ```
    (:ECRImage)-[:HAS_LAYER]->(:ECRImageLayer)
    ```

- A TrivyImageFinding is a vulnerability that affects an ECRImage.

    ```
    (:TrivyImageFinding)-[:AFFECTS]->(:ECRImage)
    ```

- ECSContainers have images.
    ```
    (:ECSContainer)-[:HAS_IMAGE]->(:ECRImage)
    ```

- KubernetesContainers have images. The relationship matches containers to images by digest (`status_image_sha`).
    ```
    (:KubernetesContainer)-[:HAS_IMAGE]->(:ECRImage)
    ```

- An ECRImage may be built from a parent ECRImage (derived from provenance attestations).
    ```
    (:ECRImage)-[:BUILT_FROM]->(:ECRImage)
    ```

    Relationship properties:
    - `parent_image_uri`: The package URI of the parent image from the attestation (e.g., `pkg:docker/account.dkr.ecr.region.amazonaws.com/repo@digest`)
    - `from_attestation`: Boolean flag indicating the relationship was derived from provenance attestation (always `true`)
    - `confidence`: Confidence level of the relationship (always `"explicit"` for attestation-based relationships)

- A manifest list ECRImage contains platform-specific ECRImages (only applies to `type="manifest_list"` nodes)
    ```
    (:ECRImage {type: "manifest_list"})-[:CONTAINS_IMAGE]->(:ECRImage {type: "image"})
    ```

- An attestation ECRImage attests/validates another ECRImage (only applies to `type="attestation"` nodes)
    ```
    (:ECRImage {type: "attestation"})-[:ATTESTS]->(:ECRImage)
    ```

- An ECRImage may be packaged by a GitHubWorkflow (derived from SLSA provenance attestations). Only applies to `type="image"` nodes with the `Image` semantic label.
    ```
    (:ECRImage:Image)-[:PACKAGED_BY]->(:GitHubWorkflow)
    ```

    Note: This cross-module relationship is created when SLSA provenance attestations specify the GitHub Actions workflow that built the container image. See the [GitHub schema](../github/schema.md#githubworkflow) for more details on GitHubWorkflow nodes.


### ECRImageLayer

Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `ECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)

> **Ontology Mapping**: This node has the extra label `ImageLayer` to enable cross-platform queries for image layers across different container registries.

| Field | Description |
|-------|-------------|
| **id** | Same as `diff_id` |
| diff_id | Digest of the layer |
| lastupdated | Timestamp of the last time the node was updated |
| is_empty | Boolean flag identifying Docker's empty layer (true when the **DiffID** is `sha256:5f70bf18...`). |
| history | The `created_by` command from the image config that created this layer (e.g., `/bin/sh -c pip install flask`). Used for Dockerfile matching. |

#### Relationships

- Image layers belong to an AWSAccount
    ```
    (:ECRImageLayer)<-[:RESOURCE]-(:AWSAccount)
    ```

- Layers point to the next layer in the manifest
    ```
    (:ECRImageLayer)-[:NEXT]->(:ECRImageLayer)
    ```

- A layer can be the head of a platform-specific image (only `type="image"` nodes have layer relationships)
    ```
    (:ECRImage {type: "image"})-[:HEAD]->(:ECRImageLayer)
    ```

- A layer can be the tail of a platform-specific image
    ```
    (:ECRImage {type: "image"})-[:TAIL]->(:ECRImageLayer)
    ```

- Platform-specific images reference all of their layers
    ```
    (:ECRImage {type: "image"})-[:HAS_LAYER]->(:ECRImageLayer)
    ```

#### Query Examples

- List the ordered layers for a specific image directly from graph relationships:
    ```cypher
    MATCH (img:ECRImage {digest: $digest})-[:HEAD]->(head:ECRImageLayer)
    MATCH (img)-[:TAIL]->(tail:ECRImageLayer)
    MATCH path = (head)-[:NEXT*0..]->(tail)
    WHERE ALL(layer IN nodes(path) WHERE (img)-[:HAS_LAYER]->(layer))
    WITH path
    ORDER BY length(path) DESC
    LIMIT 1
    UNWIND range(0, length(path)) AS idx
    RETURN idx AS position, nodes(path)[idx].diff_id AS diff_id
    ORDER BY position;
    ```

- Use the stored manifest order when you only need the digests:
    ```cypher
    MATCH (img:ECRImage {digest: $digest})
    UNWIND range(0, size(img.layer_diff_ids) - 1) AS idx
    RETURN idx AS position, img.layer_diff_ids[idx] AS diff_id
    ORDER BY position;
    ```

- Detect images whose layer chains diverge (typically because the Docker empty layer is repeated):
    ```cypher
    MATCH (img:ECRImage)-[:HAS_LAYER]->(layer:ECRImageLayer)
    MATCH (layer)-[:NEXT]->(child:ECRImageLayer)
    WHERE (img)-[:HAS_LAYER]->(child)
    WITH img, layer, collect(DISTINCT child.diff_id) AS next_diff_ids
    WHERE size(next_diff_ids) > 1
    RETURN img.digest AS digest,
           layer.diff_id AS branching_layer,
           next_diff_ids AS successors
    ORDER BY digest, branching_layer;
    ```
- Find parent image given a digest (need to specify base image repository):
    ```cypher
    WITH $target_digest as target_digest
    // Get target image's layer chain via graph traversal
    MATCH (target:ECRImage {digest: target_digest})
    MATCH (target)-[:HAS_LAYER]->(tl:ECRImageLayer)
    WITH target, collect(id(tl)) AS targetAllowedIds
    CALL {
    WITH target, targetAllowedIds
    MATCH p = (target)-[:HEAD]->(:ECRImageLayer)-[:NEXT*0..]->(:ECRImageLayer)<-[:TAIL]-(target)
    WITH p, targetAllowedIds, [n IN nodes(p) WHERE n:ECRImageLayer | id(n)] AS layerIds
    WHERE all(i IN layerIds WHERE i IN targetAllowedIds)
    RETURN [n IN nodes(p) WHERE n:ECRImageLayer | n.diff_id] AS target_diff_ids
    ORDER BY length(p) DESC
    LIMIT 1
    }
    // Get all base images with their layer chains from a repo called 'base-images'
    MATCH (base_repo:ECRRepository {name: 'base-images'})-[:REPO_IMAGE]->(base_img:ECRRepositoryImage)-[:IMAGE]->(base:ECRImage)
    MATCH (base)-[:HAS_LAYER]->(bl:ECRImageLayer)
    WITH target_diff_ids, base, base_img, collect(id(bl)) AS baseAllowedIds
    CALL {
    WITH base, baseAllowedIds
    MATCH p = (base)-[:HEAD]->(:ECRImageLayer)-[:NEXT*0..]->(:ECRImageLayer)<-[:TAIL]-(base)
    WITH p, baseAllowedIds, [n IN nodes(p) WHERE n:ECRImageLayer | id(n)] AS layerIds
    WHERE all(i IN layerIds WHERE i IN baseAllowedIds)
    RETURN [n IN nodes(p) WHERE n:ECRImageLayer | n.diff_id] AS base_diff_ids
    ORDER BY length(p) DESC
    LIMIT 1
    }
    // Calculate longest common prefix
    WITH target_diff_ids, base, base_img, base_diff_ids,
        REDUCE(lcp = 0, i IN RANGE(0, SIZE(base_diff_ids)-1) |
        CASE WHEN i < SIZE(target_diff_ids) AND base_diff_ids[i] = target_diff_ids[i]
                THEN lcp + 1 ELSE lcp END
        ) as lcp_length
    // Only keep matches where ALL base layers match (complete prefix)
    WHERE lcp_length = SIZE(base_diff_ids)
    RETURN base.digest, base_img.uri, base_img.tag, base_img.image_pushed_at,
        SIZE(base_diff_ids) as base_layer_count, lcp_length
    ORDER BY lcp_length DESC, base_img.image_pushed_at DESC
    LIMIT 1
    ```

- Find all platform-specific images in a multi-architecture manifest list:
    ```cypher
    MATCH (manifest_list:ECRImage {type: "manifest_list"})-[:CONTAINS_IMAGE]->(platform_image:ECRImage)
    RETURN platform_image.architecture, platform_image.os, platform_image.variant, platform_image.digest
    ORDER BY platform_image.architecture;
    ```

- Find which image an attestation validates:
    ```cypher
    MATCH (attestation:ECRImage {type: "attestation"})-[:ATTESTS]->(image:ECRImage)
    RETURN attestation.digest AS attestation_digest, image.digest AS validated_image_digest;
    ```

- Find all attestations for a specific image:
    ```cypher
    MATCH (attestation:ECRImage {type: "attestation"})-[:ATTESTS]->(image:ECRImage {digest: $digest})
    RETURN attestation.digest, attestation.attestation_type;
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

- A TrivyImageFinding is a vulnerability that affects a software Package.

    ```
    (:TrivyImageFinding)-[:AFFECTS]->(:Package)
    ```

- We should update a vulnerable package to a fixed version described by a TrivyFix.

    ```
    (:Package)-[:SHOULD_UPDATE_TO]->(:TrivyFix)
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
| **name** | Name of the EKS Cluster |
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
| arn | The ARN of the ELBV2Listener |

#### Relationships

- AWSLoadBalancerV2's have [listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html):
    ```
    (:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(:ELBV2Listener)
    ```
- ACM Certificates may be used by ELBV2Listeners.
    ```
    (:ACMCertificate)-[:USED_BY]->(:ELBV2Listener)
    ```

### EventBridgeRule
Representation of an AWS [EventBridge Rule](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_ListRules.html)
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | System-assigned eventbridge rule ID |
| **arn** | The Amazon Resource Name (ARN) of the rule |
| region | The region of the rule |
| name | The name of the rule |
| role_arn | The Amazon Resource Name (ARN) of the role that is used for target invocation |
| event_pattern | The event pattern of the rule |
| state | The state of the rule, Valid Values: ENABLED, DISABLED, ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS |
| description | The description of the rule |
| schedule_expression | The scheduling expression |
| managed_by | If the rule was created on behalf of your account by an AWS service, this field displays the principal name of the service that created the rule |
| event_bus_name | The name or ARN of the event bus associated with the rule |
#### Relationships
- EventBridge Rules are resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EventBridgeRule)
    ```
 - EventBridge Rules are associated with the AWS Role.
    ```
    (EventBridgeRule)-[ASSOCIATED_WITH]->(AWSRole)
    ```

### EventBridgeTarget
Representation of an AWS [EventBridge Target](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_ListTargetsByRule.html)
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | System-assigned eventbridge target ID |
| **arn** | The Amazon Resource Name (ARN) of the target |
| region | The region of the target |
| rule_arn | The arn of the rule which is associated with target |
| role_arn | The Amazon Resource Name (ARN) of the role that is used for target invocation |
#### Relationships
- EventBridge Targets are resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EventBridgeTarget)
    ```
 - EventBridge Targets are linked with the EventBridge Rules.
    ```
    (EventBridgeTarget)-[LINKED_TO_RULE]->(EventBridgeRule)
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


### AWSIpRule::IpRule

Represents a generic IP rule.  The creation of this node is currently derived from ingesting AWS [EC2 Security Group](#ec2securitygroup) rules.

> **Ontology Mapping**: This node has the extra label `IpRule` to preserve cross-platform semantics for generic IP rules.

| Field | Description |
|-------|-------------|
| **id** | Same as ruleid |
| **ruleid** | `{group_id}/{rule_type}/{from_port}{to_port}{protocol}` |
| **groupid** | The groupid of the EC2 Security Group that this was derived from |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| protocol | The protocol this rule applies to |
| fromport | Lowest port in the range defined by this rule|
| toport | Highest port in the range defined by this rule|


#### Relationships

- AWSIpRules are defined from EC2SecurityGroups.
    ```
    (AWSIpRule)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```


### AWSIpPermissionInbound::IpPermissionInbound::IpRule::AWSIpRule

An AWSIpPermissionInbound node is a specific type of AWSIpRule. It represents inbound IP-based rules derived from AWS [EC2 Security Group](#ec2securitygroup) rules.

> **Ontology Mapping**: This node has the extra labels `IpPermissionInbound`, `IpRule`, and `AWSIpRule` for backward compatibility and cross-platform semantics.

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

- AWSIpPermissionInbound rules are defined from EC2SecurityGroups.
    ```
    (AWSIpPermissionInbound)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```


### AWSIpRange::IpRange

Represents an IP address range (CIDR block) associated with an EC2 Security Group rule. IpRange nodes define the source or destination IP addresses that a security group rule applies to.

> **Ontology Mapping**: This node has the extra label `IpRange` to preserve cross-platform semantics for generic IP ranges.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the IP range (typically the CIDR block) |
| range | The IP address range in CIDR notation (e.g., 0.0.0.0/0, 10.0.0.0/16) |

#### Relationships

- AWSIpRanges belong to AWS Accounts.
    ```
    (AWSAccount)-[RESOURCE]->(AWSIpRange)
    ```

- AWSIpRanges are members of AWSIpRules.
    ```
    (AWSIpRange)-[MEMBER_OF_IP_RULE]->(AWSIpRule)
    ```


### AWSLoadBalancer

```{important}
**Label Rename:** In previous versions, Classic ELB nodes used the label `:LoadBalancer`. This has been renamed to `:AWSLoadBalancer` for consistency with other AWS resources.

**Semantic Label:** All load balancers (AWS, GCP, Azure) now also have the `:LoadBalancer` label for cross-platform queries.

**Migration:** Existing nodes are automatically relabeled on upgrade.
```

Represents a classic [AWS Elastic Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).  See [spec for details](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).

> **Ontology Mapping**: This node has the extra label `LoadBalancer` to enable cross-platform queries for load balancers across different systems (e.g., AWSLoadBalancerV2, GCPForwardingRule, AzureLoadBalancer).

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

### AWSLoadBalancerV2

```{important}
**Label Rename:** In previous versions, ALB/NLB nodes used the label `:LoadBalancerV2`. This has been renamed to `:AWSLoadBalancerV2` for consistency with other AWS resources.

**Semantic Label:** All load balancers (AWS, GCP, Azure) now also have the `:LoadBalancer` label for cross-platform queries.

**Migration:** Existing nodes are automatically relabeled on upgrade.
```

Represents an Elastic Load Balancer V2 ([Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) or [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html).) API reference [here](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancer.html).

> **Ontology Mapping**: This node has the extra label `LoadBalancer` to enable cross-platform queries for load balancers across different systems (e.g., AWSLoadBalancer, GCPForwardingRule, AzureLoadBalancer).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| scheme|  The type of load balancer.  If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| name| The name of the load balancer|
| **dnsname** | The DNS name of the load balancer. |
| exposed_internet | The `exposed_internet` flag is set to `True` when the load balancer's `scheme` field is set to `internet-facing`.  This indicates that the load balancer has a public DNS name that resolves to a public IP address. |
| exposed\_internet\_type | A list indicating the type(s) of internet exposure. Set by the `aws_ec2_asset_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/aws_ec2_asset_exposure.json). |
| **id** |  Currently set to the `dnsname` of the load balancer. |
| arn | The Amazon Resource Name (ARN) of the load balancer. |
| type | Can be `application` or `network` |
| region| The region of the load balancer |
|createdtime | The date and time the load balancer was created. |
|canonicalhostedzonenameid| The ID of the Amazon Route 53 hosted zone for the load balancer. |


#### Relationships


- AWSLoadBalancerV2's can be connected to EC2Instances and therefore expose them.
    ```
    (AWSLoadBalancerV2)-[EXPOSE]->(EC2Instance)
    ```

- AWSLoadBalancerV2's can expose IP addresses when using `ip` target type.
    ```
    (AWSLoadBalancerV2)-[EXPOSE]->(EC2PrivateIp)
    ```

- AWSLoadBalancerV2's can expose Lambda functions when using `lambda` target type.
    ```
    (AWSLoadBalancerV2)-[EXPOSE]->(AWSLambda)
    ```

- AWSLoadBalancerV2's can chain to other AWSLoadBalancerV2's when using `alb` target type (ALB-to-ALB chaining).
    ```
    (AWSLoadBalancerV2)-[EXPOSE]->(AWSLoadBalancerV2)
    ```

The `EXPOSE` relationship holds the protocol, port and TargetGroupArn the load balancer points to.

- AWSLoadBalancerV2's can be part of EC2SecurityGroups but only if their `type` = "application". NLBs don't have SGs.
    ```
    (AWSLoadBalancerV2)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    ```

- AWSLoadBalancerV2's can be part of EC2 Subnets
    ```
    (AWSLoadBalancerV2)-[SUBNET]->(EC2Subnet)
    ```

- AWSLoadBalancerV2's can be part of EC2 Subnets
    ```
    (AWSLoadBalancerV2)-[PART_OF_SUBNET]->(EC2Subnet)
    ```

- AWSLoadBalancerV2's have [listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html):
    ```
    (AWSLoadBalancerV2)-[ELBV2_LISTENER]->(ELBV2Listener)
    ```

- Internet-facing AWSLoadBalancerV2's can expose private ECS containers. Set by an analysis job.
    ```
    (AWSLoadBalancerV2)-[EXPOSE]->(ECSContainer)
    ```

- EC2NetworkAcl's can protect AWSLoadBalancerV2's via subnet traversal. Set by an analysis job.
    ```
    (EC2NetworkAcl)-[PROTECTS]->(AWSLoadBalancerV2)
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
| **id** | The ID of the network interface.  (known as `networkInterfaceId` in EC2) |
| **mac\_address**| The MAC address of the network interface|
| **private\_ip\_address**| The primary IPv4 address of the network interface within the subnet |
| description |  Description of the network interface|
| private\_dns\_name| The private DNS name |
| region | The AWS region |
| status | Status of the network interface.  Valid Values: ``available \| associated \| attaching \| in-use \| detaching `` |
| **subnetid** | The ID of the subnet |
| **subnet_id** | The ID of the subnet |
| interface_type  |  Describes the type of network interface. Valid values: `` interface \| efa `` |
| **requester_id**  | Id of the requester, e.g. `amazon-elb` for ELBs |
| requester_managed  |  Indicates whether the interface is managed by the requester |
| source_dest_check   | Indicates whether to validate network traffic to or from this network interface.  |
| **public_ip**   | Public IPv4 address attached to the interface  |
| attach_time | The timestamp when the network interface was attached to an EC2 instance. For primary interfaces (device_index=0), this reveals the first launch time of the instance [according to AWS](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html). |
| device_index | The index of the device on the instance for the network interface attachment. A value of `0` indicates the primary (eth0) network interface, which is created when the instance is launched. |

#### Usage Notes

**Finding the True First Launch Time:**

The `LaunchTime` field on EC2Instance nodes shows the *last* launch time (e.g., if an instance was stopped and restarted). To find when an instance was *originally* created, use the `attach_time` of the primary network interface (`device_index: 0`):

```cypher
// Get the true first launch time for EC2 instances
MATCH (i:EC2Instance)-[:NETWORK_INTERFACE]->(ni:NetworkInterface {device_index: 0})
WHERE ni.attach_time IS NOT NULL
RETURN i.instanceid, i.launchtime as last_launch, ni.attach_time as first_launch
```

**Primary vs Secondary Interfaces:**
- **Primary interfaces** (`device_index: 0`): Created when the instance is launched, cannot be detached. The `attach_time` represents the instance's original creation time.
- **Secondary interfaces** (`device_index: 1+`): Can be attached and detached at any time. The `attach_time` represents when the secondary interface was attached, not when the instance was created.

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

- AWSLoadBalancerV2s can have NetworkInterfaces connected to them.
    ```
    (AWSLoadBalancerV2)-[NETWORK_INTERFACE]->(NetworkInterface)
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

- AWSPrincipals with appropriate permissions can administer Redshift clusters. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).
    ```
    (AWSPrincipal)-[CAN_ADMINISTER]->(RedshiftCluster)
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

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for database instances across different systems (e.g., AzureSQLDatabase, GCPBigtableInstance).

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

### RDSEventSubscription

Representation of an AWS Relational Database Service [EventSubscription](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_EventSubscription.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The customer subscription identifier |
| **arn** | The Amazon Resource Name (ARN) for the event subscription |
| customer_aws_id | The AWS customer account associated with the event subscription |
| sns_topic_arn | The ARN of the SNS topic to which notifications are sent |
| source_type | The type of source that is generating the events (db-instance, db-cluster, db-snapshot) |
| status | The status of the event subscription (active, inactive) |
| enabled | Whether the event subscription is enabled |
| subscription_creation_time | The time the event subscription was created |
| event_categories | List of event categories for which to receive notifications |
| source_ids | List of source identifiers for which to receive notifications |
| region | The AWS region where the event subscription is located |

#### Relationships

- RDS Event Subscriptions are part of AWS Accounts.
    ```
    (AWSAccount)-[:RESOURCE]->(RDSEventSubscription)
    ```

- RDS Event Subscriptions send notifications to SNS Topics.
    ```
    (RDSEventSubscription)-[:NOTIFIES]->(SNSTopic)
    ```

- RDS Event Subscriptions monitor RDS Instances.
    ```
    (RDSEventSubscription)-[:MONITORS]->(RDSInstance)
    ```

- RDS Event Subscriptions monitor RDS Clusters.
    ```
    (RDSEventSubscription)-[:MONITORS]->(RDSCluster)
    ```

- RDS Event Subscriptions monitor RDS Snapshots.
    ```
    (RDSEventSubscription)-[:MONITORS]->(RDSSnapshot)
    ```

### ElasticacheCluster

Representation of an AWS [ElastiCache Cluster](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CacheCluster.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the ElastiCache cluster |
| cache_cluster_id | The unique identifier for the cache cluster |
| cache_node_type | The compute and memory capacity of the nodes in the cluster |
| engine | The name of the cache engine (redis, memcached) |
| engine_version | The version of the cache engine |
| cache_cluster_status | The current state of the cache cluster |
| num_cache_nodes | The number of cache nodes in the cluster |
| preferred_availability_zone | The name of the Availability Zone in which the cache cluster is located |
| preferred_maintenance_window | The weekly time range during which maintenance on the cache cluster is performed |
| cache_cluster_create_time | The date and time when the cache cluster was created |
| cache_subnet_group_name | The name of the cache subnet group associated with the cache cluster |
| auto_minor_version_upgrade | Indicates whether minor version patches are applied automatically |
| replication_group_id | The replication group to which this cache cluster belongs |
| snapshot_retention_limit | The number of days for which ElastiCache will retain automatic cache cluster snapshots |
| snapshot_window | The daily time range during which ElastiCache will take a snapshot of the cache cluster |
| auth_token_enabled | Indicates whether an authentication token is enabled for the cache cluster |
| transit_encryption_enabled | Indicates whether the cache cluster is encrypted in transit |
| at_rest_encryption_enabled | Indicates whether the cache cluster is encrypted at rest |
| topic_arn | The ARN of the SNS topic to which notifications are sent |
| region | The AWS region where the cache cluster is located |

#### Relationships

- ElastiCache clusters are part of AWS Accounts.
    ```
    (:AWSAccount)-[:RESOURCE]->(:ElasticacheCluster)
    ```

- ElastiCache topics are associated with ElastiCache clusters.
    ```
    (:ElasticacheTopic)-[:CACHE_CLUSTER]->(:ElasticacheCluster)
    ```

### ElasticacheTopic

Representation of an AWS [ElastiCache Topic](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CacheCluster.html) for notifications.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Same as ARN |
| **arn** | The Amazon Resource Name (ARN) for the SNS topic |
| status | The status of the SNS topic (active, inactive) |

#### Relationships

- ElastiCache topics are part of AWS Accounts.
    ```
    (:AWSAccount)-[:RESOURCE]->(:ElasticacheTopic)
    ```

- ElastiCache topics are associated with ElastiCache clusters.
    ```
    (:ElasticacheTopic)-[:CACHE_CLUSTER]->(:ElasticacheCluster)
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

> **Ontology Mapping**: This node has the extra label `ObjectStorage` to enable cross-platform queries for object storage across different systems (e.g., GCPBucket, AzureStorageBlobContainer).

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
| logging_enabled | True if this bucket has [logging enabled](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketLogging.html) enabled. |
| logging_target_bucket | The name of the target bucket where access logs are stored. Only defined if logging is enabled. |

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

- S3 Buckets can send notifications to SNS Topics.
    ```
    (S3Bucket)-[NOTIFIES]->(SNSTopic)
    ```

- AWSPrincipals with appropriate permissions can read from S3 buckets. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).
    ```
    (AWSPrincipal)-[CAN_READ]->(S3Bucket)
    ```

- AWSPrincipals with appropriate permissions can write to S3 buckets. Created from [permission_relationships.yaml](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/permission_relationships.yaml).
    ```
    (AWSPrincipal)-[CAN_WRITE]->(S3Bucket)
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
| lastupdated |  Timestamp of the last time the node was updated by Cartography |
| **id** | The KeyId of the key|
| **arn** |  The ARN of the key |
| **key_id** |  The KeyId of the key |
| description |  The description of the key |
| enabled |  Whether the key is enabled |
| key_state |  The current state of the key (e.g., Enabled, Disabled, PendingDeletion) |
| key_usage |  The permitted use of the key (e.g., ENCRYPT_DECRYPT, SIGN_VERIFY) |
| key_manager |  The manager of the key (AWS or CUSTOMER) |
| origin |  The source of the key material (AWS_KMS, EXTERNAL, AWS_CLOUDHSM) |
| creation_date |  The date the key was created |
| deletion_date |  The date the key is scheduled for deletion |
| valid_to |  The expiration date for the key material |
| custom_key_store_id |  The ID of the custom key store that contains the key |
| cloud_hsm_cluster_id |  The cluster ID of the AWS CloudHSM cluster that contains the key material |
| expiration_model |  Specifies whether key material expires |
| customer_master_key_spec |  The type of key material in the CMK |
| encryption_algorithms |  The encryption algorithms that AWS KMS supports for this key |
| signing_algorithms |  The signing algorithms that AWS KMS supports for this key |
| region | The region where key is created|
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the key. |
| anonymous\_access | True if this key has a policy applied to it that allows anonymous access or if it is open to the internet. |

#### Relationships

- AWS KMS Keys are resources in an AWS Account.
    ```
    (AWSAccount)-[:RESOURCE]->(KMSKey)
    ```

- AWS KMS Key may also be referred as KMSAlias via aliases.
    ```
    (KMSAlias)-[:KNOWN_AS]->(KMSKey)
    ```

- AWS KMS Key may also have KMSGrant based on grants.
    ```
    (KMSGrant)-[:APPLIED_ON]->(KMSKey)
    ```

### KMSAlias

Representation of an AWS [KMS Key Alias](https://docs.aws.amazon.com/kms/latest/APIReference/API_AliasListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated by Cartography |
| **id** | The ARN of the alias|
| **arn** |  The ARN of the alias |
| **alias_name** |  The name of the alias |
| target_key_id |  The KMS key id associated via this alias |
| creation_date |  The date the alias was created |
| last_updated_date |  The date the alias was last updated by AWS |
| region |  The AWS region where the alias is located |

#### Relationships

- AWS KMS Aliases belong to AWS Accounts.
    ```
    (AWSAccount)-[:RESOURCE]->(KMSAlias)
    ```

- AWS KMS Key may also be referred as KMSAlias via aliases.
    ```
    (KMSAlias)-[KNOWN_AS]->(KMSKey)
    ```

### KMSGrant

Representation of an AWS [KMS Key Grant](https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantListEntry.html).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of when the node was last updated by Cartography |
| **id** | The unique identifier of the key grant |
| **grant_id** | The grant identifier (indexed for performance) |
| name | The name of the key grant |
| grantee_principal | The principal associated with the key grant |
| creation_date | Epoch timestamp when the grant was created |
| key_id | The key identifier that the grant applies to |
| issuing_account | The AWS account that issued the grant |
| operations | List of operations that the grant allows |

#### Relationships

- AWS KMS Grants are resources in an AWS Account.
    ```
    (AWSAccount)-[:RESOURCE]->(KMSGrant)
    ```

- AWS KMS Grants are applied to KMS Keys.
    ```
    (KMSGrant)-[:APPLIED_ON]->(KMSKey)
    ```

### APIGatewayRestAPI

Representation of an AWS [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/api/API_GetRestApis.html).

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
| anonymous\_actions |  List of anonymous internet accessible actions that may be run on the API (policy-level). |
| anonymous\_access | True if this API has a resource policy that allows anonymous/public access (policy-level analysis via PolicyUniverse). |
| **endpoint\_type** | The endpoint configuration type: `EDGE` (CloudFront), `REGIONAL` (direct), or `PRIVATE` (VPC-only). |
| **exposed\_internet** | True if the API is network-reachable from the internet (`EDGE` or `REGIONAL`), false for `PRIVATE` endpoints. |

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
| **id** | The ARN of the API Gateway Stage |
| stagename | The name of the API Gateway Stage |
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

### APIGatewayDeployment

Representation of an AWS [API Gateway Deployment](https://docs.aws.amazon.com/apigateway/latest/api/API_GetDeployments.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The identifier for the deployment resource as string of api id and deployment id |
| **arn** | The identifier for the deployment resource. |
| description | The description for the deployment resource. |
| region |  The region for the deployment resource. |

#### Relationships

- AWS API Gateway Deployments are resources in an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(APIGatewayDeployment)
    ```
- AWS API Gateway REST APIs have deployments API Gateway Deployments.
    ```
    (APIGatewayRestAPI)-[HAS_DEPLOYMENT]->(APIGatewayDeployment)
    ```

### ACMCertificate

Representation of an AWS [ACM Certificate](https://docs.aws.amazon.com/acm/latest/APIReference/API_CertificateDetail.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the certificate |
| **arn** | The Amazon Resource Name (ARN) of the certificate |
| region | The AWS region where the certificate is located |
| domainname | The primary domain name of the certificate |
| status | The status of the certificate |
| type | The source of the certificate |
| key_algorithm | The key algorithm used |
| signature_algorithm | The signature algorithm |
| not_before | The time before which the certificate is invalid |
| not_after | The time after which the certificate expires |
| in_use_by | List of ARNs of resources that use this certificate |

#### Relationships

- ACM Certificates are resources under the AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:ACMCertificate)
    ```
- ACM Certificates may be used by ELBV2Listeners.
    ```
    (:ACMCertificate)-[:USED_BY]->(:ELBV2Listener)
    ```
  Note: the AWS ACM API may return a load balancer ARN for the `in_use_by` field instead of a listener ARN. To properly map the certificate to the listener in this situation, we need to rely on data from the ELBV2 module. This is a weird quirk of the AWS API.

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

### APIGatewayMethod

Representation of an AWS [API Gateway Method](https://docs.aws.amazon.com/apigateway/latest/api/API_GetMethod.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id represented as ApiId/ResourceId/HttpMethod |
| httpmethod |  The method's HTTP verb |
| resource_id |  Identifier for respective resource |
| api_id |  The  identifier for the API |
| authorization_type | The method's authorization type |
| authorizer_id |  The identifier of an authorizer to use on this method |
| operation_name |  A human-friendly operation identifier for the method |
| request_validator_id |  The identifier of a RequestValidator for request validation |
| api_key_required |  A boolean flag specifying whether a valid ApiKey is required to invoke this method |

#### Relationships

- AWS API Gateway Methods are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(APIGatewayMethod)
    ```
- AWS API Gateway Methods are attached to API Gateway Resource .
    ```
    (APIGatewayResource)-[HAS_METHOD]->(APIGatewayMethod)
    ```

### APIGatewayIntegration

Representation of an AWS [API Gateway Integration](https://docs.aws.amazon.com/apigateway/latest/api/API_GetIntegration.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id represented as ApiId/ResourceId/HttpMethod |
| httpmethod |  Specifies a get integration request's HTTP method |
| integration_http_method | Specifies the integration's HTTP method type |
| resource_id |  Identifier for respective resource |
| api_id |  The  identifier for the API |
| type | Specifies an API method integration type |
| uri |  Specifies Uniform Resource Identifier (URI) of the integration endpoint |
| connection_type |  The type of the network connection to the integration endpoint |
| connection_id |  The ID of the VpcLink used for the integration when connectionType=VPC_LINK and undefined, otherwise |
| credentials |  Specifies the credentials required for the integration, if any |

#### Relationships

- AWS API Gateway Integrations are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(APIGatewayIntegration)
    ```
- AWS API Gateway Integrations are attached to API Gateway Resource .
    ```
    (APIGatewayResource)-[HAS_INTEGRATION]->(APIGatewayIntegration)
    ```

### APIGatewayV2API

Representation of an AWS [API Gateway v2 API](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis.html#apisget).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The id of the API|
| name | The name of the API |
| description | The description of the API |
| protocoltype | The protocol type (HTTP or WEBSOCKET) |
| routeselectionexpression | Expression for selecting routes |
| apikeyselectionexpression | Expression for selecting API keys |
| apiendpoint | The endpoint URL of the API |
| version | The version identifier for the API |
| createddate | The timestamp when the API was created |
| region | The region where the API is created |

#### Relationships

- AWS API Gateway v2 APIs are resources in an AWS Account.
    ```
    (:AWSAccount)-[:RESOURCE]->(:APIGatewayV2API)
    ```

### AutoScalingGroup

Representation of an AWS [Auto Scaling Group Resource](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the Auto Scaling Group (same as arn) |
| **arn** | The ARN of the Auto Scaling Group |
| name |  The name of the Auto Scaling group |
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
| exposed\_internet | Set to `True` if any EC2 instance in this Auto Scaling Group is exposed to the internet. Set by the `aws_ec2_asset_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/aws_ec2_asset_exposure.json). |
| exposed\_internet\_type | A list indicating the type(s) of internet exposure inherited from the EC2 instances in the group. Possible values are `direct`, `elb`, or `elbv2`. Set by the `aws_ec2_asset_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/aws_ec2_asset_exposure.json). |


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
| **name** | The name of the AMI that was provided during image creation. |
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

> **Ontology Mapping**: This node has the extra label `Secret` and normalized `_ont_*` properties for cross-platform secret queries. See [Secret](../../ontology/schema.md#secret).

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
| **name** | The friendly name of the secret. You can use forward slashes in the name to represent a path hierarchy. For example, /prod/databases/dbserver1 could represent the secret for a server named dbserver1 in the folder databases in the folder prod. |
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
- If the secret is encrypted with a KMS key, it has a relationship to that key.
    ```
    (SecretsManagerSecret)-[ENCRYPTED_BY]->(KMSKey)
    ```

### EBSVolume

Representation of an AWS [EBS Volume](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volumes.html).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ID of the EBS Volume (same as volumeid) |
| **arn** | The Amazon Resource Name (ARN) of the volume |
| **volumeid** | The ID of the EBS Volume |
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
| **snapshotid** | The snapshot ID.|
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
| **arn** | The arn of the sqs queue. |
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
| **id** | The ID of the launch template (same as launch_template_id) |
| launch\_template\_id | The ID of the launch template |
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

- AWSDNSRecords can point to ElasticIPAddresses
    ```
    (AWSDNSRecord)-[DNS_POINTS_TO]->(ElasticIPAddress)
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
| **arn** | The ARN of the cluster |
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
    (:AWSAccount)-[:RESOURCE]->(:ECSCluster)
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
| **arn** | The ARN of the container instance |
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
    (:ECSCluster)-[:HAS_CONTAINER_INSTANCE]->(:ECSContainerInstance)
    ```

- ECSContainerInstances have ECSTasks
    ```
    (:ECSContainerInstance)-[:HAS_TASK]->(:ECSTask)
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
| **arn** | The ARN of the service |
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
    (:ECSCluster)-[:HAS_SERVICE]->(:ECSService)
    ```

- An ECSService has ECSTasks
    ```
    (:ECSService)-[:HAS_TASK]->(:ECSTask)
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
    (:AWSAccount)-[:RESOURCE]->(:ECSTaskDefinition)
    ```

- An ECSTask has an ECSTaskDefinition.
    ```
    (:ECSTask)-[:HAS_TASK_DEFINITION]->(:ECSTaskDefinition)
    ```

- ECSTaskDefinitions have task roles.
    ```
    (:ECSTaskDefinition)-[:HAS_TASK_ROLE]->(:AWSRole)
    ```

- ECSTaskDefinitions have execution roles.
    ```
    (:ECSTaskDefinition)-[:HAS_EXECUTION_ROLE]->(:AWSRole)
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
    (:ECSTaskDefinition)-[:HAS_CONTAINER_DEFINITION]->(:ECSContainerDefinition)
    ```

### ECSTask

Representation of an AWS ECS [Task](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Task.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the task |
| region | The region of the task. |
| **arn** | The arn of the task. |
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
| network\_interface\_id | The network interface ID for tasks running in awsvpc network mode. |

#### Relationships

- ECSTasks are a resource under the AWS Account
    ```
    (:AWSAccount)-[:RESOURCE]->(:ECSTask)
    ```

- ECSClusters have ECSTasks
    ```
    (:ECSCluster)-[:HAS_TASK]->(:ECSTask)
    ```

- ECSContainerInstances have ECSTasks
    ```
    (:ECSContainerInstance)-[:HAS_TASK]->(:ECSTask)
    ```

- ECSTasks have ECSTaskDefinitions
    ```
    (:ECSTask)-[:HAS_TASK_DEFINITION]->(:ECSTaskDefinition)
    ```

- ECSTasks in awsvpc network mode have NetworkInterfaces
    ```
    (:ECSTask)-[:NETWORK_INTERFACE]->(:NetworkInterface)
    ```

### ECSContainer

Representation of an AWS ECS [Container](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Container.html)

> **Ontology Mapping**: This node has the extra label `Container` to enable cross-platform queries for container instances across different systems (e.g., KubernetesContainer, AzureContainerInstance).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | The ARN of the container |
| region | The region of the container. |
| **arn** | The arn of the container. |
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
| exposed\_internet | Set to `True` if this container is exposed to the internet via an internet-facing load balancer. Set by the `aws_ecs_asset_exposure` [analysis job](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/analysis/aws_ecs_asset_exposure.json). |

#### Relationships

- ECSTasks have ECSContainers
    ```
    (:ECSTask)-[:HAS_CONTAINER]->(:ECSContainer)
    ```

- ECSContainers have images.
    ```
    (:ECSContainer)-[:HAS_IMAGE]->(:ECRImage)
    ```

### EfsFileSystem
Representation of an AWS [EFS File System](https://docs.aws.amazon.com/efs/latest/ug/API_FileSystemDescription.html)
| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ID of the file system, assigned by Amazon EFS |
| **arn** | Amazon Resource Name (ARN) for the EFS file system |
| region | The region of the file system |
| owner_id | The AWS account that created the file system |
| creation_token | The opaque string specified in the request |
| creation_time | The time that the file system was created, in seconds |
| lifecycle_state | The lifecycle phase of the file system |
| name | If the file system has a name tag, Amazon EFS returns the value in this field |
| number_of_mount_targets | The current number of mount targets that the file system has |
| size_in_bytes_value | Latest known metered size (in bytes) of data stored in the file system |
| size_in_bytes_timestamp | Time at which that size was determined |
| performance_mode | The performance mode of the file system |
| encrypted | A Boolean value that, if true, indicates that the file system is encrypted |
| kms_key_id | The ID of an AWS KMS key used to protect the encrypted file system |
| throughput_mode | Displays the file system's throughput mode |
| availability_zone_name | Describes the AWS Availability Zone in which the file system is located |
| availability_zone_id | The unique and consistent identifier of the Availability Zone in which the file system is located |
| file_system_protection | Describes the protection on the file system |

#### Relationships
- EfsFileSystem are a resource under the AWS Account.
   ```
   (AWSAccount)-[RESOURCE]->(EfsFileSystem)
   ```

### EfsMountTarget
Representation of an AWS [EFS Mount Target](https://docs.aws.amazon.com/efs/latest/ug/API_MountTargetDescription.html)
| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | System-assigned mount target ID |
| **arn** | System-assigned mount target ID |
| region | The region of the mount target |
| fileSystem_id | The ID of the file system for which the mount target is intended |
| lifecycle_state | Lifecycle state of the mount target |
| mount_target_id | System-assigned mount target ID |
| subnet_id | The ID of the mount target's subnet |
| availability_zone_id | The unique and consistent identifier of the Availability Zone that the mount target resides in |
| availability_zone_name | The name of the Availability Zone in which the mount target is located |
| ip_address | Address at which the file system can be mounted by using the mount target |
| network_interface_id | The ID of the network interface that Amazon EFS created when it created the mount target |
| owner_id | AWS account ID that owns the resource |
| vpc_id | The virtual private cloud (VPC) ID that the mount target is configured in |
#### Relationships
- Efs MountTargets are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EfsMountTarget)
    ```
- Efs MountTargets are attached to Efs FileSystems.
    ```
    (EfsMountTarget)-[ATTACHED_TO]->(EfsFileSystem)
    ```

### EfsAccessPoint
Representation of an AWS [EFS Access Point](https://docs.aws.amazon.com/efs/latest/ug/API_AccessPointDescription.html)
| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | System-assigned access point ARN |
| **arn** | The unique Amazon Resource Name (ARN) associated with the access point |
| region | The region of the access point |
|access_point_id | The ID of the access point, assigned by Amazon EFS |
| file_system_id | The ID of the EFS file system that the access point applies to |
| lifecycle_state | Identifies the lifecycle phase of the access point |
| name | The name of the access point |
| owner_id | AWS account ID that owns the resource |
| posix_gid | The POSIX group ID used for all file system operations using this access point |
| posix_uid | The POSIX user ID used for all file system operations using this access point |
| root_directory_path | Specifies the path on the EFS file system to expose as the root directory to NFS clients using the access point to access the EFS file system |
#### Relationships
- Efs AccessPoints are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(EfsAccessPoint)
    ```
- EFS Access Points are entry points into EFS File Systems.
    ```
    (EfsAccessPoint)-[ACCESS_POINT_OF]->(EfsFileSystem)
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

### SNSTopicSubscription
Representation of an AWS [SNS Topic Subscription](https://docs.aws.amazon.com/sns/latest/api/API_GetSubscriptionAttributes.html)

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the SNS topic subscription |
| **arn** | The Amazon Resource Name (ARN) of the topic subscription |
| topic_arn | The topic ARN that the subscription is associated with |
| endpoint | The subscription's endpoint |
| owner | The subscription's owner |
| protocol | The subscription's protocol for messages |
#### Relationships
- SNS Topic Subscriptions are a resource under the AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(SNSTopicSubscription)
    ```
- SNS Topic Subscriptions are associated with SNS Topics.
    ```
    (:SNSTopicSubscription)-[HAS_SUBSCRIPTION]->(:SNSTopic)
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
| **instance\_id** | The managed node ID. |
| **title** | The title of the patch. |
| **kb\_id** | The operating system-specific ID of the patch. |
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
| **arn** | The Amazon Resource Name (ARN) of the parameter. |
| name | The parameter name. |
| description | Description of the parameter actions. |
| type | The type of parameter. Valid parameter types include String, StringList, and SecureString. |
| keyid | The alias or ARN of the Key Management Service (KMS) key used to encrypt the parameter. Applies to SecureString parameters only. |
| kms_key_id_short | The shortened KMS Key ID used to encrypt the parameter. |
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
| arn | The Amazon Resource Name (ARN) of the Identity Center instance |
| status | The status of the Identity Center instance |
| identity_store_id | The identity store ID of the Identity Center instance |
| instance_status | The status of the Identity Center instance |
| created_date | The date the Identity Center instance was created |
| last_modified_date | The date the Identity Center instance was last modified |
| region | The AWS region where the Identity Center instance is located |

#### Relationships
- An AWSIdentityCenter instance is part of an AWSAccount.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AWSIdentityCenter)
    ```

- AWSIdentityCenter instance has permission sets.
    ```
    (:AWSIdentityCenter)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
    ```

- Entra service principals can federate to AWS Identity Center via SAML

    ```cypher
    (:EntraServicePrincipal)-[:FEDERATES_TO]->(:AWSIdentityCenter)
    ```

### AWSSSOUser

Representation of an AWS SSO User.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GitHubUser).

> **Cross-Platform Integration**: AWSSSOUser nodes can be federated with external identity providers like Okta, Entra (Azure AD), and others. See the complete Okta → AWS SSO → AWS Role relationship path documentation in the [Okta Schema](../okta/schema.md#cross-platform-integration-okta-to-aws).

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the SSO user |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| user_name | The username of the SSO user |
| **external_id** | The external ID of the SSO user |
| identity_store_id | The identity store ID of the SSO user |
| region | The AWS region |

#### Relationships
- AWSSSOUser is part of an AWSAccount.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AWSSSOUser)
    ```

- An AWSSSOUser can be a member of one or more AWSSSOGroups. In effect, the AWSSSOUser will receive all permission sets that the group is assigned to.
    ```
    (:AWSSSOUser)-[:MEMBER_OF_SSO_GROUP]->(:AWSSSOGroup)
    ```

- AWSSSOUsers can be assigned to AWSRoles. This happens when the user is assigned to a permission set for a specific account. This includes both direct assignments to the user and assignments inherited through AWSSSOGroup membership. Note: The AWS Identity Center API (`list_account_assignments_for_principal`) automatically resolves group memberships server-side, so users receive `ALLOWED_BY` relationships for roles they can access through groups they belong to.
    ```
    (:AWSSSOUser)<-[:ALLOWED_BY]-(:AWSRole)
    ```

- OktaUsers can assume AWS SSO users via SAML federation
     ```
    (:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
    ```
    More generically, user accounts can assume AWS SSO users via SAML federation.
    ```
    (:UserAccount)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
    ```

- An AWSSSOUser can be assigned to one or more AWSPermissionSets. This includes both direct assignments and assignments inherited through AWSSSOGroup membership.
    ```
    (:AWSSSOUser)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
    ```
    Notes:
    - The AWS Identity Center API (`list_account_assignments_for_principal`) automatically resolves group memberships server-side, so users receive `HAS_PERMISSION_SET` relationships for permission sets they have access to through groups they belong to. This means if a user is only in a group that has a permission set assignment, the user will still have a direct `HAS_PERMISSION_SET` relationship to that permission set.
    - This is a **summary relationship** that does not indicate which specific accounts the user has access to, only that they have been assigned to the permission set. For a user to have access to an AWS account, they must be assigned to a permission set for that specific account. This is captured by the `ALLOWED_BY` relationship.

- AWSSSOUser can assume AWS roles via SAML (recorded from CloudTrail management events).
    ```
    (:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML {times_used, first_seen_in_time_window, last_used, lastupdated}]->(:AWSRole)
    ```
    This relationship is created by analyzing CloudTrail `AssumeRoleWithSAML` events. The relationship properties track:
    - `times_used`: Number of times the role was assumed during the lookback window
    - `first_seen_in_time_window`: Earliest assumption time in the lookback window
    - `last_used`: Most recent assumption time
    - `lastupdated`: When this relationship was last updated by Cartography

    Note: This relationship represents **actual role usage** (what roles were assumed), while `ALLOWED_BY` represents **permitted access** (what roles can be assumed based on permission set assignments).

- Entra users can sign on to AWSSSOUser via SAML federation through AWS Identity Center. See https://docs.aws.amazon.com/singlesignon/latest/userguide/idp-microsoft-entra.html and https://learn.microsoft.com/en-us/entra/identity/saas-apps/aws-single-sign-on-tutorial.
    ```
    (:EntraUser)-[:CAN_SIGN_ON_TO]->(:AWSSSOUser)
    ```

### AWSSSOGroup

Representation of an AWS SSO Group.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the SSO group |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| display_name | The display name of the SSO group |
| description | The description of the SSO group |
| **external_id** | The external ID of the SSO group |
| identity_store_id | The identity store ID of the SSO group |
| region | The AWS region |

#### Relationships
- AWSSSOGroup is part of an AWSAccount.
    ```
    (:AWSAccount)-[:RESOURCE]->(:AWSSSOGroup)
    ```

- An AWSSSOGroup can have roles assigned. This happens if the group is assigned to a permission set for a specific account.
    ```
    (:AWSSSOGroup)<-[:ALLOWED_BY]-(:AWSRole)
    ```

- An AWSSSOGroup has assigned permission sets. AWSSSOUsers in the group will receive all permission sets that the group is assigned to.
    ```
    (:AWSSSOGroup)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
    ```
    Notes:
    - This relationship does not indicate which accounts the group has access to, only that it has been assigned to the permission set. For a group to have access to an AWS account, it must be assigned to a permission set for that specific account. This is captured by the `ALLOWED_BY` relationship.
    - The AWS Identity Center API (`list_account_assignments_for_principal`) automatically resolves group memberships server-side, so users receive `HAS_PERMISSION_SET` relationships for permission sets they have access to through groups they belong to. This means if a user is only in a group that has a permission set assignment, the user will still have a direct `HAS_PERMISSION_SET` relationship to that permission set.

- AWSSSOUsers can be members of AWSSSOGroups. In effect, the AWSSSOUser will receive all permission sets that the group is assigned to.
    ```
    (:AWSSSOUser)-[:MEMBER_OF_SSO_GROUP]->(:AWSSSOGroup)
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
| region | The AWS region where the Permission Set is located |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- An AWSPermissionSet is part of an AWSIdentityCenter instance.
    ```
    (:AWSIdentityCenter)<-[:HAS_PERMISSION_SET]-(:AWSPermissionSet)
    ```

- An AWSPermissionSet creates AWSRoles in all of the AWS accounts that its associated permission set assigns it to.
    ```
    (:AWSPermissionSet)-[:ASSIGNED_TO_ROLE]->(:AWSRole)
    ```

- An AWSSSOUser can be assigned to one or more AWSPermissionSets. This includes both direct assignments and assignments inherited through AWSSSOGroup membership.
    ```
    (:AWSSSOUser)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
    ```
    Notes:
    - The AWS Identity Center API (`list_account_assignments_for_principal`) automatically resolves group memberships server-side, so users receive `HAS_PERMISSION_SET` relationships for permission sets they have access to through groups they belong to. This means if a user is only in a group that has a permission set assignment, the user will still have a direct `HAS_PERMISSION_SET` relationship to that permission set.
    - This is a **summary relationship** that does not indicate which specific accounts the user has access to, only that they have been assigned to the permission set. For a user to have access to an AWS account, they must be assigned to a permission set _for that specific account_. This is captured by the `ALLOWED_BY` relationship.

- An AWSSSOGroup has assigned permission sets. AWSSSOUsers in the group will receive all permission sets that the group is assigned to.
    ```
    (:AWSSSOGroup)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)
    ```
    Note: This relationship does not indicate which accounts the group has access to, only that it has been assigned to the permission set. For a group to have access to an AWS account, it must be assigned to a permission set for that specific account. This is captured by the `ALLOWED_BY` relationship.

### EC2RouteTable

Representation of an AWS [EC2 Route Table](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RouteTable.html).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|
|**id**| The ID of the route table|
|**route_table_id**| The ID of the route table (same as id)|
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
|**route_table_association_id**| The ID of the route table association (same as id)|
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
|**id**| The ID of the route, formatted as `route_table_id\|destination_cidr\|target_components` where target components are prefixed with their type (e.g., gw-, nat-, pcx-) and joined with underscores.|
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
| **arn** | The ARN of the secret version. |
| secret_id | The ARN of the secret that this version belongs to. |
| version_id | The unique identifier of this version of the secret. |
| version_stages | A list of staging labels that are currently attached to this version of the secret. |
| created_date | The date and time that this version of the secret was created. |
| kms_key_ids | A list of IDs of the AWS KMS keys used to encrypt the secret version. |
| tags | A list of tags attached to this secret version. |
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
    (SecretsManagerSecretVersion)-[ENCRYPTED_BY]->(KMSKey)
    ```

### AWSBedrockFoundationModel

Representation of an AWS [Bedrock Foundation Model](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html). Foundation models are pre-trained large language models and multimodal models provided by AI companies like Anthropic, Amazon, Meta, and others.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the foundation model |
| arn | The ARN of the foundation model |
| model_id | The model identifier (e.g., "anthropic.claude-3-5-sonnet-20240620-v1:0") |
| model_name | The human-readable name of the model |
| provider_name | The provider of the model (e.g., "Anthropic", "Amazon", "Meta") |
| input_modalities | List of input modalities the model supports (e.g., ["TEXT", "IMAGE"]) |
| output_modalities | List of output modalities the model supports (e.g., ["TEXT"]) |
| response_streaming_supported | Whether the model supports streaming responses |
| customizations_supported | List of customization types supported (e.g., ["FINE_TUNING"]) |
| inference_types_supported | List of inference types supported (e.g., ["ON_DEMAND", "PROVISIONED"]) |
| model_lifecycle_status | The lifecycle status of the model (e.g., "ACTIVE", "LEGACY") |
| region | The AWS region where the model is available |

#### Relationships

- Foundation models are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockFoundationModel)
    ```

- Agents use foundation models for inference.
    ```
    (AWSBedrockAgent)-[USES_MODEL]->(AWSBedrockFoundationModel)
    ```

- Custom models can be based on foundation models.
    ```
    (AWSBedrockCustomModel)-[BASED_ON]->(AWSBedrockFoundationModel)
    ```

- Knowledge bases use foundation models for embeddings.
    ```
    (AWSBedrockKnowledgeBase)-[USES_EMBEDDING_MODEL]->(AWSBedrockFoundationModel)
    ```

- Guardrails can be applied to foundation models.
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockFoundationModel)
    ```

- Provisioned throughput provides capacity for foundation models.
    ```
    (AWSBedrockProvisionedModelThroughput)-[PROVIDES_CAPACITY_FOR]->(AWSBedrockFoundationModel)
    ```

### AWSBedrockCustomModel

Representation of an AWS [Bedrock Custom Model](https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html). Custom models are created through fine-tuning or continued pre-training of foundation models using customer-provided training data.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the custom model |
| arn | The ARN of the custom model |
| model_name | The name of the custom model |
| base_model_arn | The ARN of the foundation model this custom model is based on |
| creation_time | The timestamp when the custom model was created |
| job_name | The name of the training job that created this model |
| job_arn | The ARN of the training job |
| customization_type | The type of customization (e.g., "FINE_TUNING", "CONTINUED_PRE_TRAINING") |
| model_kms_key_arn | The KMS key ARN used to encrypt the custom model |
| training_data_s3_uri | The S3 URI of the training data |
| output_data_s3_uri | The S3 URI where training output is stored |
| region | The AWS region where the custom model exists |

#### Relationships

- Custom models are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockCustomModel)
    ```

- Custom models are based on foundation models.
    ```
    (AWSBedrockCustomModel)-[BASED_ON]->(AWSBedrockFoundationModel)
    ```

- Custom models are trained from data in S3 buckets.
    ```
    (AWSBedrockCustomModel)-[TRAINED_FROM]->(S3Bucket)
    ```

- Agents use custom models for inference.
    ```
    (AWSBedrockAgent)-[USES_MODEL]->(AWSBedrockCustomModel)
    ```

- Guardrails can be applied to custom models.
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockCustomModel)
    ```

- Provisioned throughput provides capacity for custom models.
    ```
    (AWSBedrockProvisionedModelThroughput)-[PROVIDES_CAPACITY_FOR]->(AWSBedrockCustomModel)
    ```

### AWSBedrockAgent

Representation of an AWS [Bedrock Agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html). Agents are autonomous AI assistants that can break down tasks, use tools (Lambda functions), and search knowledge bases to accomplish complex goals.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the agent |
| arn | The ARN of the agent |
| agent_id | The unique identifier of the agent |
| agent_name | The name of the agent |
| agent_status | The status of the agent (e.g., "CREATING", "PREPARED", "FAILED") |
| description | The description of the agent |
| instruction | The instructions that guide the agent's behavior |
| foundation_model | The ARN of the foundation or custom model the agent uses |
| agent_resource_role_arn | The ARN of the IAM role that the agent assumes |
| idle_session_ttl_in_seconds | The time in seconds before idle sessions expire |
| created_at | The timestamp when the agent was created |
| updated_at | The timestamp when the agent was last updated |
| prepared_at | The timestamp when the agent was last prepared |
| region | The AWS region where the agent exists |

#### Relationships

- Agents are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockAgent)
    ```

- Agents use foundation or custom models for inference.
    ```
    (AWSBedrockAgent)-[USES_MODEL]->(AWSBedrockFoundationModel)
    (AWSBedrockAgent)-[USES_MODEL]->(AWSBedrockCustomModel)
    ```

- Agents can use multiple knowledge bases for RAG (Retrieval Augmented Generation).
    ```
    (AWSBedrockAgent)-[USES_KNOWLEDGE_BASE]->(AWSBedrockKnowledgeBase)
    ```

- Agents can invoke Lambda functions as action groups (tools).
    ```
    (AWSBedrockAgent)-[INVOKES]->(AWSLambda)
    ```

- Agents assume IAM roles for permissions.
    ```
    (AWSBedrockAgent)-[HAS_ROLE]->(AWSRole)
    ```

- Guardrails can be applied to agents.
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockAgent)
    ```

### AWSBedrockKnowledgeBase

Representation of an AWS [Bedrock Knowledge Base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html). Knowledge bases enable RAG (Retrieval Augmented Generation) by converting documents from S3 into vector embeddings for semantic search.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the knowledge base |
| arn | The ARN of the knowledge base |
| knowledge_base_id | The unique identifier of the knowledge base |
| name | The name of the knowledge base |
| description | The description of the knowledge base |
| role_arn | The ARN of the IAM role that the knowledge base uses |
| status | The status of the knowledge base (e.g., "CREATING", "ACTIVE", "DELETING") |
| created_at | The timestamp when the knowledge base was created |
| updated_at | The timestamp when the knowledge base was last updated |
| region | The AWS region where the knowledge base exists |

#### Relationships

- Knowledge bases are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockKnowledgeBase)
    ```

- Knowledge bases source data from S3 buckets.
    ```
    (AWSBedrockKnowledgeBase)-[SOURCES_DATA_FROM]->(S3Bucket)
    ```

- Knowledge bases use embedding models to convert documents to vectors.
    ```
    (AWSBedrockKnowledgeBase)-[USES_EMBEDDING_MODEL]->(AWSBedrockFoundationModel)
    ```

- Agents use knowledge bases for RAG.
    ```
    (AWSBedrockAgent)-[USES_KNOWLEDGE_BASE]->(AWSBedrockKnowledgeBase)
    ```

### AWSBedrockGuardrail

Representation of an AWS [Bedrock Guardrail](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html). Guardrails provide content filtering, safety controls, and policy enforcement for models and agents by blocking harmful content and enforcing responsible AI usage.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the guardrail |
| arn | The ARN of the guardrail |
| guardrail_id | The unique identifier of the guardrail |
| name | The name of the guardrail |
| description | The description of the guardrail |
| version | The version of the guardrail |
| status | The status of the guardrail (e.g., "CREATING", "READY", "FAILED") |
| blocked_input_messaging | The message returned when input is blocked |
| blocked_outputs_messaging | The message returned when output is blocked |
| created_at | The timestamp when the guardrail was created |
| updated_at | The timestamp when the guardrail was last updated |
| region | The AWS region where the guardrail exists |

#### Relationships

- Guardrails are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockGuardrail)
    ```

- Guardrails are applied to agents to enforce safety policies.
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockAgent)
    ```

- Guardrails are applied to foundation models (derived from agent configurations).
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockFoundationModel)
    ```

- Guardrails are applied to custom models (derived from agent configurations).
    ```
    (AWSBedrockGuardrail)-[APPLIED_TO]->(AWSBedrockCustomModel)
    ```

### AWSBedrockProvisionedModelThroughput

Representation of AWS [Bedrock Provisioned Throughput](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html). Provisioned throughput provides reserved capacity for foundation models and custom models, ensuring consistent performance and availability for production workloads.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the provisioned throughput |
| arn | The ARN of the provisioned throughput |
| provisioned_model_name | The name of the provisioned model throughput |
| model_arn | The ARN of the model (foundation or custom) |
| desired_model_arn | The desired model ARN (used during updates) |
| foundation_model_arn | The ARN of the foundation model |
| model_units | The number of model units allocated |
| desired_model_units | The desired number of model units (used during updates) |
| status | The status of the provisioned throughput (e.g., "Creating", "InService", "Updating") |
| commitment_duration | The commitment duration for the purchase (e.g., "OneMonth", "SixMonths") |
| commitment_expiration_time | The timestamp when the commitment expires |
| creation_time | The timestamp when the provisioned throughput was created |
| last_modified_time | The timestamp when the provisioned throughput was last modified |
| region | The AWS region where the provisioned throughput exists |

#### Relationships

- Provisioned throughputs are resources under an AWS Account.
    ```
    (AWSAccount)-[RESOURCE]->(AWSBedrockProvisionedModelThroughput)
    ```

- Provisioned throughput provides capacity for foundation models.
    ```
    (AWSBedrockProvisionedModelThroughput)-[PROVIDES_CAPACITY_FOR]->(AWSBedrockFoundationModel)
    ```

- Provisioned throughput provides capacity for custom models.
    ```
    (AWSBedrockProvisionedModelThroughput)-[PROVIDES_CAPACITY_FOR]->(AWSBedrockCustomModel)
    ```

### AWSSageMakerDomain

Represents an [AWS SageMaker Domain](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeDomain.html). A Domain is a centralized environment for SageMaker Studio users and their resources.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Domain |
| arn | The ARN of the Domain |
| domain_id | The Domain ID |
| domain_name | The name of the Domain |
| status | The status of the Domain |
| creation_time | When the Domain was created |
| last_modified_time | When the Domain was last modified |
| region | The AWS region where the Domain exists |

#### Relationships

- Domain is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerDomain)
    ```
- Domain contains User Profiles
    ```
    (AWSSageMakerDomain)-[:CONTAINS]->(AWSSageMakerUserProfile)
    ```

### AWSSageMakerUserProfile

Represents an [AWS SageMaker User Profile](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeUserProfile.html). A User Profile represents a user within a SageMaker Studio Domain.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the User Profile |
| arn | The ARN of the User Profile |
| user_profile_name | The name of the User Profile |
| domain_id | The Domain ID that this profile belongs to |
| status | The status of the User Profile |
| creation_time | When the User Profile was created |
| last_modified_time | When the User Profile was last modified |
| execution_role | The IAM execution role ARN for the user |
| region | The AWS region where the User Profile exists |

#### Relationships

- User Profile is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerUserProfile)
    ```
- User Profile belongs to a Domain
    ```
    (AWSSageMakerDomain)-[:CONTAINS]->(AWSSageMakerUserProfile)
    ```
- User Profile has an execution role
    ```
    (AWSSageMakerUserProfile)-[:HAS_EXECUTION_ROLE]->(AWSRole)
    ```

### AWSSageMakerNotebookInstance

Represents an [AWS SageMaker Notebook Instance](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeNotebookInstance.html). A Notebook Instance is a fully managed ML compute instance running Jupyter notebooks.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Notebook Instance |
| arn | The ARN of the Notebook Instance |
| notebook_instance_name | The name of the Notebook Instance |
| notebook_instance_status | The status of the Notebook Instance |
| instance_type | The ML compute instance type |
| url | The URL to connect to the Jupyter notebook |
| creation_time | When the Notebook Instance was created |
| last_modified_time | When the Notebook Instance was last modified |
| role_arn | The IAM role ARN associated with the instance |
| region | The AWS region where the Notebook Instance exists |

#### Relationships

- Notebook Instance is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerNotebookInstance)
    ```
- Notebook Instance has an execution role
    ```
    (AWSSageMakerNotebookInstance)-[:HAS_EXECUTION_ROLE]->(AWSRole)
    ```
- Notebook Instance can invoke Training Jobs (probabilistic relationship based on shared execution role)
    ```
    (AWSSageMakerNotebookInstance)-[:CAN_INVOKE]->(AWSSageMakerTrainingJob)
    ```

### AWSSageMakerTrainingJob

Represents an [AWS SageMaker Training Job](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTrainingJob.html). A Training Job trains ML models using specified algorithms and datasets.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Training Job |
| arn | The ARN of the Training Job |
| training_job_name | The name of the Training Job |
| training_job_status | The status of the Training Job |
| creation_time | When the Training Job was created |
| training_start_time | When training started |
| training_end_time | When training ended |
| role_arn | The IAM role ARN used by the training job |
| algorithm_specification_training_image | The Docker image for the training algorithm |
| input_data_s3_bucket_id | The S3 bucket ID where input data is stored |
| output_data_s3_bucket_id | The S3 bucket ID where output artifacts are stored |
| region | The AWS region where the Training Job runs |

#### Relationships

- Training Job is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerTrainingJob)
    ```
- Training Job has an execution role
    ```
    (AWSSageMakerTrainingJob)-[:HAS_EXECUTION_ROLE]->(AWSRole)
    ```
- Training Job reads data from S3 Bucket
    ```
    (AWSSageMakerTrainingJob)-[:READS_FROM]->(S3Bucket)
    ```
- Training Job produces model artifacts in S3 Bucket
    ```
    (AWSSageMakerTrainingJob)-[:PRODUCES_MODEL_ARTIFACT]->(S3Bucket)
    ```

### AWSSageMakerModel

Represents an [AWS SageMaker Model](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModel.html). A Model contains the information needed to deploy ML models for inference.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Model |
| arn | The ARN of the Model |
| model_name | The name of the Model |
| creation_time | When the Model was created |
| execution_role_arn | The IAM role ARN that SageMaker assumes to perform operations |
| primary_container_image | The Docker image for the primary container |
| model_package_name | The Model Package name if the model is based on one |
| model_artifacts_s3_bucket_id | The S3 bucket ID where model artifacts are stored |
| region | The AWS region where the Model exists |

#### Relationships

- Model is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerModel)
    ```
- Model has an execution role
    ```
    (AWSSageMakerModel)-[:HAS_EXECUTION_ROLE]->(AWSRole)
    ```
- Model references artifacts (Knowledge from training ) that is stored in an S3 bucket
    ```
    (AWSSageMakerModel)-[:REFERENCES_ARTIFACTS_IN]->(S3Bucket)
    ```
- Model derives model blueprint from a model package
    ```
    (AWSSageMakerModel)-[:DERIVES_FROM]->(AWSSageMakerModelPackage)
    ```

### AWSSageMakerEndpointConfig

Represents an [AWS SageMaker Endpoint Configuration](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeEndpointConfig.html). An Endpoint Config specifies the ML compute instances and model variants for deploying models. Allows for a model to provide a prediction to a request in real time.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Endpoint Config |
| arn | The ARN of the Endpoint Config |
| endpoint_config_name | The name of the Endpoint Config |
| creation_time | When the Endpoint Config was created |
| model_name | The name of the model to deploy |
| region | The AWS region where the Endpoint Config exists |

#### Relationships

- Endpoint Config is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerEndpointConfig)
    ```
- Endpoint Config uses a Model
    ```
    (AWSSageMakerEndpointConfig)-[:USES]->(AWSSageMakerModel)
    ```

### AWSSageMakerEndpoint

Represents an [AWS SageMaker Endpoint](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeEndpoint.html). An Endpoint provides a persistent HTTPS endpoint for real-time inference.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Endpoint |
| arn | The ARN of the Endpoint |
| endpoint_name | The name of the Endpoint |
| endpoint_status | The status of the Endpoint |
| creation_time | When the Endpoint was created |
| last_modified_time | When the Endpoint was last modified |
| endpoint_config_name | The name of the Endpoint Config used |
| region | The AWS region where the Endpoint exists |

#### Relationships

- Endpoint is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerEndpoint)
    ```
- Endpoint uses an Endpoint Config
    ```
    (AWSSageMakerEndpoint)-[:USES]->(AWSSageMakerEndpointConfig)
    ```

### AWSSageMakerTransformJob

Represents an [AWS SageMaker Transform Job](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTransformJob.html). A Transform Job performs batch inference on datasets. Takes
a large dataset and uses batch inference to write multiple predictions to an S3 Bucket.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Transform Job |
| arn | The ARN of the Transform Job |
| transform_job_name | The name of the Transform Job |
| transform_job_status | The status of the Transform Job |
| creation_time | When the Transform Job was created |
| model_name | The name of the model used for the transform |
| output_data_s3_bucket_id | The S3 bucket ID where transform output is stored |
| region | The AWS region where the Transform Job runs |

#### Relationships

- Transform Job is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerTransformJob)
    ```
- Transform Job uses a Model
    ```
    (AWSSageMakerTransformJob)-[:USES]->(AWSSageMakerModel)
    ```
- Transform Job writes output to S3 Bucket
    ```
    (AWSSageMakerTransformJob)-[:WRITES_TO]->(S3Bucket)
    ```

### AWSSageMakerModelPackageGroup

Represents an [AWS SageMaker Model Package Group](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModelPackageGroup.html). A Model Package Group is a collection of versioned model packages in the SageMaker Model Registry.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Model Package Group |
| arn | The ARN of the Model Package Group |
| model_package_group_name | The name of the Model Package Group |
| creation_time | When the Model Package Group was created |
| model_package_group_status | The status of the Model Package Group |
| region | The AWS region where the Model Package Group exists |

#### Relationships

- Model Package Group is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerModelPackageGroup)
    ```
- Model Package Group contains Model Packages
    ```
    (AWSSageMakerModelPackageGroup)-[:CONTAINS]->(AWSSageMakerModelPackage)
    ```

### AWSSageMakerModelPackage

Represents an [AWS SageMaker Model Package](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModelPackage.html). A Model Package is a versioned model in the SageMaker Model Registry that acts as a blueprint for a deployed model.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The ARN of the Model Package |
| arn | The ARN of the Model Package |
| model_package_name | The name of the Model Package |
| model_package_group_name | The name of the group this package belongs to |
| model_package_version | The version number of the Model Package |
| model_package_status | The status of the Model Package |
| model_approval_status | The approval status of the Model Package |
| creation_time | When the Model Package was created |
| model_artifacts_s3_bucket_id | The S3 bucket ID where model artifacts are stored |
| region | The AWS region where the Model Package exists |

#### Relationships

- Model Package is a resource under an AWS Account
    ```
    (AWSAccount)-[:RESOURCE]->(AWSSageMakerModelPackage)
    ```
- Model Package belongs to a Model Package Group
    ```
    (AWSSageMakerModelPackageGroup)-[:CONTAINS]->(AWSSageMakerModelPackage)
    ```
- Model Package references artifacts in S3 Bucket
    ```
    (AWSSageMakerModelPackage)-[:REFERENCES_ARTIFACTS_IN]->(S3Bucket)
    ```
