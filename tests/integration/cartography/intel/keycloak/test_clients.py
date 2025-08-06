from unittest.mock import patch

import requests

import cartography.intel.keycloak.clients
import tests.data.keycloak.clients
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.cartography.intel.keycloak.test_scopes import (
    _ensure_local_neo4j_has_test_scopes,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_clients(neo4j_session):
    cartography.intel.keycloak.clients.load_clients(
        neo4j_session,
        tests.data.keycloak.clients.KEYCLOAK_CLIENTS,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.clients,
    "get",
    return_value=tests.data.keycloak.clients.KEYCLOAK_CLIENTS,
)
def test_load_keycloak_clients(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_scopes(neo4j_session)

    # Act
    cartography.intel.keycloak.clients.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Clients exist
    expected_nodes = {
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "admin-cli",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "account-console",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "security-admin-console",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "realm-management",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "springfield-powerplant",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "admin-permissions",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "broker",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "account",
        ),
    }
    assert (
        check_nodes(neo4j_session, "KeycloakClient", ["id", "client_id"])
        == expected_nodes
    )

    # Assert Clients are connected with Realm
    expected_rels = {
        ("a683628e-fb67-4228-b29e-248a1c8b63d1", TEST_REALM),
        ("fa694007-ef2d-46e4-8e36-257ba5c23308", TEST_REALM),
        ("6876f461-9d47-4880-ae05-15c7023fbada", TEST_REALM),
        ("396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb", TEST_REALM),
        ("3c36cc2c-956b-4171-b076-250330547120", TEST_REALM),
        ("5e5d5c0b-46d1-454b-aa0d-e885f8290464", TEST_REALM),
        ("d042a0a5-1776-434a-a318-3f14ccd07ac9", TEST_REALM),
        ("92b51cf6-e996-4263-b375-67bcf9bab926", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakClient",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Clients are connected with Default Scopes
    expected_rels = {
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "0908dc73-29f1-4374-851e-fce191204d72",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "7f477610-425d-4836-b615-1a3b37d00773",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "f312d0c8-a00c-4651-b1de-11c568df7422",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakClient",
            "id",
            "KeycloakScope",
            "id",
            "HAS_DEFAULT_SCOPE",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert Clients are connected with Optional Scopes
    expected_rels = {
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "396ee90e-3db5-4bc9-bb1d-a9c119e8f7fb",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "3c36cc2c-956b-4171-b076-250330547120",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "5e5d5c0b-46d1-454b-aa0d-e885f8290464",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "6876f461-9d47-4880-ae05-15c7023fbada",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "17f2be1d-e95a-4f55-b56e-c60576f5cbf6",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "92b51cf6-e996-4263-b375-67bcf9bab926",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "17f2be1d-e95a-4f55-b56e-c60576f5cbf6",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "a683628e-fb67-4228-b29e-248a1c8b63d1",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "d042a0a5-1776-434a-a318-3f14ccd07ac9",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "2d557704-531d-479b-9720-c548985742a0",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "3729a739-d111-435f-8425-24596d4beae5",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
        ),
        (
            "fa694007-ef2d-46e4-8e36-257ba5c23308",
            "e824414b-facb-4277-90c1-a187b589ed7b",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakClient",
            "id",
            "KeycloakScope",
            "id",
            "HAS_OPTIONAL_SCOPE",
            rel_direction_right=True,
        )
        == expected_rels
    )
