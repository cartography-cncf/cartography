MOCK_REPOSITORIES = {
    "values": [
        {
            "uuid": "{repo-uuid-1}",
            "full_name": "my-workspace/repo-with-project",
            "slug": "repo-with-project",
            "name": "repo-with-project",
            "description": "Has a project",
            "is_private": True,
            "scm": "git",
            "mainbranch": {"name": "main"},
            "project": {"key": "PROJ", "uuid": "{project-uuid-1}"},
            "created_on": "2020-01-01T00:00:00.000000+00:00",
            "updated_on": "2020-02-01T00:00:00.000000+00:00",
            "size": 1024,
            "language": "python",
            "links": {
                "clone": [
                    {
                        "name": "https",
                        "href": "https://bitbucket.org/my-workspace/repo-with-project.git",
                    },
                    {
                        "name": "ssh",
                        "href": "git@bitbucket.org:my-workspace/repo-with-project.git",
                    },
                ],
                "html": {
                    "href": "https://bitbucket.org/my-workspace/repo-with-project"
                },
            },
        },
        {
            "uuid": "{repo-uuid-2}",
            "full_name": "my-workspace/repo-without-project",
            "slug": "repo-without-project",
            "name": "repo-without-project",
            "description": "No project assigned",
            "is_private": False,
            "scm": "git",
            "mainbranch": {"name": "master"},
            "created_on": "2020-01-01T00:00:00.000000+00:00",
            "updated_on": "2020-02-01T00:00:00.000000+00:00",
            "size": 512,
            "language": "go",
            "links": {
                "clone": [
                    {
                        "name": "https",
                        "href": "https://bitbucket.org/my-workspace/repo-without-project.git",
                    },
                ],
                "html": {
                    "href": "https://bitbucket.org/my-workspace/repo-without-project"
                },
            },
        },
    ],
    "next": None,
}

TEST_REPO_WITH_PROJECT_ID = "repo-uuid-1"
TEST_REPO_WITHOUT_PROJECT_ID = "repo-uuid-2"
