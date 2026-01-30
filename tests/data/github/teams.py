from cartography.intel.github.util import PaginatedGraphqlData

GH_TEAM_DATA = (
    PaginatedGraphqlData(
        nodes=[
            {
                "slug": "team-a",
                "url": "https://github.com/orgs/simpsoncorp/teams/team-a",
                "description": None,
                "repositories": {"totalCount": 0},
                "members": {"totalCount": 0},
                "childTeams": {"totalCount": 0},
            },
            {
                "slug": "team-b",
                "url": "https://github.com/orgs/simpsoncorp/teams/team-b",
                "description": None,
                "repositories": {"totalCount": 3},
                "members": {"totalCount": 0},
                "childTeams": {"totalCount": 0},
            },
            {
                "slug": "team-c",
                "url": "https://github.com/orgs/simpsoncorp/teams/team-c",
                "description": None,
                "repositories": {"totalCount": 0},
                "members": {"totalCount": 3},
                "childTeams": {"totalCount": 0},
            },
            {
                "slug": "team-d",
                "url": "https://github.com/orgs/simpsoncorp/teams/team-d",
                "description": "Team D",
                "repositories": {"totalCount": 0},
                "members": {"totalCount": 0},
                "childTeams": {"totalCount": 2},
            },
            {
                "slug": "team-e",
                "url": "https://github.com/orgs/simpsoncorp/teams/team-e",
                "description": "some description here",
                "repositories": {"totalCount": 0},
                "members": {"totalCount": 0},
                "childTeams": {"totalCount": 0},
            },
        ],
        edges=[],
    ),
    {
        "url": "https://github.com/simpsoncorp",
        "login": "SimpsonCorp",
    },
)

GH_TEAM_REPOS = PaginatedGraphqlData(
    nodes=[
        {"url": "https://github.com/simpsoncorp/sample_repo"},
        {"url": "https://github.com/simpsoncorp/SampleRepo2"},
        {"url": "https://github.com/cartography-cncf/cartography"},
    ],
    edges=[
        {"permission": "ADMIN"},
        {"permission": "WRITE"},
        {"permission": "READ"},
    ],
)

GH_TEAM_USERS = PaginatedGraphqlData(
    nodes=[
        {"url": "https://github.com/hjsimpson"},
        {"url": "https://github.com/lmsimpson"},
        {"url": "https://github.com/mbsimpson"},
    ],
    edges=[
        {"role": "MEMBER"},
        {"role": "MAINTAINER"},
        {"role": "MAINTAINER"},
    ],
)

GH_TEAM_CHILD_TEAM = PaginatedGraphqlData(
    nodes=[
        {"url": "https://github.com/orgs/simpsoncorp/teams/team-a"},
        {"url": "https://github.com/orgs/simpsoncorp/teams/team-b"},
    ],
    edges=[],
)
