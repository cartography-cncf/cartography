## Opal Schema

.. _opal_schema:

### OpalResource

Representation of an Opal Resource.

| Field | Description |
|-------|-------------|
|id| The unique identifier of the Opal Resource|
|app_id| The unique identifier of the Opal Application|
|name| The name of the Opal Resource|
|admin_owner_id| The unique identifier of the admin owner|
|description| A brief description of the Opal Resource|
|remote_resource_id| The unique identifier of the remote resource|
|remote_resource_name| The name of the remote resource|
|resource_type| The type of the Opal Resource|
|max_duration| The maximum duration for which access is granted|
|recommended_duration| The recommended duration for which access is granted|
|require_manager_approval| Indicates if manager approval is required (true or false)|
|require_support_ticket| Indicates if a support ticket is required (true or false)|
|require_mfa_to_approve| Indicates if MFA is required to approve (true or false)|
|require_mfa_to_request| Indicates if MFA is required to request (true or false)|
|require_mfa_to_connect| Indicates if MFA is required to connect (true or false)|
|is_requestable| Indicates if the resource is requestable (true or false)|
|remote_id| The ARN of the AWS Permission Set associated with the resource|
|remote_account_id| The AWS Account ID associated with the resource|
|firstseen| Timestamp of when a sync job discovered this node|
|lastupdated| Timestamp of the last time the node was updated|

#### Relationships
- OpalResource nodes provide access to AWSRole nodes.

        ```
        (OpalResource)-[PROVIDES_ACCESS_TO]->(AWSRole)
        ```
- OpalResource nodes provide access to OktaGroup nodes.

        ```
        (OpalResource)-[PROVIDES_ACCESS_TO]->(OktaGroup)
        ```
- OpalResource nodes provide access to AWSPermissionSet nodes.

        ```
        (OpalResource)-[PROVIDES_ACCOUNT_ACCESS]->(AWSPermissionSet)
        ```
- OpalResource nodes can have auto-approved access from OktaGroup nodes.

        ```
        (OpalResource)<-[CAN_AUTO_APPROVED_ACCESS]-(OktaGroup)
        ```
- OpalResource nodes can have manually-approved access from OktaGroup nodes.

        ```
        (OpalResource)<-[CAN_MANUALLY_APPROVE_ACCESS]-(OktaGroup)
        ```
