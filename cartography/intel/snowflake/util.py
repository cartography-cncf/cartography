"""Shared plumbing for the Snowflake REST API v2 and the Snowflake SQL API.

Snowflake exposes two HTTP surfaces on the same host and the same bearer token:

- The **object API** (``/api/v2/<resource>``) lists and fetches objects. It covers
  most of the inventory but leaves whole security-relevant surfaces out (security
  and storage integrations, programmatic access tokens, MFA enrollment, shares,
  replication groups, account-level grants, policy attachments).
- The **SQL API** (``POST /api/v2/statements``) runs arbitrary ``SHOW`` /
  ``DESCRIBE`` / ``ACCOUNT_USAGE`` statements and fills those gaps.

Both are driven from one :class:`requests.Session` so a single credential,
retry policy and timeout apply to the whole module.
"""

import base64
import hashlib
import logging
import time
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from urllib.parse import quote

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from dateutil import parser as dateutil_parser
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each.
_TIMEOUT = (60, 60)
_RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)

# Snowflake caps a key-pair JWT at one hour regardless of the requested `exp`, so
# re-mint before that ceiling rather than at it.
_JWT_LIFETIME = timedelta(minutes=59)
_JWT_RENEW_MARGIN = timedelta(minutes=5)

# A request that runs longer than roughly 45 seconds returns 202 + Location
# instead of a body. Poll that URL until it resolves.
_ASYNC_POLL_INTERVAL_SECONDS = 2
_ASYNC_POLL_MAX_SECONDS = 900

# Statements that exceed this run server-side rather than being killed; the SQL
# API then answers 202 and we poll, same as the object API.
_SQL_STATEMENT_TIMEOUT_SECONDS = 300

# Snowflake error codes that mean "this account cannot answer that", as opposed
# to "the request was wrong". Callers treat these as skippable.
_SQL_UNAVAILABLE_MESSAGE_MARKERS = (
    "unsupported feature",
    "insufficient privileges",
    "does not exist or not authorized",
    "not authorized to perform this operation",
)


def iso_to_datetime(value: Any) -> datetime | None:
    """Parse a Snowflake timestamp into a timezone-aware ``datetime``.

    The object API returns RFC-3339 strings and the SQL API returns everything as
    a string, including epoch-seconds-with-fraction for ``TIMESTAMP_LTZ``
    columns. Both forms land here so callers never store epoch integers, per the
    repo's native-temporal convention.
    """
    if value in (None, ""):
        return None
    text = str(value)
    # The SQL API renders TIMESTAMP_* columns as "<epoch seconds>.<nanos> <tz
    # offset minutes>", which isoparse cannot read.
    epoch_part = text.split(" ", 1)[0]
    try:
        return datetime.fromtimestamp(float(epoch_part), tz=timezone.utc)
    except ValueError:
        return dateutil_parser.isoparse(text)


def schedule_to_text(value: Any) -> str | None:
    """Render a Snowflake schedule as a single readable string.

    Neo4j properties must be primitives, but the object API returns schedules as
    nested objects whose shape differs per resource: a task reports
    ``{"type": "USER_DEFINED", "seconds": 3600}`` or a cron expression, while an
    alert reports ``{"schedule_type": ..., "minutes": 60}``. Flattening them to one
    string keeps the property comparable across resource types.
    """
    if value in (None, "", {}):
        return None
    if not isinstance(value, dict):
        return str(value)
    if value.get("cron") or value.get("cron_expr"):
        expression = value.get("cron") or value.get("cron_expr")
        timezone_name = value.get("time_zone") or value.get("timezone")
        return f"USING CRON {expression} {timezone_name}".strip()
    # Snowflake reports every unit it knows about and zeroes the unused ones, so a
    # 60-minute schedule arrives as {"minutes": 60, "seconds": 0}. Picking the first
    # present unit would render that as "0 seconds", so only non-zero units count.
    for unit in ("hours", "minutes", "seconds"):
        if value.get(unit):
            return f"{value[unit]} {unit}"
    # An unrecognised shape still yields its discriminator rather than nothing.
    return str(value.get("type") or value.get("schedule_type") or value) or None


def datatype_of(value: Any) -> str | None:
    """Return the SQL datatype from a function or procedure return-type object.

    The object API reports a return type as
    ``{"type": "DATATYPE", "datatype": "FLOAT", "nullable": true}``; only the
    datatype itself is a useful graph property.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("datatype") or value.get("type")
    return str(value)


def normalize_account_id(account_id: str) -> str:
    """Return an account identifier in the canonical ``ORGNAME.ACCOUNTNAME`` form.

    Snowflake writes the same identifier two ways: ``MYORG-MYACCT`` in URLs and
    ``MYORG.MYACCT`` in SQL. Accept either so operators can paste whichever form
    their console shows them.

    Only the *first* separator is rewritten: an organization name cannot contain
    a hyphen, but an account name can, so replacing every hyphen would mangle an
    account called ``MY-ACCT``.
    """
    if not account_id:
        raise ValueError("Cannot normalize an empty Snowflake account id.")
    organization, separator, account = account_id.partition(".")
    if not separator:
        organization, separator, account = account_id.partition("-")
    if not separator or not organization or not account:
        raise ValueError(
            f"Snowflake account id {account_id!r} is not of the form "
            "ORGNAME-ACCOUNTNAME or ORGNAME.ACCOUNTNAME.",
        )
    return f"{organization.upper()}.{account.upper()}"


def hyphenated_account_id(account_id: str) -> str:
    """Return the ``ORGNAME-ACCOUNTNAME`` form used in key-pair JWT claims.

    The JWT ``iss`` and ``sub`` claims are ``<account_identifier>.<user>``, where
    the period is only the delimiter before the user name. Snowflake documents the
    account identifier itself as hyphen-separated and uppercase
    (``MYORGANIZATION-MYACCOUNT.MYUSER``), so passing the dotted SQL form would
    produce ``MYORG.MYACCT.SVC``, which Snowflake rejects.

    The graph keeps the dotted form for node ids; only the claims use this one.
    """
    organization, _, account = normalize_account_id(account_id).partition(".")
    return f"{organization}-{account}"


def account_host(account_id: str) -> str:
    """Return the API hostname for a Snowflake account identifier.

    The REST host uses a hyphen between the organization and the account name and
    is case-insensitive.
    """
    organization, _, account = normalize_account_id(account_id).partition(".")
    return f"https://{organization.lower()}-{account.lower()}.snowflakecomputing.com"


def sf_id(account_id: str, object_type: str, qualified_name: str) -> str:
    """Build an account-scoped, type-tagged node id.

    Snowflake object names are unique only within their own namespace *and* their
    own object type: a stage, a pipe, a stream and a task can all be named
    ``FOO`` in one schema, and a role and a warehouse can share a name at the
    account level. So unlike Databricks' ``uc_id``, the object type has to be
    part of the key or unrelated objects collapse onto a single Neo4j node.

    Every component must be non-empty: a blank account id would merge two
    Snowflake accounts into one graph.
    """
    if not account_id or not object_type or not qualified_name:
        raise ValueError(
            f"Cannot build a Snowflake id from account_id={account_id!r}, "
            f"object_type={object_type!r}, qualified_name={qualified_name!r}",
        )
    return f"{account_id}/{object_type}/{qualified_name}"


def _quote_identifier(part: str) -> str:
    """Quote an identifier component unless it is a plain uppercase identifier.

    Snowflake folds unquoted identifiers to uppercase, so ``ORDERS`` and
    ``orders`` are the same object, while a quoted ``"orders"`` is a different
    one. Normalising here (rather than in each transform) is what keeps a
    child's recomputed parent id byte-identical to the parent's own id.
    """
    is_bare_identifier = (part[:1].isalpha() or part[:1] == "_") and part.replace(
        "_", "A"
    ).replace("$", "A").isalnum()
    if is_bare_identifier and part.isupper():
        return part
    return '"' + part.replace('"', '""') + '"'


def sf_fqn(*parts: str) -> str:
    """Join identifier components into a dotted fully-qualified name.

    Used on both sides of every parent/child id computation, so that a table's
    ``parent_schema_id`` matches the schema node's own ``id`` exactly.
    """
    if not parts or any(not part for part in parts):
        raise ValueError(f"Cannot build a Snowflake FQN from parts={parts!r}")
    return ".".join(_quote_identifier(part) for part in parts)


def sf_path_segment(name: str) -> str:
    """Percent-encode a Snowflake object name for use as one REST path segment.

    A quoted Snowflake identifier may legally contain characters that are
    structural in a URL, so a name like ``my/db`` or ``prod?1`` interpolated raw
    would address a different endpoint than intended. Every character outside the
    unreserved set is escaped, including ``/``, so the name always stays a single
    segment.

    Deliberately not ``sf_fqn``: the REST path wants the *raw* Snowflake name,
    not the dotted quoted form. ``sf_fqn`` would embed literal double quotes,
    which Snowflake answers with a 404 for any database that needs quoting.
    """
    return quote(name, safe="")


def untag_image_path(reference: str | None) -> str | None:
    """Strip the tag or digest suffix from an image reference.

    The images endpoint reports ``image_path`` and ``SHOW SERVICE CONTAINERS``
    reports ``image_name``, both as ``/db/schema/repo/image:tag``. The two can carry
    different tags while pinning the same digest, so the tag has to come off before
    the paths can be compared. Matching on the untagged path together with the digest
    is what keeps a container attached to the one repository it actually pulled from,
    rather than to every repository holding a copy of the same bytes.

    A digest-pinned reference (``...@sha256:...``) is handled too. A colon is only
    treated as a tag separator when it follows the last ``/``, since a registry host
    may carry a port.
    """
    if not reference:
        return None
    path = reference.split("@", 1)[0]
    separator = path.rfind(":")
    if separator > path.rfind("/"):
        path = path[:separator]
    return path or None


def parse_stage_url(url: str | None) -> tuple[str | None, str | None]:
    """Return ``(scheme, container)`` for a Snowflake external storage URL.

    Handles ``s3://bucket/path`` and ``gcs://bucket/path`` (the bucket is the
    netloc) and ``azure://account.blob.core.windows.net/container/path`` (Azure
    puts the storage account in the netloc and the container in the first path
    segment, unlike the ``abfss://container@account`` form Databricks emits).
    Used to link stages and external volume storage locations to the S3 / GCS /
    Azure resources the aws / gcp / azure modules already ingested.
    """
    if not url:
        return None, None
    scheme, _, rest = url.partition("://")
    if not rest:
        return None, None
    scheme = scheme.lower()
    netloc, _, path = rest.partition("/")
    if scheme in ("azure", "azures"):
        # account.blob.core.windows.net -> account
        return scheme, (netloc.split(".", 1)[0] or None)
    return scheme, (netloc or None)


def skip_or_raise_http(error: requests.HTTPError, *skippable_statuses: int) -> None:
    """Re-raise an HTTP error unless its status is an expected, skippable one.

    Snowflake listings are fetched per parent (per database, per schema, ...) and
    the connecting role's ``USAGE`` grants decide what it can see. A ``403`` on
    an object the role cannot reach is expected; a transient ``5xx`` or an auth
    failure must abort the sync so the caller does NOT run cleanup on partial
    data and delete still-valid nodes.
    """
    status = error.response.status_code if error.response is not None else None
    if status not in skippable_statuses:
        raise error


def is_sql_unavailable(error: Exception) -> bool:
    """Whether a SQL API failure means the feature or privilege is absent.

    ``SHOW MASKING POLICIES`` errors outright on a Standard-edition account and
    ``ACCOUNT_USAGE`` views need ``IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE``.
    Neither is a bug, so callers skip that surface (and its cleanup) instead of
    failing the whole sync. Anything else propagates.
    """
    message = str(error).lower()
    return any(marker in message for marker in _SQL_UNAVAILABLE_MESSAGE_MARKERS)


def warn_unavailable(resource: str, reason: str) -> None:
    """Log that a surface was skipped, so an empty graph section is explainable."""
    logger.warning(
        "Snowflake %s is unavailable (%s) - skipping it and its cleanup.",
        resource,
        reason,
    )


def _http_error_detail(error: requests.HTTPError) -> str:
    """Return Snowflake's own error message for a failed request, if it sent one.

    Snowflake puts a numeric ``code`` and a human ``message`` in the JSON body
    (for example ``390432 / "Network policy is required."``), which is far more
    actionable than the status line alone.
    """
    response = error.response
    if response is None:
        return str(error)
    try:
        body = response.json()
    except ValueError:
        return str(error)
    message = body.get("message")
    if not message:
        return str(error)
    return f"Snowflake error {body.get('code')}: {message}"


class SnowflakeSqlError(RuntimeError):
    """A statement submitted to the Snowflake SQL API failed."""


class SnowflakeClient:
    """A thin client for the Snowflake REST API v2 and the Snowflake SQL API.

    Supports the two credential types the REST API accepts for a machine
    identity:

    - **Programmatic access token (PAT)**: a static bearer secret.
    - **Key-pair JWT**: an RS256 assertion signed with the user's private key and
      re-minted before Snowflake's hard one-hour ceiling.

    The object endpoints take no role parameter: they run as the user's default
    role (or the PAT's role restriction). Only the SQL API accepts an explicit
    role, so ``role`` is applied there and callers must pin the user's default
    role to match. See ``docs/root/modules/snowflake/config.md``.
    """

    def __init__(
        self,
        account_id: str,
        user: str,
        pat: str | None = None,
        private_key: str | None = None,
        private_key_passphrase: str | None = None,
        role: str | None = None,
        warehouse: str | None = None,
    ) -> None:
        if not pat and not private_key:
            raise ValueError("Must provide either pat or private_key.")
        self.account_id = normalize_account_id(account_id)
        self.host = account_host(account_id)
        self.user = user.upper()
        self.role = role
        self.warehouse = warehouse
        self._pat = pat
        self._private_key = private_key
        self._private_key_passphrase = private_key_passphrase
        self._jwt: str | None = None
        self._jwt_expiry: datetime | None = None
        self._session = requests.Session()
        retry_policy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=_RETRYABLE_STATUS_CODES,
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry_policy))
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "cartography",
            },
        )

    # -- authentication -----------------------------------------------------

    def _load_private_key(self) -> Any:
        passphrase = (
            self._private_key_passphrase.encode()
            if self._private_key_passphrase
            else None
        )
        return serialization.load_pem_private_key(
            self._private_key.encode(),  # type: ignore[union-attr]
            password=passphrase,
        )

    def _public_key_fingerprint(self, private_key: Any) -> str:
        """Return the ``SHA256:<base64>`` fingerprint Snowflake expects in ``iss``.

        Snowflake fingerprints the DER-encoded SubjectPublicKeyInfo of the public
        half of the key pair, which is what ``DESC USER`` reports as
        ``RSA_PUBLIC_KEY_FP``.
        """
        public_der = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        digest = hashlib.sha256(public_der).digest()
        return f"SHA256:{base64.b64encode(digest).decode()}"

    def _mint_jwt(self) -> tuple[str, datetime]:
        """Return a freshly signed ``(assertion, expiry)`` pair."""
        private_key = self._load_private_key()
        fingerprint = self._public_key_fingerprint(private_key)
        qualified_user = f"{hyphenated_account_id(self.account_id)}.{self.user.upper()}"
        now = datetime.now(tz=timezone.utc)
        expiry = now + _JWT_LIFETIME
        token = jwt.encode(
            {
                "iss": f"{qualified_user}.{fingerprint}",
                "sub": qualified_user,
                "iat": int(now.timestamp()),
                "exp": int(expiry.timestamp()),
            },
            private_key,
            algorithm="RS256",
        )
        logger.debug("Snowflake key-pair JWT minted, expires at %s.", expiry)
        return token, expiry

    def _authorization(self) -> tuple[str, str]:
        """Return the ``(bearer token, token type)`` pair for the next request."""
        if self._pat:
            return self._pat, "PROGRAMMATIC_ACCESS_TOKEN"
        now = datetime.now(tz=timezone.utc)
        if (
            self._jwt is None
            or self._jwt_expiry is None
            or self._jwt_expiry - _JWT_RENEW_MARGIN <= now
        ):
            self._jwt, self._jwt_expiry = self._mint_jwt()
        return self._jwt, "KEYPAIR_JWT"

    def _apply_auth(self) -> None:
        token, token_type = self._authorization()
        self._session.headers["Authorization"] = f"Bearer {token}"
        self._session.headers["X-Snowflake-Authorization-Token-Type"] = token_type

    # -- object API ---------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Issue one request, resolving Snowflake's 202 async handshake."""
        self._apply_auth()
        response = self._session.request(method, url, timeout=_TIMEOUT, **kwargs)
        if response.status_code == 202:
            response = self._await_async(response)
        response.raise_for_status()
        return response

    def _await_async(self, response: requests.Response) -> requests.Response:
        """Poll a 202 response's ``Location`` until the result is ready.

        Snowflake answers 202 for any request that outlives its synchronous
        budget (roughly 45 seconds), on both the object and SQL surfaces. The
        poll is bounded so a stuck statement fails the sync loudly rather than
        hanging it forever.
        """
        location = response.headers.get("Location")
        if not location:
            raise SnowflakeSqlError(
                "Snowflake returned 202 without a Location header; cannot poll "
                "for the result.",
            )
        url = self._absolute(location)
        deadline = time.monotonic() + _ASYNC_POLL_MAX_SECONDS
        while True:
            if time.monotonic() > deadline:
                raise SnowflakeSqlError(
                    f"Snowflake request did not complete within "
                    f"{_ASYNC_POLL_MAX_SECONDS}s: {url}",
                )
            time.sleep(_ASYNC_POLL_INTERVAL_SECONDS)
            self._apply_auth()
            polled = self._session.get(url, timeout=_TIMEOUT)
            if polled.status_code != 202:
                return polled

    def _absolute(self, url: str) -> str:
        """Resolve a possibly-relative API URL against the account host."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return f"{self.host}{url}"

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET one object endpoint and return the parsed JSON body."""
        return self._request("GET", f"{self.host}{path}", params=params or {}).json()

    def list_all(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Return every item from a paginated object listing.

        Snowflake list endpoints return a bare JSON array and advertise further
        pages through the ``Link`` response header, whose ``rel="next"`` URL
        points at ``/api/v2/results/{handle}?page=N``. The ``showLimit`` and
        ``fromName`` query params are ``SHOW ... LIMIT ... FROM`` filters, *not* a
        cursor, so following ``Link`` is the only correct way to paginate; mistaking
        the two silently truncates the graph and then cleanup deletes the
        difference.

        Follows the advertised URL verbatim rather than rebuilding it from the
        handle, and guards against a self-referential ``Link`` that would
        otherwise loop forever.
        """
        results: list[dict[str, Any]] = []
        url = f"{self.host}{path}"
        request_params: dict[str, Any] | None = params or {}
        seen_urls: set[str] = set()
        while True:
            response = self._request("GET", url, params=request_params)
            body = response.json()
            results.extend(body if isinstance(body, list) else [body])
            next_link = response.links.get("next", {}).get("url")
            if not next_link:
                return results
            next_url = self._absolute(next_link)
            if next_url in seen_urls:
                raise ValueError(
                    f"Snowflake listing {path} repeated page URL {next_url!r}; "
                    "aborting to avoid an infinite loop.",
                )
            seen_urls.add(next_url)
            url = next_url
            # The next-page URL already carries its own query string.
            request_params = None

    # -- SQL API ------------------------------------------------------------

    def run_sql(
        self,
        statement: str,
        database: str | None = None,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run one statement through the SQL API and return rows as dicts.

        This is how the module reaches everything the object API omits. Unlike
        the object endpoints, the SQL API accepts an explicit ``role``, so the
        configured role is pinned here.

        Every value comes back as a string (or ``None``), keyed by the lowercased
        column name, because ``SHOW`` output casing varies across Snowflake
        versions. Callers coerce.
        """
        payload: dict[str, Any] = {
            "statement": statement,
            "timeout": _SQL_STATEMENT_TIMEOUT_SECONDS,
        }
        if self.role:
            payload["role"] = self.role
        if self.warehouse:
            payload["warehouse"] = self.warehouse
        if database:
            payload["database"] = database
        if schema:
            payload["schema"] = schema

        try:
            response = self._request(
                "POST",
                f"{self.host}/api/v2/statements",
                params={"requestId": str(uuid.uuid4())},
                json=payload,
            )
        except requests.HTTPError as error:
            # Snowflake reports *why* a statement failed in the response body, not
            # in the status line. Surfacing it is what lets `is_sql_unavailable`
            # distinguish "Standard edition has no masking policies" from a real
            # failure, so re-raise with the message attached.
            raise SnowflakeSqlError(
                f"{_http_error_detail(error)} (statement: {statement})",
            ) from error
        body = response.json()
        metadata = body.get("resultSetMetaData") or {}
        columns = [
            str(column["name"]).lower() for column in metadata.get("rowType", [])
        ]
        rows: list[list[Any]] = list(body.get("data") or [])

        # A large result set is split into partitions; partition 0 arrives inline
        # and the rest have to be fetched or the listing is silently short.
        handle = body.get("statementHandle")
        partitions = metadata.get("partitionInfo") or []
        for partition in range(1, len(partitions)):
            page = self._request(
                "GET",
                f"{self.host}/api/v2/statements/{handle}",
                params={"partition": partition},
            ).json()
            rows.extend(page.get("data") or [])

        return [dict(zip(columns, row)) for row in rows]

    def describe(self, statement: str) -> dict[str, str | None]:
        """Run a ``DESCRIBE`` statement and fold its property rows into one dict.

        ``DESC INTEGRATION`` returns one row per property
        (``property``, ``property_type``, ``property_value``, ``property_default``)
        rather than one row per object, so integrations have to be flattened
        before they can be loaded as a node.
        """
        rows = self.run_sql(statement)
        properties: dict[str, str | None] = {}
        for row in rows:
            key = row.get("property")
            if key:
                properties[str(key).lower()] = row.get("property_value")
        return properties
