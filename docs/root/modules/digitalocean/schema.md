## DigitalOcean Schema

### DOAccount
Representation of a DigitalOcean [Account](https://developers.digitalocean.com/documentation/v2/#account) object.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The UUID of the account |
| uuid | The UUID of the account (same value as id) |
| droplet_limit | Total number of droplets that the account can have at one time |
| floating_ip_limit | Total number of floating IPs the account may have |
| status | Status of the account |

#### Relationships

- DOAccount contains DOProjects.

    ```
    (DOAccount)-[RESOURCE]->(DOProjects)
    ```

### DOProject
Representation of a DigitalOcean [Project](https://developers.digitalocean.com/documentation/v2/#projects) object.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique universal identifier of the project |
| account_id | Id of the DOAccount where this project belongs to |
| description | The description of the project |
| environment | The environment of the project's resources |
| is_default | If true, all resources will be added to this project if no project is specified |
| name | The human-readable name for the project |
| owner_uuid | The unique universal identifier of the project's owner |
| created_at | A time value given in ISO8601 combined date and time format that represents when the project was created |
| updated_at | A time value given in ISO8601 combined date and time format that represents when the project was updated |

#### Relationships

- DOProject has DODroplets as resource.

    ```
    (DOProject)-[RESOURCE]->(DODroplet)
    ```

### DODroplet
Representation of a DigitalOcean [Droplet](https://developers.digitalocean.com/documentation/v2/#droplets) object.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | A unique identifier for each Droplet instance |
| account_id | Id of the DOAccount where this Droplet belongs to |
| features | An array of features enabled on this Droplet |
| locked | A boolean value indicating whether the Droplet has been locked, preventing actions by users |
| image | The slug of the base image used to create the Droplet instance|
| ip_address | The v4 external ip address of this Droplet |
| ip_v6_address | The v6 external ip address of this Droplet |
| kernel | The current kernel image id|
| name | The human-readable name set for the Droplet instance |
| private_ip_address | The v4 internal ip address of this Droplet |
| project_id | Id of the DOProject where this Droplet belongs to |
| region | The region that the Droplet instance is deployed in |
| size | The current size object describing the Droplet |
| status | A status string indicating the state of the Droplet instance.This may be "new", "active", "off", or "archive"|
| tags | An array of Tags the Droplet has been tagged with |
| volumes | A flat array including the unique identifier for each Block Storage volume attached to the Droplet |
| created_at | A time value given in ISO8601 combined date and time format that represents when the Droplet was created |

#### Relationships

- DODroplet is a resource of a DOProject.

    ```
    (DODroplet)<-[RESOURCE]-(DOProject)
    ```
