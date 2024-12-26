import textwrap
from typing import Any
from typing import List

from cartography.intel.github.repos import UserAffiliationAndRepoPermission

GET_REPOS: List[dict[str, Any]] = [
    {
        'name': 'sample_repo',
        'nameWithOwner': 'example_org/sample_repo',
        'primaryLanguage': {
            'name': 'Python',
        },
        'url': 'https://github.com/example_org/sample_repo',
        'sshUrl': 'git@github.com:example_org/sample_repo.git',
        'createdAt': '2011-02-15T18:40:15Z',
        'description': 'My description',
        'updatedAt': '2020-01-02T20:10:09Z',
        'homepageUrl': '',
        'languages': {
            'totalCount': 1,
            'nodes': [
                {'name': 'Python'},
            ],
        },
        'defaultBranchRef': {
            'name': 'master',
            'id': 'branch_ref_id==',
        },
        'isPrivate': True,
        'isArchived': False,
        'isDisabled': False,
        'isLocked': True,
        'owner': {
            'url': 'https://github.com/example_org',
            'login': 'example_org',
            '__typename': 'Organization',
        },
        'directCollaborators': {'totalCount': 0},
        'outsideCollaborators': {'totalCount': 0},
        'requirements': {'text': 'cartography\nhttplib2<0.7.0\njinja2\nlxml\n-e git+https://example.com#egg=foobar\nhttps://example.com/foobar.tar.gz\npip @ https://github.com/pypa/pip/archive/1.3.1.zip#sha1=da9234ee9982d4bbb3c72346a6de940a148ea686\n'},  # noqa
        'setupCfg': {
            'text': textwrap.dedent('''
                [options]
                install_requires =
                    neo4j
                    scipy!=1.20.0  # comment
            '''),
        },
    },
    {
        'name': 'SampleRepo2',
        'nameWithOwner': 'example_org/SampleRepo2',
        'primaryLanguage': {
            'name': 'Python',
        },
        'url': 'https://github.com/example_org/SampleRepo2',
        'sshUrl': 'git@github.com:example_org/SampleRepo2.git',
        'createdAt': '2011-09-21T18:55:16Z',
        'description': 'Some other description',
        'updatedAt': '2020-07-03T00:25:25Z',
        'homepageUrl': 'http://example.com/',
        'languages': {
            'totalCount': 1,
            'nodes': [
                {'name': 'Python'},
            ],
        },
        'defaultBranchRef': {
            'name': 'master',
            'id': 'other_branch_ref_id==',
        },
        'isPrivate': False,
        'isArchived': False,
        'isDisabled': False,
        'isLocked': False,
        'owner': {
            'url': 'https://github.com/example_org',
            'login': 'example_org', '__typename': 'Organization',
        },
        'directCollaborators': {'totalCount': 1},
        'outsideCollaborators': {'totalCount': 0},
        'requirements': None,
        'setupCfg': None,
    },
    {
        'name': 'cartography',
        'nameWithOwner': 'lyft/cartography',
        'primaryLanguage': {'name': 'Python'},
        'url': 'https://github.com/lyft/cartography',
        'sshUrl': 'git@github.com:lyft/cartography.git',
        'createdAt': '2019-02-27T00:16:29Z',
        'description': 'One graph to rule them all',
        'updatedAt': '2020-09-02T18:35:17Z',
        'homepageUrl': '',
        'languages': {
            'totalCount': 2,
            'nodes': [{'name': 'Python'}, {'name': 'Makefile'}],
        },
        'defaultBranchRef': {
            'name': 'master',
            'id': 'putsomethinghere',
        },
        'isPrivate': False,
        'isArchived': False,
        'isDisabled': False,
        'isLocked': False,
        'owner': {
            'url': 'https://github.com/example_org',
            'login': 'example_org',
            '__typename': 'Organization',
        },
        'directCollaborators': {'totalCount': 3},
        'outsideCollaborators': {'totalCount': 5},
        'requirements': {
            'text': 'cartography==0.1.0\nhttplib2>=0.7.0\njinja2\nlxml\n# This is a comment line to be ignored\nokta==0.9.0',  # noqa
        },
        'setupCfg': {
            'text': textwrap.dedent('''
                [options]
                install_requires =
                    neo4j>=1.0.0
                    numpy!=1.20.0  # comment
                    okta
            '''),
        },
    },
]


# - This list is not a raw API response, but the lightly processed collected results of all the API calls, for all
# repos that have collaborators.
# - The actual values are mostly arbitrary but the length of the lists is directly tied to the data in GET_REPOS,
# e.g. since GET_REPOS notes that 'sample_repo' has 0 direct collaborators, the 'sample_repo' list below is empty.
OUTSIDE_COLLABORATORS: dict[str, List[UserAffiliationAndRepoPermission]] = {
    GET_REPOS[0]['url']: [],
    GET_REPOS[1]['url']: [],
    GET_REPOS[2]['url']: [
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/marco-lancini',
                'login': 'marco-lancini',
                'name': 'Marco Lancini',
                'email': 'm@example.com',
                'company': 'ExampleCo',
            },
            permission='WRITE',
            affiliation='OUTSIDE',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/sachafaust',
                'login': 'sachafaust',
                'name': 'Sacha Faust',
                'email': 's@example.com',
                'company': 'ExampleCo',
            },
            permission='READ',
            affiliation='OUTSIDE',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/SecPrez',
                'login': 'SecPrez',
                'name': 'SecPrez',
                'email': 'sec@example.com',
                'company': 'ExampleCo',
            },
            permission='ADMIN',
            affiliation='OUTSIDE',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/ramonpetgrave64',
                'login': 'ramonpetgrave64',
                'name': 'Ramon Petgrave',
                'email': 'r@example.com',
                'company': 'ExampleCo',
            },
            permission='TRIAGE',
            affiliation='OUTSIDE',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/roshinis78',
                'login': 'roshinis78',
                'name': 'Roshini Saravanakumar',
                'email': 'ro@example.com',
                'company': 'ExampleCo',
            },
            permission='MAINTAIN',
            affiliation='OUTSIDE',
        ),
    ],
}


# - All notes for OUTSIDE_COLLABORATORS apply here as well.
# - We also include the lists from OUTSIDE_COLLABORATORS here.  Users who are outside collaborators are
#   also marked as direct collaborators, by Github, so we mimic that idea in our test data here.
DIRECT_COLLABORATORS: dict[str, List[UserAffiliationAndRepoPermission]] = {
    GET_REPOS[0]['url']: [],
    GET_REPOS[1]['url']: [
        *OUTSIDE_COLLABORATORS[GET_REPOS[1]['url']],
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/direct_foo',
                'login': 'direct_foo',
                'name': 'Foo User',
                'email': '',
                'company': None,
            },
            permission='ADMIN',
            affiliation='DIRECT',
        ),
    ],
    GET_REPOS[2]['url']: [
        *OUTSIDE_COLLABORATORS[GET_REPOS[2]['url']],
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/direct_bar',
                'login': 'direct_bar',
                'name': 'Bar User',
                'email': 'b@sushigrass.com',
                'company': 'sushiGrass',
            },
            permission='WRITE',
            affiliation='DIRECT',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/direct_baz',
                'login': 'direct_baz',
                'name': 'Baz User',
                'email': 'b@testco.com',
                'company': 'TestCo',
            },
            permission='READ',
            affiliation='DIRECT',
        ),
        UserAffiliationAndRepoPermission(
            user={
                'url': 'https://github.com/direct_bat',
                'login': 'direct_bat',
                'name': 'Bat User',
                'email': '',
                'company': None,
            },
            permission='MAINTAIN',
            affiliation='DIRECT',
        ),
    ],
}
