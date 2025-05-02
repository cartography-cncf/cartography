# flake8: noqa
GCP_ORGANIZATIONS = [
    {
        "displayName": "example.com",
        "owner": {
            "directoryCustomerId": "asdf",
        },
        "creationTime": "2017-01-13T20:06:21.571Z",
        "lifecycleState": "ACTIVE",
        "name": "organizations/1337",
    },
]

GCP_FOLDERS = [
    {
        "name": "folders/1414",
        "parent": "organizations/1337",
        "displayName": "my-folder",
        "lifecycleState": "ACTIVE",
        "createTime": "2019-04-11T13:33:07.766Z",
    },
]

GCP_PROJECTS = [
    {
        "createTime": "2019-05-22T19:28:30.592Z",
        "lifecycleState": "ACTIVE",
        "name": "Group 1",
        "parent": {"id": "1414", "type": "folder"},
        "projectId": "this-project-has-a-parent-232323",
        "projectNumber": "232323",
    },
]

GCP_PROJECTS_WITHOUT_PARENT = [
    {
        "createTime": "2019-11-11T21:06:32.043Z",
        "lifecycleState": "ACTIVE",
        "name": "my-parentless-project",
        "projectId": "my-parentless-project-987654",
        "projectNumber": "123456789012",
    },
]
