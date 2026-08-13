import base64
import hashlib
import json
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import jwt
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from cartography.intel.snowflake.util import account_host
from cartography.intel.snowflake.util import hyphenated_account_id
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import normalize_account_id
from cartography.intel.snowflake.util import parse_stage_url
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import untag_image_path

TEST_ACCOUNT = "MYORG.MYACCT"


def _build_client(port: int) -> SnowflakeClient:
    """A PAT client pointed at a local test server instead of Snowflake."""
    client = SnowflakeClient(TEST_ACCOUNT, "svc", pat="test-pat")
    client.host = f"http://127.0.0.1:{port}"
    client._session.mount("http://", client._session.adapters["https://"])
    return client


def _serve(handler: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server._thread = thread  # type: ignore[attr-defined]
    return server


def _shutdown(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()
    server._thread.join()  # type: ignore[attr-defined]


def _respond_json(handler: BaseHTTPRequestHandler, payload: object, **headers: str):
    body = json.dumps(payload).encode()
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    for name, value in headers.items():
        handler.send_header(name.replace("_", "-"), value)
    handler.end_headers()
    handler.wfile.write(body)


class _LinkPaginationHandler(BaseHTTPRequestHandler):
    """Serves a two-page listing advertised through the Link header."""

    requested_paths: list[str] = []

    def do_GET(self) -> None:
        type(self).requested_paths.append(self.path)
        if self.path.startswith("/api/v2/roles"):
            _respond_json(
                self,
                [{"name": "ROLE_ONE"}],
                Link='</api/v2/results/handle-1?page=1>; rel="next", '
                '</api/v2/results/handle-1?page=1>; rel="last"',
            )
            return
        _respond_json(self, [{"name": "ROLE_TWO"}])

    def log_message(self, format: str, *args: object) -> None:
        pass


class _SelfReferentialLinkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        _respond_json(
            self,
            [{"name": "ROLE_ONE"}],
            Link='</api/v2/results/handle-1?page=1>; rel="next"',
        )

    def log_message(self, format: str, *args: object) -> None:
        pass


class _AsyncAcceptedHandler(BaseHTTPRequestHandler):
    """Answers 202 + Location once, then serves the result."""

    polled = 0

    def do_GET(self) -> None:
        if self.path.startswith("/api/v2/warehouses"):
            self.send_response(202)
            self.send_header("Location", "/api/v2/results/handle-async")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        type(self).polled += 1
        _respond_json(self, [{"name": "WH"}])

    def log_message(self, format: str, *args: object) -> None:
        pass


class _SqlHandler(BaseHTTPRequestHandler):
    """A SQL API that returns one inline partition plus one fetched partition."""

    def do_POST(self) -> None:
        _respond_json(
            self,
            {
                "statementHandle": "handle-sql",
                "resultSetMetaData": {
                    "rowType": [{"name": "NAME"}, {"name": "created_on"}],
                    "partitionInfo": [{"rowCount": 1}, {"rowCount": 1}],
                },
                "data": [["ROLE_ONE", "1751412460.000"]],
            },
        )

    def do_GET(self) -> None:
        _respond_json(self, {"data": [["ROLE_TWO", "1751412461.000"]]})

    def log_message(self, format: str, *args: object) -> None:
        pass


class _SqlErrorHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = json.dumps(
            {"code": "002003", "message": "Unsupported feature 'MASKING POLICY'."},
        ).encode()
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_list_follows_link_header_across_pages():
    # Arrange
    _LinkPaginationHandler.requested_paths = []
    server = _serve(_LinkPaginationHandler)
    client = _build_client(server.server_port)

    try:
        # Act
        result = client.list_all("/api/v2/roles")
    finally:
        _shutdown(server)

    # Assert: both pages are returned, and the second request used the URL the
    # Link header advertised rather than a rebuilt one.
    assert result == [{"name": "ROLE_ONE"}, {"name": "ROLE_TWO"}]
    assert _LinkPaginationHandler.requested_paths[1] == (
        "/api/v2/results/handle-1?page=1"
    )


def test_list_aborts_on_self_referential_link():
    # Arrange
    server = _serve(_SelfReferentialLinkHandler)
    client = _build_client(server.server_port)

    try:
        # Act + Assert: a Link header pointing at itself must fail loudly rather
        # than loop forever.
        with pytest.raises(ValueError, match="repeated page URL"):
            client.list_all("/api/v2/results/handle-1")
    finally:
        _shutdown(server)


def test_request_resolves_202_by_polling_location(mocker):
    # Arrange
    _AsyncAcceptedHandler.polled = 0
    server = _serve(_AsyncAcceptedHandler)
    client = _build_client(server.server_port)
    mocker.patch("cartography.intel.snowflake.util.time.sleep")

    try:
        # Act
        result = client.list_all("/api/v2/warehouses")
    finally:
        _shutdown(server)

    # Assert
    assert result == [{"name": "WH"}]
    assert _AsyncAcceptedHandler.polled == 1


def test_run_sql_returns_all_partitions_keyed_by_lowercase_column():
    # Arrange
    server = _serve(_SqlHandler)
    client = _build_client(server.server_port)

    try:
        # Act
        rows = client.run_sql("SHOW ROLES")
    finally:
        _shutdown(server)

    # Assert: the inline partition and the fetched one are both present, and
    # column names are lowercased because SHOW output casing varies by version.
    assert rows == [
        {"name": "ROLE_ONE", "created_on": "1751412460.000"},
        {"name": "ROLE_TWO", "created_on": "1751412461.000"},
    ]


def test_run_sql_surfaces_snowflake_error_message():
    # Arrange
    server = _serve(_SqlErrorHandler)
    client = _build_client(server.server_port)

    try:
        # Act
        with pytest.raises(SnowflakeSqlError) as caught:
            client.run_sql("SHOW MASKING POLICIES IN ACCOUNT")
    finally:
        _shutdown(server)

    # Assert: the body's message reaches the caller, so is_sql_unavailable can
    # tell an edition limitation from a real failure.
    assert "Unsupported feature" in str(caught.value)
    assert is_sql_unavailable(caught.value)


def test_pat_and_keypair_produce_different_token_types(mocker):
    # Arrange
    pat_client = SnowflakeClient(TEST_ACCOUNT, "svc", pat="test-pat")
    key_client = SnowflakeClient(TEST_ACCOUNT, "svc", private_key="unused")
    mocker.patch.object(
        key_client,
        "_mint_jwt",
        return_value=("minted-jwt", datetime.now(tz=timezone.utc) + timedelta(hours=1)),
    )

    # Act
    pat_token, pat_type = pat_client._authorization()
    key_token, key_type = key_client._authorization()

    # Assert
    assert (pat_token, pat_type) == ("test-pat", "PROGRAMMATIC_ACCESS_TOKEN")
    assert (key_token, key_type) == ("minted-jwt", "KEYPAIR_JWT")


def test_keypair_jwt_is_reused_until_it_nears_expiry(mocker):
    # Arrange
    client = SnowflakeClient(TEST_ACCOUNT, "svc", private_key="unused")
    mint = mocker.patch.object(
        client,
        "_mint_jwt",
        return_value=("minted-jwt", datetime.now(tz=timezone.utc) + timedelta(hours=1)),
    )

    # Act
    client._authorization()
    client._authorization()

    # Assert: Snowflake caps a JWT at one hour, so it is minted once and reused
    # until the renewal margin, not re-minted per request.
    assert mint.call_count == 1

    # Act: once the cached assertion is inside the renewal margin it is re-minted.
    client._jwt_expiry = datetime.now(tz=timezone.utc) + timedelta(minutes=1)
    client._authorization()

    # Assert
    assert mint.call_count == 2


def test_mint_jwt_signs_the_claims_snowflake_expects():
    # Arrange: a real key pair, so the RS256 signing path is genuinely exercised.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    client = SnowflakeClient(TEST_ACCOUNT, "svc", private_key=pem)

    # Act
    token, expiry = client._mint_jwt()
    claims = jwt.decode(token, private_key.public_key(), algorithms=["RS256"])

    # Assert: Snowflake requires an uppercase <ACCOUNT_IDENTIFIER>.<USER> subject and
    # an issuer suffixed with the public key's SHA256 fingerprint. The account
    # identifier is hyphen-separated (MYORGANIZATION-MYACCOUNT.MYUSER in Snowflake's
    # own example); the dotted SQL form is rejected, so the client must not use the
    # account id it keys graph nodes on.
    assert claims["sub"] == "MYORG-MYACCT.SVC"
    assert claims["iss"].startswith("MYORG-MYACCT.SVC.SHA256:")
    # Snowflake caps the assertion at one hour, so never request more.
    assert expiry - datetime.now(tz=timezone.utc) <= timedelta(hours=1)


def test_mint_jwt_fingerprint_matches_snowflakes_definition():
    # Arrange
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    client = SnowflakeClient(TEST_ACCOUNT, "svc", private_key=pem)

    # Act
    fingerprint = client._public_key_fingerprint(private_key)

    # Assert: Snowflake fingerprints the DER SubjectPublicKeyInfo, which is what
    # DESC USER reports as RSA_PUBLIC_KEY_FP. Recompute it independently here.
    expected_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    expected = (
        "SHA256:" + base64.b64encode(hashlib.sha256(expected_der).digest()).decode()
    )
    assert fingerprint == expected


def test_client_requires_a_credential():
    with pytest.raises(ValueError, match="either pat or private_key"):
        SnowflakeClient(TEST_ACCOUNT, "svc")


def test_account_host_accepts_either_separator():
    assert account_host("MYORG.MYACCT") == "https://myorg-myacct.snowflakecomputing.com"
    assert account_host("myorg-myacct") == "https://myorg-myacct.snowflakecomputing.com"
    with pytest.raises(ValueError):
        account_host("")


def test_normalize_account_id_only_rewrites_the_first_separator():
    assert normalize_account_id("myorg-myacct") == "MYORG.MYACCT"
    assert normalize_account_id("MYORG.MYACCT") == "MYORG.MYACCT"
    # An organization name cannot contain a hyphen but an account name can, so
    # only the first separator is a separator.
    assert normalize_account_id("myorg-my-acct") == "MYORG.MY-ACCT"
    assert (
        account_host("myorg-my-acct") == "https://myorg-my-acct.snowflakecomputing.com"
    )
    for bad in ("", "noseparator", "-myacct", "myorg-"):
        with pytest.raises(ValueError):
            normalize_account_id(bad)


def test_sf_id_is_account_scoped_and_type_tagged():
    # A role and a warehouse can share a name, so the type segment is what keeps
    # them on separate nodes.
    assert sf_id(TEST_ACCOUNT, "role", "SYSADMIN") == "MYORG.MYACCT/role/SYSADMIN"
    assert sf_id(TEST_ACCOUNT, "warehouse", "SYSADMIN") != sf_id(
        TEST_ACCOUNT, "role", "SYSADMIN"
    )
    for bad in (("", "role", "X"), (TEST_ACCOUNT, "", "X"), (TEST_ACCOUNT, "role", "")):
        with pytest.raises(ValueError):
            sf_id(*bad)


def test_sf_fqn_quotes_only_non_uppercase_identifiers():
    assert sf_fqn("PROD", "SALES", "ORDERS") == "PROD.SALES.ORDERS"
    assert sf_fqn("PROD", "MY_SCHEMA", "T1") == "PROD.MY_SCHEMA.T1"
    # A lowercase or space-bearing name was created quoted and stays a distinct
    # object, so the id has to keep the quotes.
    assert sf_fqn("PROD", "sales") == 'PROD."sales"'
    assert sf_fqn("PROD", "my schema") == 'PROD."my schema"'
    assert sf_fqn("PROD", 'we"ird') == 'PROD."we""ird"'
    # Snowflake requires quoting an identifier that does not start with a letter.
    assert sf_fqn("PROD", "1DB") == 'PROD."1DB"'
    with pytest.raises(ValueError):
        sf_fqn("PROD", "")


def test_sf_path_segment_escapes_url_significant_characters():
    # A plain identifier is left alone, so the common case produces a readable URL.
    assert sf_path_segment("PROD") == "PROD"
    assert sf_path_segment("MY_DB$1") == "MY_DB%241"
    # A quoted Snowflake name may contain characters that are structural in a URL.
    # Each has to be escaped, or the request addresses a different endpoint.
    assert sf_path_segment("my/db") == "my%2Fdb"
    assert sf_path_segment("prod?1") == "prod%3F1"
    assert sf_path_segment("a b") == "a%20b"
    assert sf_path_segment("d#1") == "d%231"
    # Not the dotted quoted form: the REST path wants the raw name.
    assert sf_path_segment("sales") == "sales"


def test_hyphenated_account_id_accepts_either_input_form():
    # Both spellings of the same account produce the one form the JWT claims need.
    assert hyphenated_account_id("MYORG.MYACCT") == "MYORG-MYACCT"
    assert hyphenated_account_id("myorg-myacct") == "MYORG-MYACCT"
    # An account name may itself contain a hyphen; only the first separator splits.
    assert hyphenated_account_id("MYORG.MY-ACCT") == "MYORG-MY-ACCT"


def test_untag_image_path_strips_tags_and_digests():
    assert untag_image_path("/db/schema/repo/img:latest") == "/db/schema/repo/img"
    assert untag_image_path("/db/schema/repo/img:v3") == "/db/schema/repo/img"
    # A digest-pinned reference resolves to the same path as a tagged one, so a
    # container written either way matches the same image.
    assert untag_image_path("/db/schema/repo/img@sha256:abc") == "/db/schema/repo/img"
    # An untagged reference is already the answer.
    assert untag_image_path("/db/schema/repo/img") == "/db/schema/repo/img"
    # A registry host port is not a tag: the colon precedes the last slash.
    assert (
        untag_image_path("registry.example.com:5000/db/repo/img")
        == "registry.example.com:5000/db/repo/img"
    )
    assert untag_image_path(None) is None
    assert untag_image_path("") is None


def test_parse_stage_url():
    assert parse_stage_url("s3://my-bucket/path") == ("s3", "my-bucket")
    assert parse_stage_url("gcs://my-bucket/path") == ("gcs", "my-bucket")
    # Azure puts the storage account in the netloc, unlike the abfss:// form.
    assert parse_stage_url("azure://acct.blob.core.windows.net/container/path") == (
        "azure",
        "acct",
    )
    assert parse_stage_url(None) == (None, None)
    assert parse_stage_url("") == (None, None)
    assert parse_stage_url("not-a-url") == (None, None)


def test_iso_to_datetime_handles_both_api_formats():
    # The object API returns RFC-3339.
    parsed = iso_to_datetime("2026-07-01T23:27:40Z")
    assert parsed is not None and parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).hour == 23
    # The SQL API returns epoch seconds with a trailing timezone-offset field.
    epoch = iso_to_datetime("1751412460.000 1440")
    assert epoch is not None and epoch.tzinfo is not None
    assert epoch.astimezone(timezone.utc).year == 2025
    assert iso_to_datetime(None) is None
    assert iso_to_datetime("") is None


def test_skip_or_raise_http_only_swallows_expected_statuses():
    response = requests.Response()
    response.status_code = 403
    error = requests.HTTPError(response=response)
    # A role without USAGE on an object is expected and skippable.
    skip_or_raise_http(error, 403, 404)
    # A 500 must abort the sync so cleanup does not run on partial data.
    response.status_code = 500
    with pytest.raises(requests.HTTPError):
        skip_or_raise_http(error, 403, 404)


def test_is_sql_unavailable_distinguishes_gating_from_failure():
    assert is_sql_unavailable(SnowflakeSqlError("Unsupported feature 'X'."))
    assert is_sql_unavailable(SnowflakeSqlError("Insufficient privileges to operate"))
    assert not is_sql_unavailable(SnowflakeSqlError("Syntax error at line 1"))
