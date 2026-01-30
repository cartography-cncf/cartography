from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.authenticationexecutions
import tests.data.keycloak.authenticationexecutions
from tests.integration.cartography.intel.keycloak.test_authenticationflows import (
    _ensure_local_neo4j_has_test_authenticationflows,
)
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"
TEST_REALM_ID = "abcd1234-efgh-5678-ijkl-9012mnop3456"


def _ensure_local_neo4j_has_test_authenticationexecutions(neo4j_session):
    raw_data = deepcopy(
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS
    )
    transformed_exec, flow_steps, initial_flow_steps = (
        cartography.intel.keycloak.authenticationexecutions.transform(
            raw_data, TEST_REALM
        )
    )
    cartography.intel.keycloak.authenticationexecutions.load_authenticationexecutions(
        neo4j_session,
        transformed_exec,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )
    cartography.intel.keycloak.authenticationexecutions.load_execution_flow(
        neo4j_session,
        flow_steps,
        initial_flow_steps,
        TEST_REALM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.authenticationexecutions,
    "get",
    return_value=deepcopy(
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS
    ),
)
def test_load_keycloak_authenticationexecutions(_mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
        "REALM_ID": TEST_REALM_ID,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_authenticationflows(neo4j_session)
    flow_aliases = list(
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS.keys()
    )

    # Act
    cartography.intel.keycloak.authenticationexecutions.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
        flow_aliases,
    )

    # Assert Authentication Executions exist
    expected_nodes = set()
    for (
        flow_executions
    ) in (
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS.values()
    ):
        for execution in flow_executions:
            expected_nodes.add((execution["id"], execution["index"]))
    assert len(expected_nodes) > 0
    assert (
        check_nodes(neo4j_session, "KeycloakAuthenticationExecution", ["id", "index"])
        == expected_nodes
    )

    # Assert Authentication Executions are connected with Realm
    expected_rels = set()
    for (
        flow_executions
    ) in (
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS.values()
    ):
        for execution in flow_executions:
            expected_rels.add((execution["id"], TEST_REALM))
    assert (
        check_rels(
            neo4j_session,
            "KeycloakAuthenticationExecution",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Flows are connected to Executions
    expected_rels = set()
    for (
        flow_name,
        flow_executions,
    ) in (
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS.items()
    ):
        for execution in flow_executions:
            if execution["level"] == 0:
                expected_rels.add((execution["id"], flow_name))
    assert (
        check_rels(
            neo4j_session,
            "KeycloakAuthenticationExecution",
            "id",
            "KeycloakAuthenticationFlow",
            "alias",
            "HAS_STEP",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.keycloak.authenticationexecutions,
    "get",
    return_value=tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS,
)
def test_load_keycloak_authenticationexecutions_flow_compute(_mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
        "REALM_ID": TEST_REALM_ID,
    }
    _ensure_local_neo4j_has_test_authenticationflows(neo4j_session)

    # Get flow aliases from test data
    flow_aliases = list(
        tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS.keys()
    )

    # Act
    cartography.intel.keycloak.authenticationexecutions.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
        flow_aliases,
    )

    # Check all execution flow
    expected_rels = {
        (
            "0a599b6c-7fdd-48c8-b32c-9e5d68d56634",
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
        ),
        (
            "171c093a-8150-4520-929f-773811bc6967",
            "98e23ac0-5952-4ad6-9c67-bdd03ce477d6",
        ),
        (
            "1d9ab39a-40db-498b-8452-3303431ed517",
            "8d0d7031-1549-4f17-97bf-d184c85fe1ad",
        ),
        (
            "1f73724a-8eba-48dd-9687-0ca2d1ca51a7",
            "0a599b6c-7fdd-48c8-b32c-9e5d68d56634",
        ),
        (
            "2fb47abd-cc7f-400a-a599-f16c05c47a25",
            "d950c4b8-d77c-4544-bf0b-9d5d641a9e20",
        ),
        (
            "3807df28-95d3-4852-9409-1731679a7754",
            "8d0d7031-1549-4f17-97bf-d184c85fe1ad",
        ),
        (
            "3e6bc1c2-3830-4c5d-98e8-18104f2e8515",
            "90485757-bd1b-4ba6-a370-41d5989ec806",
        ),
        (
            "43986e10-a7f5-47fc-a256-69c832c0494d",
            "554400de-3639-443b-9618-bdb419b968f1",
        ),
        (
            "514f11a8-904c-4505-97cf-20ba719d712e",
            "83dcc6a0-37ee-474e-8691-08a326e9b5ed",
        ),
        (
            "564dd787-08c5-46cc-ab23-1a53f55c7b0a",
            "f1f9ce3c-77e9-42fd-b984-885ae9fc78f8",
        ),
        (
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
            "171c093a-8150-4520-929f-773811bc6967",
        ),
        (
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
            "514f11a8-904c-4505-97cf-20ba719d712e",
        ),
        (
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
            "92cf299a-1a2f-4ac0-a8c6-2733da4bf51c",
        ),
        (
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
            "ad23087f-4d89-4e6f-8d73-f08e70daf548",
        ),
        (
            "5aa0a992-fdc8-4c81-b708-263b7b8c39f6",
            "b3c4f17a-bdf9-4912-a5a6-87ce81a024ee",
        ),
        (
            "5e4a5bba-8134-4bee-a29f-db55159ac20f",
            "8d0d7031-1549-4f17-97bf-d184c85fe1ad",
        ),
        (
            "60f26fda-3e00-49ba-b185-a75be68ab985",
            "042c4718-69cc-4525-a402-363a8313c175",
        ),
        (
            "6cc1d62b-0bba-4298-823c-fba17619ff47",
            "43986e10-a7f5-47fc-a256-69c832c0494d",
        ),
        (
            "79f60d6e-554d-4f79-9dd7-0c7200410fcd",
            "fb827409-3fa1-40bb-8086-6740456a21bd",
        ),
        (
            "83dcc6a0-37ee-474e-8691-08a326e9b5ed",
            "98e23ac0-5952-4ad6-9c67-bdd03ce477d6",
        ),
        (
            "8651de9d-9bd9-471e-9b04-1d1ed987efc5",
            "b65787c9-5702-4828-89af-62548ff6a49d",
        ),
        (
            "90485757-bd1b-4ba6-a370-41d5989ec806",
            "8651de9d-9bd9-471e-9b04-1d1ed987efc5",
        ),
        (
            "90c3517a-38cd-4bf6-9d6e-bf9f3a699cc0",
            "99f4e9ab-35da-4677-875a-7d12574cbff5",
        ),
        (
            "92cf299a-1a2f-4ac0-a8c6-2733da4bf51c",
            "8651de9d-9bd9-471e-9b04-1d1ed987efc5",
        ),
        (
            "932f90cc-887f-44a3-a852-281a29319c4e",
            "ab1d2099-7ccf-46dc-acf0-db0ea86a1722",
        ),
        (
            "9485f3bb-5655-4f8f-a6d5-2bf233dcbb44",
            "6cc1d62b-0bba-4298-823c-fba17619ff47",
        ),
        (
            "9833ab4e-9aec-4425-9533-5dcba42d1815",
            "60f26fda-3e00-49ba-b185-a75be68ab985",
        ),
        (
            "98e23ac0-5952-4ad6-9c67-bdd03ce477d6",
            "3e6bc1c2-3830-4c5d-98e8-18104f2e8515",
        ),
        (
            "99f4e9ab-35da-4677-875a-7d12574cbff5",
            "b748ed9c-eddb-4839-aed3-3e052ee71356",
        ),
        (
            "a09d1cc7-91c7-4f0d-a7d7-3b790f3d0f43",
            "a635151d-937d-49fe-b545-b9b567ff5b15",
        ),
        (
            "ab1d2099-7ccf-46dc-acf0-db0ea86a1722",
            "1d9ab39a-40db-498b-8452-3303431ed517",
        ),
        (
            "ad23087f-4d89-4e6f-8d73-f08e70daf548",
            "eb632e6d-5a18-4ac7-a86b-3e0a03a40428",
        ),
        (
            "b1a89f3b-6a69-4261-9972-1b0d60b69ced",
            "90c3517a-38cd-4bf6-9d6e-bf9f3a699cc0",
        ),
        (
            "b3c4f17a-bdf9-4912-a5a6-87ce81a024ee",
            "eb632e6d-5a18-4ac7-a86b-3e0a03a40428",
        ),
        (
            "bac4d919-88fc-4b4c-8a11-57ce0d1e3d97",
            "bafab46e-ddc7-40c7-9a33-276cd9849a4e",
        ),
        (
            "bafab46e-ddc7-40c7-9a33-276cd9849a4e",
            "a09d1cc7-91c7-4f0d-a7d7-3b790f3d0f43",
        ),
        (
            "c86f2207-0b49-4375-a023-2eefad7d027d",
            "e0aa3383-af6e-40f2-8966-8846d7654af1",
        ),
        (
            "c94c34c2-3701-452d-b9f4-9baf2f108959",
            "564dd787-08c5-46cc-ab23-1a53f55c7b0a",
        ),
        (
            "d950c4b8-d77c-4544-bf0b-9d5d641a9e20",
            "9833ab4e-9aec-4425-9533-5dcba42d1815",
        ),
        (
            "db257175-afa0-4f2a-ba49-5ab41f47a6a1",
            "90c3517a-38cd-4bf6-9d6e-bf9f3a699cc0",
        ),
        (
            "e0aa3383-af6e-40f2-8966-8846d7654af1",
            "bac4d919-88fc-4b4c-8a11-57ce0d1e3d97",
        ),
        (
            "eb632e6d-5a18-4ac7-a86b-3e0a03a40428",
            "514f11a8-904c-4505-97cf-20ba719d712e",
        ),
        (
            "f3145cad-e9ad-4db5-b034-82f538c71f95",
            "564dd787-08c5-46cc-ab23-1a53f55c7b0a",
        ),
        (
            "f3cef032-488d-4c54-a5a6-03752c7d7ce0",
            "932f90cc-887f-44a3-a852-281a29319c4e",
        ),
        (
            "f8279a6a-cf6c-46f9-887f-17d9798b7118",
            "f3cef032-488d-4c54-a5a6-03752c7d7ce0",
        ),
        (
            "fb827409-3fa1-40bb-8086-6740456a21bd",
            "e849aa88-cf22-4751-a819-7b39abc9d4dd",
        ),
        (
            "fcb19b91-927c-4f1c-899d-c00a42d6cd76",
            "9485f3bb-5655-4f8f-a6d5-2bf233dcbb44",
        ),
        (
            "ffd35871-b965-49c2-aa8c-d5d59df057cf",
            "378a41dc-1b89-473f-81d3-82902722a479",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "KeycloakAuthenticationExecution",
            "id",
            "KeycloakAuthenticationExecution",
            "id",
            "NEXT_STEP",
            rel_direction_right=False,
        )
        == expected_rels
    )
