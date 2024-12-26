## Github Schema

.. _github_schema:

### GitHubRepository

Representation of a single GitHubRepository (repo) [repository object](https://developer.github.com/v4/object/repository/). This node contains all data unique to the repo.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The GitHub repo id. These are not unique across GitHub instances, so are prepended with the API URL the id applies to |
| createdat | GitHub timestamp from when the repo was created |
| name | Name of the repo |
| fullname | Name of the organization and repo together |
| description | Text describing the repo |
| primarylanguage | The primary language used in the repo |
| homepage | The website used as a homepage for project information |
| defaultbranch | The default branch used by the repo, typically master |
| defaultbranchid | The unique identifier of the default branch |
| private | True if repo is private |
| disabled | True if repo is disabled |
| archived | True if repo is archived |
| locked | True if repo is locked |
| giturl | URL used to access the repo from git commandline |
| url | Web URL for viewing the repo
| sshurl | URL for access the repo via SSH
| updatedat | GitHub timestamp for last time repo was modified |


#### Relationships

- GitHubUsers or GitHubOrganizations own GitHubRepositories.

    ```
    (GitHubUser)-[OWNER]->(GitHubRepository)
    (GitHubOrganization)-[OWNER]->(GitHubRepository)
    ```

- GitHubRepositories in an organization can have [outside collaborators](https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation) who may be granted different levels of access, including ADMIN,
WRITE, MAINTAIN, TRIAGE, and READ ([Reference](https://docs.github.com/en/graphql/reference/enums#repositorypermission)).

    ```
    (GitHubUser)-[:OUTSIDE_COLLAB_{ACTION}]->(GitHubRepository)
    ```

- GitHubRepositories in an organization also mark all [direct collaborators](https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation), folks who are not necessarily 'outside' but who are granted access directly to the repository (as opposed to via membership in a team).  They may be granted different levels of access, including ADMIN,
WRITE, MAINTAIN, TRIAGE, and READ ([Reference](https://docs.github.com/en/graphql/reference/enums#repositorypermission)).

    ```
    (GitHubUser)-[:DIRECT_COLLAB_{ACTION}]->(GitHubRepository)
    ```

- GitHubRepositories use ProgrammingLanguages
    ```
   (GitHubRepository)-[:LANGUAGE]->(ProgrammingLanguage)
    ```
- GitHubRepositories have GitHubBranches
    ```
   (GitHubRepository)-[:BRANCH]->(GitHubBranch)
    ```
- GitHubTeams can have various levels of [access](https://docs.github.com/en/graphql/reference/enums#repositorypermission) to GitHubRepositories.

  ```
  (GitHubTeam)-[ADMIN|READ|WRITE|TRIAGE|MAINTAIN]->(GitHubRepository)
  ```

### GitHubOrganization

Representation of a single GitHubOrganization [organization object](https://developer.github.com/v4/object/organization/). This node contains minimal data for the GitHub Organization.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The URL of the GitHub organization |
| username | Name of the organization |


#### Relationships

- GitHubOrganizations own GitHubRepositories.

    ```
    (GitHubOrganization)-[OWNER]->(GitHubRepository)
    ```

- GitHubTeams are resources under GitHubOrganizations

    ```
    (GitHubOrganization)-[RESOURCE]->(GitHubTeam)
    ```

- GitHubUsers relate to GitHubOrganizations in a few ways:
  - Most typically, they are members of an organization.
  - They may also be org admins (aka org owners), with broad permissions over repo and team settings.  In these cases, they will be graphed with two relationships between GitHubUser and GitHubOrganization, both `MEMBER_OF` and `ADMIN_OF`.
  - In some cases there may be a user who is "unaffiliated" with an org, for example if the user is an enterprise owner, but not member of, the org.  [Enterprise owners](https://docs.github.com/en/enterprise-cloud@latest/admin/managing-accounts-and-repositories/managing-users-in-your-enterprise/roles-in-an-enterprise#enterprise-owners) have complete control over the enterprise (i.e. they can manage all enterprise settings, members, and policies) yet may not show up on member lists of the GitHub org.

    ```
    # a typical member
    (GitHubUser)-[MEMBER_OF]->(GitHubOrganization)

    # an admin member has two relationships to the org
    (GitHubUser)-[MEMBER_OF]->(GitHubOrganization)
    (GitHubUser)-[ADMIN_OF]->(GitHubOrganization)

    # an unaffiliated user (e.g. an enterprise owner)
    (GitHubUser)-[UNAFFILIATED]->(GitHubOrganization)
    ```


### GitHubTeam

A GitHubTeam [organization object](https://docs.github.com/en/graphql/reference/objects#team).


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The URL of the GitHub Team |
| name | The name (a.k.a URL slug) of the GitHub Team |
| description | Description of the GitHub team |


#### Relationships

- GitHubTeams can have various levels of [access](https://docs.github.com/en/graphql/reference/enums#repositorypermission) to GitHubRepositories.

    ```
    (GitHubTeam)-[ADMIN|READ|WRITE|TRIAGE|MAINTAIN]->(GitHubRepository)
    ```

- GitHubTeams are resources under GitHubOrganizations

    ```
    (GitHubOrganization)-[RESOURCE]->(GitHubTeam)
    ```

- GitHubTeams may be children of other teams:

    ```
    (GitHubTeam)-[MEMBER_OF_TEAM]->(GitHubTeam)
    ```

- GitHubUsers may be ['immediate'](https://docs.github.com/en/graphql/reference/enums#teammembershiptype) members of a team (as opposed to being members via membership in a child team), with their membership [role](https://docs.github.com/en/graphql/reference/enums#teammemberrole) being MEMBER or MAINTAINER.

    ```
    (GitHubUser)-[MEMBER|MAINTAINER]->(GitHubTeam)
    ```


### GitHubUser

Representation of a single GitHubUser [user object](https://developer.github.com/v4/object/user/). This node contains minimal data for the GitHub User.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The URL of the GitHub user |
| username | Name of the user |
| fullname | The full name |
| has_2fa_enabled | Whether the user has 2-factor authentication enabled |
| is_site_admin | Whether the user is a site admin |
| is_enterprise_owner | Whether the user is an [enterprise owner](https://docs.github.com/en/enterprise-cloud@latest/admin/managing-accounts-and-repositories/managing-users-in-your-enterprise/roles-in-an-enterprise#enterprise-owners) |
| permission | Only present if the user is an [outside collaborator](https://docs.github.com/en/graphql/reference/objects#repositorycollaboratorconnection) of this repo.  `permission` is either ADMIN, MAINTAIN, READ, TRIAGE, or WRITE ([ref](https://docs.github.com/en/graphql/reference/enums#repositorypermission)). |
| email | The user's publicly visible profile email. |
| company | The user's public profile company. |


#### Relationships

- GitHubUsers own GitHubRepositories.

    ```
    (GitHubUser)-[OWNER]->(GitHubRepository)
    ```

- GitHubRepositories in an organization can have [outside collaborators](https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation) who may be granted different levels of access, including ADMIN,
WRITE, MAINTAIN, TRIAGE, and READ ([Reference](https://docs.github.com/en/graphql/reference/enums#repositorypermission)).

    ```
    (GitHubUser)-[:OUTSIDE_COLLAB_{ACTION}]->(GitHubRepository)
    ```

- GitHubRepositories in an organization also mark all [direct collaborators](https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation), folks who are not necessarily 'outside' but who are granted access directly to the repository (as opposed to via membership in a team).  They may be granted different levels of access, including ADMIN,
WRITE, MAINTAIN, TRIAGE, and READ ([Reference](https://docs.github.com/en/graphql/reference/enums#repositorypermission)).

    ```
    (GitHubUser)-[:DIRECT_COLLAB_{ACTION}]->(GitHubRepository)
    ```

- GitHubUsers relate to GitHubOrganizations in a few ways:
  - Most typically, they are members of an organization.
  - They may also be org admins (aka org owners), with broad permissions over repo and team settings.  In these cases, they will be graphed with two relationships between GitHubUser and GitHubOrganization, both `MEMBER_OF` and `ADMIN_OF`.
  - In some cases there may be a user who is "unaffiliated" with an org, for example if the user is an enterprise owner, but not member of, the org.  [Enterprise owners](https://docs.github.com/en/enterprise-cloud@latest/admin/managing-accounts-and-repositories/managing-users-in-your-enterprise/roles-in-an-enterprise#enterprise-owners) have complete control over the enterprise (i.e. they can manage all enterprise settings, members, and policies) yet may not show up on member lists of the GitHub org.

    ```
    # a typical member
    (GitHubUser)-[MEMBER_OF]->(GitHubOrganization)

    # an admin member has two relationships to the org
    (GitHubUser)-[MEMBER_OF]->(GitHubOrganization)
    (GitHubUser)-[ADMIN_OF]->(GitHubOrganization)

    # an unaffiliated user (e.g. an enterprise owner)
    (GitHubUser)-[UNAFFILIATED]->(GitHubOrganization)
    ```

- GitHubTeams may be children of other teams:

    ```
    (GitHubTeam)-[MEMBER_OF_TEAM]->(GitHubTeam)
    ```

- GitHubUsers may be ['immediate'](https://docs.github.com/en/graphql/reference/enums#teammembershiptype) members of a team (as opposed to being members via membership in a child team), with their membership [role](https://docs.github.com/en/graphql/reference/enums#teammemberrole) being MEMBER or MAINTAINER.

    ```
    (GitHubUser)-[MEMBER|MAINTAINER]->(GitHubTeam)
    ```


### GitHubBranch

Representation of a single GitHubBranch [ref object](https://developer.github.com/v4/object/ref). This node contains minimal data for a repository branch.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The GitHub branch id. These are not unique across GitHub instances, so are prepended with the API URL the id applies to |
| name | Name of the branch |


#### Relationships

- GitHubRepositories have GitHubBranches.

    ```
    (GitHubBranch)<-[BRANCH]-(GitHubRepository)
    ```

### ProgrammingLanguage

Representation of a single Programming Language [language object](https://developer.github.com/v4/object/language). This node contains programming language information.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Language ids need not be tracked across instances, so defaults to the name |
| name | Name of the language |


#### Relationships

- GitHubRepositories use ProgrammingLanguages.

    ```
    (ProgrammingLanguage)<-[LANGUAGE]-(GitHubRepository)
    ```


### Dependency::PythonLibrary

Representation of a Python library as listed in a [requirements.txt](https://pip.pypa.io/en/stable/user_guide/#requirements-files)
or [setup.cfg](https://setuptools.pypa.io/en/latest/userguide/declarative_config.html) file.
Within a setup.cfg file, cartography will load everything from `install_requires`, `setup_requires`, and `extras_require`.

| Field | Description |
|-------|-------------|
|**id**|The [canonicalized](https://packaging.pypa.io/en/latest/utils/#packaging.utils.canonicalize_name) name of the library. If the library was pinned in a requirements file using the `==` operator, then `id` has the form ``{canonical name}\|{pinned_version}``.|
|name|The [canonicalized](https://packaging.pypa.io/en/latest/utils/#packaging.utils.canonicalize_name) name of the library.|
|version|The exact version of the library. This field is only present if the library was pinned in a requirements file using the `==` operator.|

#### Relationships

- Software on Github repos can import Python libraries by optionally specifying a version number.

    ```
    (GitHubRepository)-[:REQUIRES{specifier}]->(PythonLibrary)
    ```

    - specifier: A string describing this library's version e.g. "<4.0,>=3.0" or "==1.0.2". This field is only present on the `:REQUIRES` edge if the repo's requirements file provided a version pin.

- A Python Dependency is affected by a SemgrepSCAFinding (optional)

    ```
    (:SemgrepSCAFinding)-[:AFFECTS]->(:PythonLibrary)
    ```
