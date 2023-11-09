## Lastpass Schema

.. _lastpass_schema:


### Human

Lastpass use Human node as pivot with other Identity Providers (GSuite, GitHub ...)

Human nodes are not created by Lastpass module, link is made using analysis job.


#### Relationships

- Human as an access to Lastpass
    ```
    (Human)-[IDENTITY_LASTPASS]->(LastpassUser)
    ```

### LastpassUser

Representation of a single User in Lastpass

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Lastpass ID |
| name | Full name of the user |
| email | User email |
| created | Timestamp of when the account was created |
| last_pw_change | Timestamp of the last master password change |
| last_login | Timestamp of the last login |
| neverloggedin | Flag indicating the user never logged in |
| disabled | Flag indicating accout is disabled |
| admin | Flag for admin account |
| totalscore | Lastpass security score (max 100) |
| mpstrength | Master password strenght (max 100) |
| sites | Number of site credentials stored |
| notes | Number of secured notes stored |
| formfills | Number of forms stored |
| applications | Number of applications (mobile) stored |
| attachments | Number of file attachments stored |
| password_reset_required | Flag indicating user requested password reset |
| multifactor | MFA method (null if None) |
