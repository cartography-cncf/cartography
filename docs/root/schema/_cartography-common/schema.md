## Cartography common schema

Cartography use some abstract node to allow pivot between similar entities from different applications.

### Human

Cartography use Human node as pivot between Identity Providers (GSuite, GitHub ...) and applications.
Application Users are linked using a `IDENTITY_APPNAME` relationship. Please refer to each intel module documentation for further information.

| Field       | Description |
|-------------|-------------|
| firstseen   | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id          | Email of the Human |
| email       | Email of the Human |
