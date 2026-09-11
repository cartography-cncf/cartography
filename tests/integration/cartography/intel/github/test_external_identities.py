import json
from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.github import external_identities
from cartography.intel.github.users import load_organization
from cartography.intel.github.users import load_users
from cartography.intel.okta.users import _load_okta_users
from cartography.intel.ontology.users import sync as sync_ontology_users
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.github.external_identities import API_URL
from tests.data.github.external_identities import FORBIDDEN
from tests.data.github.external_identities import IDENTITIES
from tests.data.github.external_identities import NO_SAML_PROVIDER
from tests.data.github.external_identities import ORG
from tests.data.github.external_identities import ORG_URL
from tests.data.github.external_identities import page
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _seed_org(session, org_url=ORG_URL):
    org = {"url": org_url, "login": org_url.rsplit("/", 1)[1]}
    load_organization(session, GitHubOrganizationSchema(), [org], 100)
    load_users(
        session,
        GitHubOrganizationUserSchema(),
        [
            {
                "url": f"https://github.com/example-{name}",
                "login": f"example-{name}",
                "MEMBER_OF": org_url,
                "organizationVerifiedDomainEmails": (
                    ["carol@example.com"] if name == "carol" else []
                ),
            }
            for name in ("alice", "bob", "carol")
        ],
        org,
        100,
    )


@pytest.fixture(autouse=True)
def prerequisites(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_org(neo4j_session)
    neo4j_session.run("CREATE (:OktaOrganization {id: 'example.okta.com'})")
    _load_okta_users(
        neo4j_session,
        [
            {"id": f"okta-{name}", "email": f"{name}@example.com"}
            for name in ("alice", "bob", "carol", "unlinked")
        ],
        {"UPDATE_TAG": 100, "OKTA_ORG_ID": "example.okta.com"},
    )


def _sync(session, tag=100, org=ORG):
    external_identities.sync(session, {"UPDATE_TAG": tag}, "test-token", API_URL, org)


def _ontology(session, tag=100):
    sync_ontology_users(session, ["okta"], tag, {"UPDATE_TAG": tag})


def _github_links(session):
    return check_rels(session, "User", "email", "GitHubUser", "username", "HAS_ACCOUNT")


@patch("cartography.intel.github.util.requests.post")
def test_sync_paginated_identities_and_ontology(mock_post, neo4j_session):
    # Arrange
    mock_post.side_effect = [
        Mock(json=lambda: page(IDENTITIES[:2], has_next_page=True, cursor="cursor-1")),
        Mock(json=lambda: page(IDENTITIES[2:])),
    ]

    # Act
    _sync(neo4j_session, org=ORG.upper())
    _ontology(neo4j_session)

    # Assert
    assert check_nodes(
        neo4j_session, "GitHubExternalIdentity", ["id", "saml_name_id"]
    ) == {
        (f"{ORG_URL}|E_example_alice", " Alice@Example.com "),
        (f"{ORG_URL}|E_example_bob", "bob@example.com"),
        (f"{ORG_URL}|E_example_unlinked", "unlinked@example.com"),
        (f"{ORG_URL}|E_example_without_saml", None),
    }
    assert check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubExternalIdentity",
        "id",
        "RESOURCE",
    ) == {(ORG_URL, f"{ORG_URL}|{identity['id']}") for identity in IDENTITIES}
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubExternalIdentity",
        "id",
        "HAS_IDENTITY",
    ) == {
        ("example-alice", f"{ORG_URL}|E_example_alice"),
        ("example-bob", f"{ORG_URL}|E_example_bob"),
        ("example-carol", f"{ORG_URL}|E_example_without_saml"),
    }
    assert _github_links(neo4j_session) == {
        ("alice@example.com", "example-alice"),
        ("bob@example.com", "example-bob"),
        ("carol@example.com", "example-carol"),
    }
    assert (
        neo4j_session.run(
            "MATCH (:OktaUser)<-[:HAS_ACCOUNT]-(:User)-[:HAS_ACCOUNT]->(:GitHubUser) RETURN count(*) AS n"
        ).single()["n"]
        == 3
    )
    assert [
        json.loads(call.kwargs["json"]["variables"])["cursor"]
        for call in mock_post.call_args_list
    ] == [None, "cursor-1"]


@patch("cartography.intel.github.util.requests.post")
def test_cleanup_reassignment_and_other_organization(mock_post, neo4j_session):
    # Arrange
    other_org = "other-org"
    other_url = f"https://github.com/{other_org}"
    _seed_org(neo4j_session, other_url)
    mock_post.return_value.json.return_value = page(IDENTITIES)
    _sync(neo4j_session)
    mock_post.return_value.json.return_value = page([IDENTITIES[3]], org_url=other_url)
    _sync(neo4j_session, org=other_org)
    _ontology(neo4j_session)
    firstseen = neo4j_session.run(
        "MATCH (i:GitHubExternalIdentity {id: $id}) RETURN i.firstseen AS value",
        id=f"{ORG_URL}|E_example_alice",
    ).single()["value"]
    changed = deepcopy(IDENTITIES[0])
    changed["samlIdentity"]["nameId"] = "bob@example.com"
    mock_post.return_value.json.return_value = page([changed])

    # Act
    _sync(neo4j_session, 200)
    _ontology(neo4j_session, 200)

    # Assert
    assert check_nodes(
        neo4j_session, "GitHubExternalIdentity", ["id", "lastupdated"]
    ) == {
        (f"{ORG_URL}|E_example_alice", 200),
        (f"{other_url}|E_example_without_saml", 100),
    }
    assert _github_links(neo4j_session) == {
        ("bob@example.com", "example-alice"),
        ("carol@example.com", "example-carol"),
    }
    link_firstseen = neo4j_session.run(
        "MATCH (:User {email: 'bob@example.com'})-[r:HAS_ACCOUNT]->(:GitHubUser {username: 'example-alice'}) RETURN r.firstseen AS value"
    ).single()["value"]

    # Act
    _sync(neo4j_session, 300)
    _ontology(neo4j_session, 300)

    # Assert
    assert neo4j_session.run(
        "MATCH (:GitHubUser)-[r:HAS_IDENTITY]->(i:GitHubExternalIdentity {id: $id}) RETURN count(r) AS n, min(i.firstseen) AS firstseen",
        id=f"{ORG_URL}|E_example_alice",
    ).single().data() == {"n": 1, "firstseen": firstseen}
    assert neo4j_session.run(
        "MATCH (:User {email: 'bob@example.com'})-[r:HAS_ACCOUNT]->(:GitHubUser {username: 'example-alice'}) RETURN r.firstseen AS firstseen, r.lastupdated AS lastupdated"
    ).single().data() == {"firstseen": link_firstseen, "lastupdated": 300}


@patch("cartography.intel.github.util.requests.post")
def test_authoritative_empty_removes_saml_links(mock_post, neo4j_session):
    # Arrange
    mock_post.return_value.json.return_value = page(IDENTITIES)
    _sync(neo4j_session)
    _ontology(neo4j_session)
    mock_post.return_value.json.return_value = page([])

    # Act
    _sync(neo4j_session, 200)
    _ontology(neo4j_session, 200)

    # Assert
    assert check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"]) == set()
    assert _github_links(neo4j_session) == {("carol@example.com", "example-carol")}
    assert len(check_nodes(neo4j_session, "GitHubUser", ["id"])) == 3


@pytest.mark.parametrize("denied_on_second_page", [False, True])
@pytest.mark.parametrize("unavailable_response", [FORBIDDEN, NO_SAML_PROVIDER])
@patch("cartography.intel.github.util.requests.post")
def test_denied_snapshot_preserves_existing_identities(
    mock_post, neo4j_session, denied_on_second_page, unavailable_response
):
    # Arrange
    mock_post.return_value.json.return_value = page(IDENTITIES)
    _sync(neo4j_session)
    _ontology(neo4j_session)
    denied = Mock(json=lambda: unavailable_response)
    mock_post.side_effect = (
        [Mock(json=lambda: page([], has_next_page=True, cursor="cursor-1"))]
        if denied_on_second_page
        else []
    ) + [denied]

    # Act
    _sync(neo4j_session, 200)
    _ontology(neo4j_session, 200)

    # Assert
    assert check_nodes(neo4j_session, "GitHubExternalIdentity", ["lastupdated"]) == {
        (100,)
    }
    assert len(check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"])) == 4
    assert _github_links(neo4j_session) == {
        ("alice@example.com", "example-alice"),
        ("bob@example.com", "example-bob"),
        ("carol@example.com", "example-carol"),
    }


@patch("cartography.intel.github.util.requests.post")
def test_partial_error_does_not_write_or_cleanup(mock_post, neo4j_session):
    # Arrange
    mock_post.return_value.json.return_value = page(IDENTITIES)
    _sync(neo4j_session)
    response = page([IDENTITIES[0]])
    response["errors"] = [
        {
            "message": "timedout",
            "path": ["organization", "samlIdentityProvider", "externalIdentities"],
        }
    ]
    mock_post.return_value.json.return_value = response

    # Act and assert
    with pytest.raises(RuntimeError, match="query failed"):
        _sync(neo4j_session, 200)
    assert len(check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"])) == 4
    assert check_nodes(neo4j_session, "GitHubExternalIdentity", ["lastupdated"]) == {
        (100,)
    }


@pytest.mark.parametrize(
    "case",
    [
        "ambiguous",
        "ambiguous_email",
        "conflicting_public_email",
        "nonmember",
        "opaque_nameid",
    ],
)
@patch("cartography.intel.github.util.requests.post")
def test_ontology_rejects_unreliable_matches(mock_post, neo4j_session, case):
    # Arrange
    identities = deepcopy(IDENTITIES[:1])
    if case == "ambiguous":
        identities.append(
            {
                "id": "E_example_conflict",
                "samlIdentity": {"nameId": "bob@example.com"},
                "user": identities[0]["user"],
            }
        )
    elif case == "ambiguous_email":
        _load_okta_users(
            neo4j_session,
            [{"id": "okta-duplicate", "email": "ALICE@example.com"}],
            {"UPDATE_TAG": 100, "OKTA_ORG_ID": "example.okta.com"},
        )
    elif case == "conflicting_public_email":
        neo4j_session.run(
            "MATCH (g:GitHubUser {username: 'example-alice'}) SET g.email = 'bob@example.com'"
        )
    elif case == "nonmember":
        neo4j_session.run(
            "MATCH (:GitHubUser {username: 'example-alice'})-[r:MEMBER_OF]->(:GitHubOrganization) DELETE r"
        )
    else:
        identities[0]["samlIdentity"]["nameId"] = "alice"
    mock_post.return_value.json.return_value = page(identities)

    # Act
    _sync(neo4j_session)
    _ontology(neo4j_session)

    # Assert
    expected = {("carol@example.com", "example-carol")}
    if case == "conflicting_public_email":
        expected.add(("bob@example.com", "example-alice"))
    assert _github_links(neo4j_session) == expected
    assert len(check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"])) == len(
        identities
    )


@patch("cartography.intel.github.util.requests.post")
def test_ontology_rejects_conflicting_organizations(mock_post, neo4j_session):
    # Arrange
    _seed_org(neo4j_session, "https://github.com/other-org")
    mock_post.return_value.json.return_value = page(IDENTITIES[:1])
    _sync(neo4j_session)
    other_identity = deepcopy(IDENTITIES[0])
    other_identity["samlIdentity"]["nameId"] = "bob@example.com"
    mock_post.return_value.json.return_value = page(
        [other_identity], org_url="https://github.com/other-org"
    )
    _sync(neo4j_session, org="other-org")

    # Act
    _ontology(neo4j_session)

    # Assert
    assert len(check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"])) == 2
    assert _github_links(neo4j_session) == {("carol@example.com", "example-carol")}


@patch("cartography.intel.github.util.requests.post")
def test_unlinked_identity_removes_old_account_relationship(mock_post, neo4j_session):
    # Arrange
    mock_post.return_value.json.return_value = page(IDENTITIES[:1])
    _sync(neo4j_session)
    _ontology(neo4j_session)
    unlinked = deepcopy(IDENTITIES[0])
    unlinked["user"] = None
    mock_post.return_value.json.return_value = page([unlinked])

    # Act
    _sync(neo4j_session, 200)
    _ontology(neo4j_session, 200)

    # Assert
    assert check_nodes(neo4j_session, "GitHubExternalIdentity", ["id"]) == {
        (f"{ORG_URL}|E_example_alice",)
    }
    assert (
        check_rels(
            neo4j_session,
            "GitHubUser",
            "id",
            "GitHubExternalIdentity",
            "id",
            "HAS_IDENTITY",
        )
        == set()
    )
    assert _github_links(neo4j_session) == {("carol@example.com", "example-carol")}
