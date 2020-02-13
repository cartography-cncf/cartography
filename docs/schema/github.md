# Cartography - CRXcavator Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [GitHubRepository](#githubrepository)
  - [Relationships](#relationships)
- [GitHubOrganization](#githuborganization)
  - [Relationships](#relationships-1)
- [GitHubUser](#githubuser)
  - [Relationships](#relationships-2)
- [GitHubBranch](#githubbranch)
  - [Relationships](#relationships-3)
- [GitHubBranch](#githubbranch-1)
  - [Relationships](#relationships-4)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## GitHubRepository

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


### Relationships

- GitHubUsers or GitHubOrganizations own GitHubRepositories.

    ```
    (GitHubUser)-[OWNER]->(GitHubRepository)
    (GitHubOrganization)-[OWNER]->(GitHubRepository)
    ```

- GitHubRepositories use ProgrammingLanguages
    ```
   (GitHubRepository)-[:LANGUAGE]->(ProgrammingLanguage)
    ```
- GitHubRepositories have GitHubBranches
    ```
   (GitHubRepository)-[:BRANCH]->(GitHubBranch)
    ```

## GitHubOrganization

Representation of a single GitHubOrganization [organization object](https://developer.github.com/v4/object/organization/). This node contains minimal data for the GitHub Organization.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The GitHub organization id. These are not unique across GitHub instances, so are prepended with the API URL the id applies to |
| username | Name of the organization |


### Relationships

- GitHubOrganizations own GitHubRepositories.

    ```
    (GitHubOrganization)-[OWNER]->(GitHubRepository)
    ```

## GitHubUser

Representation of a single GitHubUser [user object](https://developer.github.com/v4/object/user/). This node contains minimal data for the GitHub User.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The GitHub user id. These are not unique across GitHub instances, so are prepended with the API URL the id applies to |
| username | Name of the user |


### Relationships

- GitHubUsers own GitHubRepositories.

    ```
    (GitHubUser)-[OWNER]->(GitHubRepository)
    ```

## GitHubBranch

Representation of a single GitHubBranch [ref object](https://developer.github.com/v4/object/ref). This node contains minimal data for a repository branch.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The GitHub branch id. These are not unique across GitHub instances, so are prepended with the API URL the id applies to |
| name | Name of the branch |


### Relationships

- GitHubRepositories have GitHubBranches.

    ```
    (GitHubBranch)<-[BRANCH]-(GitHubRepository)
    ```

## GitHubBranch

Representation of a single Programming Language [language object](https://developer.github.com/v4/object/language). This node contains programming language information.


| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | Language ids need not be tracked across instances, so defaults to the name |
| name | Name of the language |


### Relationships

- GitHubRepositories use ProgrammingLanguages.

    ```
    (ProgrammingLanguage)<-[LANGUAGE]-(GitHubRepository)
    ```
