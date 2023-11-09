from cartography.intel.github.util import PaginatedGraphqlData

GH_TEAM_DATA = (
    PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team-a',
                'url': 'https://github.com/orgs/example_org/teams/team-a',
                'description': None,
                'repositories': {'totalCount': 0},
            },
            {
                'slug': 'team-b',
                'url': 'https://github.com/orgs/example_org/teams/team-b',
                'description': None,
                'repositories': {'totalCount': 3},
            },
            {
                'slug': 'team-c',
                'url': 'https://github.com/orgs/example_org/teams/team-c',
                'description': None,
                'repositories': {'totalCount': 0},
            },
            {
                'slug': 'team-d',
                'url': 'https://github.com/orgs/example_org/teams/team-d',
                'description': 'Team D',
                'repositories': {'totalCount': 0},
            },
            {
                'slug': 'team-e',
                'url': 'https://github.com/orgs/example_org/teams/team-e',
                'description': 'some description here',
                'repositories': {'totalCount': 0},
            },
        ],
        edges=[],
    ), {
        'url': 'https://github.com/example_org',
        'login': 'example_org',
    },
)

GH_TEAM_REPOS = PaginatedGraphqlData(
    nodes=[
        {'url': 'https://github.com/example_org/sample_repo'},
        {'url': 'https://github.com/example_org/SampleRepo2'},
        {'url': 'https://github.com/lyft/cartography'},
    ],
    edges=[
        {'permission': 'ADMIN'},
        {'permission': 'WRITE'},
        {'permission': 'READ'},
    ],
)
