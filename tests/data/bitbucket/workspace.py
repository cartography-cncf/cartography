WORKSPACES= [
        {
            "created_on": "2023-03-24T07:12:16.787134+00:00",
            "is_private": True,
            "name": "Workspace",
            "slug": "Workspace",
            "type": "workspace",
            "uuid": "id123"
        },
        {
            "created_on": "2023-04-17T09:46:47.454188+00:00",
            "is_private": True,
            "name": "Workspace12",
            "slug": "workspace12",
            "type": "workspace",
            "uuid": "id456"
        }
    ]

PROJECTS= [
        {
            "created_on": "2023-05-11T05:04:17.808136+00:00",
            "description": None,
            "has_publicly_visible_repos": True,
            "is_private": False,
            "key": "BIT",
            "name": "bitbuket-test",
            "owner": {
                "display_name": "workspace",
                "type": "team",
                "username": "workspace",
                "uuid": "id-456"
            },
            "type": "project",
            "updated_on": "2023-05-11T05:04:17.808148+00:00",
            "uuid": "project-123",
            "workspace": {
                "name": "workspace",
                "slug": "workspace",
                "type": "workspace",
                "uuid": "id456"
            }
        },
        {
            "created_on": "2023-04-26T16:59:00.963792+00:00",
            "description": None,
            "has_publicly_visible_repos": False,
            "is_private": False,
            "key": "FIR",
            "name": "firstproject",
            "owner": {
                "display_name": "workspace",
                "type": "team",
                "username": "workspace",
                "uuid": "qere"
            },
            "type": "project",
            "updated_on": "2023-04-26T16:59:00.963827+00:00",
            "uuid": "project-987",
            "workspace": {
                "name": "workspace",
                "slug": "workspace",
                "type": "workspace",
                "uuid": "id123"
            }
        }
    ]
REPOSITORIES=[
    {
        "type": "repository",
        "full_name": "Workspace12/repo1",
        "name": "repo1",
        "slug": "repo1",
        "description": "",
        "scm": "git",
        "website": None,
        "owner": {
            "display_name": "fgh",
            "type": "team",
            "uuid": "123",
            "username": "fgh"
        },
        "workspace": {
            "type": "workspace",
            "uuid": "id123",
            "name": "workspace",
            "slug": "workspace",

        },
        "is_private": True,
        "project": {
            "type": "project",
            "key": "FIR",
            "uuid": "project123",
            "name": "firstproject",
        },
        "fork_policy": "no_public_forks",
        "created_on": "2023-03-24T07:16:07.545221+00:00",
        "updated_on": "2023-03-24T07:16:10.045801+00:00",
        "size": 55804,
        "language": "",
        "has_issues": False,
        "has_wiki": False,
        "uuid": "repo1",
        "mainbranch": {
            "name": "master",
            "type": "branch"
        },
        "override_settings": {
            "default_merge_strategy": True,
            "branching_model": True
        },
        "parent": None
    },
    {
        "type": "repository",
        "full_name": "workspace/demofirstrepo",
        "name": "DemofirstRepo",
        "slug": "demofirstrepo",
        "description": "",
        "scm": "git",
        "website": None,
        "owner": {
            "display_name": "fgh",
            "type": "team",
            "uuid": "sfgdfhjkgjklh-nmn",
            "username": "fgh"
        },
        "workspace": {
            "type": "workspace",
            "uuid": "id123",
            "name": "workspace",
            "slug": "workspace"
        },
        "is_private": True,
        "project": {
            "type": "project",
            "key": "FIR",
            "uuid": "project123",
            "name": "firstproject",
        },
        "fork_policy": "no_public_forks",
        "created_on": "2023-04-17T06:06:08.630453+00:00",
        "updated_on": "2023-04-17T06:06:11.257481+00:00",
        "size": 55908,
        "language": "",
        "has_issues": False,
        "has_wiki": False,
        "uuid": "repo2",
        "mainbranch": {
            "name": "main",
            "type": "branch"
        },
        "override_settings": {
            "default_merge_strategy": True,
            "branching_model": True
        },
        "parent": None
    },
]

members=[
        {
            "type": "workspace_membership",
            "user": {
                "account_id": "632d8cbcb2e3c5ad0fa32990",
                "display_name": "user-123",
                "nickname": "user-123",
                "type": "user",
                "uuid": "user-123"
            },
            "workspace": {
                "name": "workspace12",
                "slug": "workspace12",
                "type": "workspace",
                "uuid": "id123"
            }
        },
        {
            "type": "workspace_membership",
            "user": {
                "account_id": "621135a307f51e0069458910",
                "display_name": "ABC",
                "nickname": "ABC",
                "type": "user",
                "uuid": "user-567"
            },
            "workspace": {
                "name": "workspace12",
                "slug": "workspace12",
                "type": "workspace",
                "uuid": "id123"
            }
        }
    ]
