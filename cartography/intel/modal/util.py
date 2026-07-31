"""Adapter over the Modal API.

This is the only module in the Modal integration that imports the ``modal`` SDK or
``modal_proto``, and the only place ``client.stub`` is touched. Every helper here returns
plain ``dict`` / ``list[dict]``, so the per-resource intel modules (and their tests) never
see protobuf messages or SDK handles.

Modal has no public REST API: everything is gRPC behind the Python client. A large part of
the inventory (apps, app layout, sandbox detail, NFS shares, image tags, tasks, clusters,
service users, richer member and environment records, proxies, domains, environment role
principals) is reachable *only* through Modal's internal gRPC protocol defined in
``modal_proto.api_pb2``.

Modal does document a public listing surface for some objects
(``Secret``/``Volume``/``Dict``/``Queue``/``Environment.objects.list()``, ``Sandbox.list``,
``modal.experimental.get_app_objects``), but we deliberately do **not** use it. Those
helpers are wrapped by ``synchronizer.create_blocking``, and calling either the blocking
form or its ``.aio`` variant from our own event loop deadlocks with
``RPC request ... made outside of task context``. Verified against modal 1.5.3. Using the
raw RPCs for everything also keeps the whole adapter on one uniform mechanism and yields
the object ids that the public CLI output omits.

The stub methods are called bare rather than through ``retry_transient_errors``. Each one is
a ``modal._grpc_client.UnaryUnaryWrapper`` that already applies Modal's own retry policy by
default, which is how Modal's own code calls them; wrapping them again nested the two policies
and allowed up to nine attempts for a single logical request.

PRIVATE PROTOCOL WARNING
------------------------
The ``client.stub.<Rpc>`` calls below, and the ``modal.client._Client`` /
``modal._workspace._Workspace`` private classes, are unversioned Modal internals and may
change or disappear in any Modal release. They are confined to this module on purpose: a
protocol break should require edits here and nowhere else. The dependency is pinned
``modal>=1.5.3,<2`` for that reason.

NOTE ON ``@timeit``
-------------------
The helpers below are intentionally NOT decorated with ``@timeit``, unlike the ``sync()``
functions that call them. ``timeit``'s wrapper is synchronous: applied to a coroutine
function it calls ``method(...)``, which returns a coroutine immediately, so the timer
measures coroutine *creation* rather than the awaited request. The timing would be
meaningless. Worse, ``functools.wraps`` does not preserve coroutine-ness, so
``inspect.iscoroutinefunction()`` becomes False and ``unittest.mock.patch.object`` then
substitutes a ``MagicMock`` instead of an ``AsyncMock`` — which breaks every test that
mocks these functions with ``TypeError: object dict can't be used in 'await' expression``.

Everything is async. ``_Client.from_credentials`` opens its own gRPC connection, and that
connection is bound to the event loop that created it, so the client must be created and
used inside a single loop. ``start_modal_ingestion`` therefore runs one ``asyncio.run()``
for the whole module, mirroring ``cartography.intel.microsoft.entra``.
"""

import asyncio
import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import modal
from google.protobuf.empty_pb2 import Empty
from google.protobuf.timestamp_pb2 import Timestamp
from grpclib.const import Status
from grpclib.exceptions import GRPCError
from grpclib.exceptions import StreamTerminatedError
from modal._utils.time_utils import as_timestamp
from modal._workspace import _Workspace
from modal.client import _Client
from modal_proto import api_pb2

logger = logging.getLogger(__name__)

# Errors raised by the Modal client and the underlying gRPC transport. The entry point
# catches these to isolate a failing resource without aborting the whole module, so it is
# exported from here to keep `modal` imports out of every other file.
#
# Deliberately does NOT include the builtin OSError. These exceptions gate a "skip this
# resource and keep its existing data" path, which must only be reachable for failures we
# recognise as Modal request failures. OSError is far broader than that and would let local
# or infrastructure faults be laundered into a partial success. Modal surfaces genuine
# connection problems as modal.exception.ConnectionError (its own class, not the builtin),
# and grpclib raises GRPCError / StreamTerminatedError, so nothing is lost.
MODAL_API_ERRORS: tuple[type[Exception], ...] = (
    GRPCError,
    StreamTerminatedError,
    modal.exception.NotFoundError,
    modal.exception.AuthError,
    modal.exception.ConnectionError,
    modal.exception.RemoteError,
    modal.exception.InvalidError,
)

# `ImageListTags` is the one listing that pages with an opaque token. Modal's own CLI
# sleeps 1s between pages, so we mirror that to stay polite.
_IMAGE_PAGE_DELAY_SECONDS = 1.0

# Server-side cap on `ListPagination.max_objects`, per Modal's own public managers.
_LIST_PAGE_SIZE = 100

# `SandboxList` pages by walking `before_timestamp` backwards. Termination relies on
# timestamps strictly decreasing; this cap keeps a pathological page boundary (several
# sandboxes sharing one timestamp) from looping forever. Hitting it means enumeration was
# partial, which the caller must treat as "do not clean up".
_SANDBOX_PAGE_LIMIT = 200


class ModalClient:
    """Owns an open Modal client and the workspace it authenticates to.

    Construct with :meth:`create` (the constructor cannot be async). All the module-level
    ``get_*`` / ``list_*`` helpers take one of these.
    """

    def __init__(self, client: _Client) -> None:
        self._client = client

    @classmethod
    async def create(cls, token_id: str, token_secret: str) -> "ModalClient":
        return cls(await _Client.from_credentials(token_id, token_secret))

    @property
    def stub(self) -> Any:
        """The default control-plane stub. Private Modal protocol, see module docstring."""
        return self._client.stub

    @property
    def raw(self) -> _Client:
        """The underlying async client, for the public SDK calls that take ``client=``."""
        return self._client


def _timestamp(value: Any) -> datetime | None:
    """Convert a Modal timestamp to an aware datetime.

    Modal's protocol is inconsistent here: most messages use an epoch-seconds double and
    leave unset values at 0.0, but `TokenInfoGetResponse` uses a
    ``google.protobuf.Timestamp`` message, whose unset value is also epoch 0. Both are
    accepted so callers do not have to care. Neo4j stores native temporal types, so this
    returns a datetime rather than an epoch number.
    """
    if value is None:
        return None
    if isinstance(value, Timestamp):
        seconds = value.seconds + value.nanos / 1000000000
    else:
        seconds = value
    if not seconds:
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def _enum_name(enum_wrapper: Any, value: int) -> str | None:
    """Resolve a protobuf enum value to its member name.

    Raw graph values are the member names (e.g. ``APP_STATE_DEPLOYED``) rather than ints:
    they are stable, readable, and are what the ontology mapping dicts key on.
    """
    try:
        return enum_wrapper.Name(value)
    except ValueError:
        logger.debug("Unknown Modal enum value %s for %s", value, enum_wrapper)
        return None


def _optional_str(value: str) -> str | None:
    """Protobuf string fields default to ''; the graph wants None for "absent"."""
    return value or None


async def _paginate(
    client: ModalClient,
    rpc: Any,
    request_cls: Any,
    environment_name: str,
    items_field: str,
) -> list[Any]:
    """Drain a `ListPagination`-style listing for one environment.

    Modal's named-object listings (secrets, volumes, dicts, queues) all page the same way:
    100 items at a time, walking ``created_before`` backwards, ending on a short page. This
    mirrors the loop in Modal's own public managers (see ``modal/secret.py``).
    """
    items: list[Any] = []
    created_before = as_timestamp(None)
    while True:
        response = await rpc(
            request_cls(
                environment_name=environment_name,
                pagination=api_pb2.ListPagination(
                    max_objects=_LIST_PAGE_SIZE,
                    created_before=created_before,
                ),
            )
        )
        page = list(getattr(response, items_field))
        items.extend(page)
        if len(page) < _LIST_PAGE_SIZE:
            return items
        created_before = page[-1].metadata.creation_info.created_at


# =============================================================================
# Workspace and environments
# =============================================================================


async def get_workspace(client: ModalClient) -> dict[str, Any]:
    """Return the workspace the credentials authenticate against.

    Two RPCs: `TokenInfoGet` is the only source of the workspace id (and identifies the
    credential doing the sync), `WorkspaceNameLookup` supplies the URL slug that web
    endpoint hostnames embed.
    """
    token_info = await client.stub.TokenInfoGet(api_pb2.TokenInfoGetRequest())
    name_lookup = await client.stub.WorkspaceNameLookup(Empty())
    # Exactly one identity is populated: a personal user token or a service user token.
    # Which one performed the sync is worth recording, because a workspace inventoried
    # with someone's personal token is a different operational posture from one using a
    # dedicated least-privilege service user.
    if token_info.HasField("service_user_identity"):
        principal_type = "service_user"
        principal_id = token_info.service_user_identity.service_user_id
        principal_name = token_info.service_user_identity.service_user_name
    elif token_info.HasField("user_identity"):
        principal_type = "user"
        principal_id = token_info.user_identity.user_id
        principal_name = token_info.user_identity.username
    else:
        principal_type = None
        principal_id = ""
        principal_name = ""

    return {
        "id": token_info.workspace_id,
        "name": _optional_str(token_info.workspace_name),
        "slug": _optional_str(name_lookup.username),
        "synced_with_token_id": _optional_str(token_info.token_id),
        "synced_with_token_name": _optional_str(token_info.token_name),
        "synced_with_principal_type": principal_type,
        "synced_with_principal_id": _optional_str(principal_id),
        "synced_with_principal_name": _optional_str(principal_name),
        "synced_with_token_expires_at": _timestamp(token_info.expires_at),
    }


async def list_environments(client: ModalClient) -> list[dict[str, Any]]:
    """List every environment in the workspace.

    Uses the private `EnvironmentList` rather than the public
    `modal.Environment.objects.list()` because the public manager discards everything
    except name / id / webhook suffix, and we want the concurrency limits too.
    """
    response = await client.stub.EnvironmentList(Empty())
    return [
        {
            "id": item.environment_id,
            "name": item.name,
            "webhook_suffix": _optional_str(item.webhook_suffix),
            "created_at": _timestamp(item.created_at),
            "is_default": item.default,
            "is_managed": item.is_managed,
            "environment_type": _enum_name(
                api_pb2.EnvironmentType, item.environment_type
            ),
            "max_concurrent_tasks": item.max_concurrent_tasks,
            "max_concurrent_gpus": item.max_concurrent_gpus,
            "current_concurrent_tasks": item.current_concurrent_tasks,
            "current_concurrent_gpus": item.current_concurrent_gpus,
            # Availability signal. The cost figures on this message
            # (cycle_budget_dollars, current_cycle_usage, ...) are out of scope.
            "spend_limit_reached": item.spend_limit_reached,
        }
        for item in response.items
    ]


# =============================================================================
# Identity and access (workspace-global)
# =============================================================================


async def list_workspace_members(client: ModalClient) -> list[dict[str, Any]]:
    """List workspace members.

    Uses the private `WorkspaceMembersList` rather than `Workspace.members.list()`: the
    public dataclass drops `identity_provider_type` and `idp_external_id`, which are the
    fields that make non-SSO members in an SSO workspace queryable.
    """
    response = await client.stub.WorkspaceMembersList(Empty())
    return [
        {
            "id": item.user_id,
            "member_id": _optional_str(item.member_id),
            "email": _optional_str(item.email),
            "display_name": _optional_str(item.member_displayname),
            "member_role": _enum_name(api_pb2.MemberRole, item.member_role),
            "identity_provider_type": _enum_name(
                api_pb2.IdentityProviderType, item.identity_provider_type
            ),
            "idp_external_id": _optional_str(item.idp_external_id),
            "avatar_url": _optional_str(item.avatar_url),
            "joined_at": _timestamp(item.joined_at),
            "last_active_at": _timestamp(item.last_active_at),
            "deleted_at": _timestamp(item.deleted_at),
        }
        for item in response.members
    ]


async def list_service_users(client: ModalClient) -> list[dict[str, Any]]:
    """List service users, i.e. the workspace's machine identities and API tokens.

    Private `ServiceUserList`; there is no CLI or public Python equivalent. `token_id` is
    the `ak-` API token id, and `last_used_at` is what makes stale-credential detection
    possible.
    """
    response = await client.stub.ServiceUserList(Empty())
    return [
        {
            "id": item.service_user_id,
            "name": _optional_str(item.name),
            "token_id": _optional_str(item.token_id),
            "created_by": _optional_str(item.created_by),
            "created_at": _timestamp(item.created_at),
            "last_used_at": _timestamp(item.last_used_at),
        }
        for item in response.service_users
    ]


async def list_proxy_tokens(client: ModalClient) -> list[dict[str, Any]]:
    """List proxy auth tokens (public SDK).

    An unscoped proxy token authenticates against every proxy-auth-protected web endpoint
    in the workspace, so `scoped` is the interesting field here.
    """
    workspace = _Workspace.from_context(client=client.raw)
    tokens = await workspace.proxy_tokens.list()
    return [
        {
            "id": token.token_id,
            "token_id": token.token_id,
            "created_at": token.created_at,
            "scoped": token.scoped,
        }
        for token in tokens
    ]


async def list_domains(client: ModalClient) -> tuple[list[dict[str, Any]], bool]:
    """List custom domains, each with its validation DNS records flattened out.

    Returns ``(domains, available)``. ``available`` is False when the workspace does not
    have the custom-domains add-on, in which case `DomainList` answers UNIMPLEMENTED and we
    learned nothing about its domains. That is deliberately NOT reported as an empty list:
    an empty list would let the caller's cleanup delete previously-ingested domains, which
    is the same "failed enumeration must not clean up" rule the rest of this module follows.
    Any other gRPC status propagates.

    Each dict carries a nested ``dns_records`` list, which the intel module splits into
    `ModalDomain` and `ModalDomainDNSRecord` rows.
    """
    try:
        response = await client.stub.DomainList(api_pb2.DomainListRequest())
    except GRPCError as exc:
        if exc.status is Status.UNIMPLEMENTED:
            logger.info(
                "Modal DomainList is not available for this workspace "
                "(custom domains are a paid add-on); skipping domain ingestion.",
            )
            return [], False
        raise
    domains = []
    for item in response.domains:
        domains.append(
            {
                "id": item.domain_id,
                "domain_name": item.domain_name,
                "created_at": _timestamp(item.created_at),
                "certificate_status": _enum_name(
                    api_pb2.CertificateStatus, item.certificate_status
                ),
                "dns_records": [
                    {
                        "type": _enum_name(api_pb2.DNSRecordType, record.type),
                        "name": _optional_str(record.name),
                        "value": _optional_str(record.value),
                    }
                    for record in item.dns_records
                ],
            }
        )
    return domains, True


async def get_environment_roles(
    client: ModalClient, environment_id: str
) -> list[dict[str, Any]]:
    """Return the role bindings for one environment.

    Note this RPC keys on the environment *id*, unlike every other environment-scoped
    call, which keys on the name. Each principal is either a user or a service user;
    exactly one of ``user_id`` / ``service_user_id`` is set.
    """
    response = await client.stub.EnvironmentGetRoles(
        api_pb2.EnvironmentGetRolesRequest(environment_id=environment_id)
    )
    return [
        {
            "user_id": _optional_str(principal.user_id),
            "service_user_id": _optional_str(principal.service_user_id),
            "email": _optional_str(principal.email),
            "user_name": _optional_str(principal.user_name),
            "service_user_name": _optional_str(principal.service_user_name),
            "role": _enum_name(api_pb2.EnvironmentRole, principal.role),
        }
        for principal in response.principal_roles
    ]


# =============================================================================
# Apps, functions and classes
# =============================================================================


async def list_apps(client: ModalClient, environment_name: str) -> list[dict[str, Any]]:
    """List apps in an environment (private `AppList`, unpaginated).

    There is no public app listing API at all: no ``modal.App.list()``, and
    ``App.registered_functions`` is documented as build-phase-only.
    """
    response = await client.stub.AppList(
        api_pb2.AppListRequest(environment_name=environment_name)
    )
    return [
        {
            "id": item.app_id,
            # Ephemeral apps have no name; the description is the only human label.
            "name": _optional_str(item.name),
            "description": _optional_str(item.description),
            "state": _enum_name(api_pb2.AppState, item.state),
            "created_at": _timestamp(item.created_at),
            "stopped_at": _timestamp(item.stopped_at),
            "n_running_tasks": item.n_running_tasks,
        }
        for item in response.apps
    ]


async def get_app_layout(client: ModalClient, app_id: str) -> dict[str, Any]:
    """Return an app's functions and classes, with function handle metadata.

    Private `AppGetLayout`, one call per app. This is the only way to enumerate a deployed
    app's functions: there is no public app listing, and ``App.registered_functions`` is
    documented as build-phase-only.

    The response carries both ``{name: id}`` maps and an ``objects`` list holding the
    handle metadata, so name and metadata are joined here on the object id. That keeps
    everything on the raw protocol: ``modal.experimental.get_app_objects`` is decorated
    with ``@synchronizer.create_blocking``, and calling its ``.aio`` variant from our own
    event loop deadlocks ("RPC request made outside of task context").

    Returns ``{"functions": [...], "classes": [...]}``.
    """
    response = await client.stub.AppGetLayout(
        api_pb2.AppGetLayoutRequest(app_id=app_id)
    )
    layout = response.app_layout

    metadata_by_id: dict[str, Any] = {}
    for obj in layout.objects:
        if obj.HasField("function_handle_metadata"):
            metadata_by_id[obj.object_id] = obj.function_handle_metadata

    functions = []
    for name, function_id in layout.function_ids.items():
        metadata = metadata_by_id.get(function_id)
        web_url = _optional_str(metadata.web_url) if metadata is not None else None
        functions.append(
            {
                "id": function_id,
                "name": name,
                "app_id": app_id,
                "web_url": web_url,
                # Every non-null web_url is internet-reachable. Whether it is protected by
                # proxy auth is NOT readable from this API (requires_proxy_auth is
                # write-only), so callers must not infer that it is unauthenticated.
                "is_web_endpoint": web_url is not None,
                "function_type": (
                    _enum_name(api_pb2.Function.FunctionType, metadata.function_type)
                    if metadata is not None
                    else None
                ),
                "is_method": metadata.is_method if metadata is not None else None,
                "definition_id": (
                    _optional_str(metadata.definition_id)
                    if metadata is not None
                    else None
                ),
                "input_plane_url": (
                    _optional_str(metadata.input_plane_url)
                    if metadata is not None
                    else None
                ),
                "input_plane_region": (
                    _optional_str(metadata.input_plane_region)
                    if metadata is not None
                    else None
                ),
            }
        )

    classes = [
        {"id": class_id, "name": name, "app_id": app_id}
        for name, class_id in layout.class_ids.items()
    ]
    return {"functions": functions, "classes": classes}


# =============================================================================
# Sandboxes
# =============================================================================


def _sandbox_state(info: Any) -> str:
    """Derive a sandbox state.

    `SandboxInfo` has no state field, so it is inferred from the task result plus
    readiness: a finished sandbox carries a `GenericResult` status, a ready one with no
    result is running, and anything else is still starting.
    """
    if info.HasField("task_info") and info.task_info.HasField("result"):
        status = info.task_info.result.status
        if status:
            return _enum_name(api_pb2.GenericStatus, status) or "UNKNOWN"
    return "RUNNING" if info.ready_at else "PENDING"


def _resource_value(resource_info: Any, field: str) -> int | None:
    """Read a `ResourceInfo.ResourceValue` wrapper.

    ``memory_mb`` and ``milli_cpu`` are ``{value, is_default}`` messages rather than
    scalars, so an unset field must be distinguished from a real zero.
    """
    if not resource_info.HasField(field):
        return None
    return getattr(resource_info, field).value


# Modal distinguishes sandbox generations only by the shape of the id: a v2 id is `sb-` plus a
# 26-character Crockford-base32 ULID whose first character is 0-7. Mirrors
# `modal.sandbox._is_v2_sandbox_id`, which is private, so it is reimplemented here rather than
# imported.
_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _is_v2_sandbox_id(sandbox_id: str) -> bool:
    prefix, separator, suffix = sandbox_id.partition("-")
    return (
        prefix == "sb"
        and separator == "-"
        and len(suffix) == 26
        and suffix[0] in "01234567"
        and all(ch in _ULID_ALPHABET for ch in suffix)
    )


def _sandbox_to_dict(info: Any) -> dict[str, Any]:
    """Convert one `SandboxInfo` to the graph shape.

    Shared by the v1 and v2 listings: both return the same message type.
    """
    resource_info = info.resource_info
    regions = list(info.regions)
    return {
        "id": info.id,
        "name": _optional_str(info.name),
        "app_id": _optional_str(info.app_id),
        "state": _sandbox_state(info),
        # v1 and v2 sandboxes are distinguished only by the shape of their id, so the
        # generation is derived rather than reported. Worth surfacing: the two are listed by
        # different RPCs and support different operations.
        "sandbox_version": "v2" if _is_v2_sandbox_id(info.id) else "v1",
        "created_at": _timestamp(info.created_at),
        "ready_at": _timestamp(info.ready_at),
        "image_id": _optional_str(info.image_id),
        "memory_mb": _resource_value(resource_info, "memory_mb"),
        "memory_mb_max": resource_info.memory_mb_max or None,
        "milli_cpu": _resource_value(resource_info, "milli_cpu"),
        "milli_cpu_max": resource_info.milli_cpu_max or None,
        "gpu_type": _optional_str(resource_info.gpu_type),
        "ephemeral_disk_mb": resource_info.ephemeral_disk_mb or None,
        "regions": regions,
        # A single-region sandbox gets a scalar region so it can join the ontology's region
        # field; a multi-region one deliberately does not.
        "region": regions[0] if len(regions) == 1 else None,
        "timeout_secs": info.timeout_secs or None,
        "idle_timeout_secs": info.idle_timeout_secs or None,
        "tags": [f"{tag.tag_name}={tag.tag_value}" for tag in info.tags],
        "tunnels": [
            {
                "host": _optional_str(tunnel.host),
                "port": tunnel.port or None,
                "unencrypted_host": _optional_str(tunnel.unencrypted_host),
                "unencrypted_port": tunnel.unencrypted_port or None,
                "container_port": tunnel.container_port,
            }
            for tunnel in info.tunnels
        ],
    }


async def list_sandboxes(
    client: ModalClient, environment_name: str
) -> tuple[list[dict[str, Any]], bool]:
    """List running sandboxes in an environment, with their tunnels.

    Returns ``(sandboxes, complete)``. ``complete`` is False if pagination hit
    ``_SANDBOX_PAGE_LIMIT``, in which case the caller must skip cleanup rather than
    delete sandboxes it merely failed to see.

    Uses the private `SandboxList` rather than the public ``Sandbox.list()`` because the
    public generator yields handles whose metadata is only ``{result, app_id}``, dropping
    the image, resources, regions, timeouts and tunnels that we actually want.
    ``include_finished`` is left False: finished sandboxes are ephemeral by nature and
    would otherwise accumulate forever.

    This returns v1 sandboxes only. v2 sandboxes are not included by Modal, and come from
    :func:`list_sandboxes_v2`.
    """
    sandboxes: list[dict[str, Any]] = []
    before_timestamp = 0.0
    complete = False
    for _ in range(_SANDBOX_PAGE_LIMIT):
        request = api_pb2.SandboxListRequest(
            environment_name=environment_name,
            include_finished=False,
        )
        if before_timestamp:
            request.before_timestamp = before_timestamp
        response = await client.stub.SandboxList(request)
        if not response.sandboxes:
            complete = True
            break
        sandboxes.extend(_sandbox_to_dict(info) for info in response.sandboxes)
        oldest = min(info.created_at for info in response.sandboxes)
        if before_timestamp and oldest >= before_timestamp:
            # Timestamps stopped decreasing, so the cursor cannot advance.
            break
        before_timestamp = oldest
    if not complete:
        logger.warning(
            "Modal sandbox enumeration for environment %s stopped after %d pages "
            "without exhausting the list; treating it as incomplete so cleanup is "
            "skipped.",
            environment_name,
            _SANDBOX_PAGE_LIMIT,
        )
    return sandboxes, complete


async def list_sandboxes_v2(
    client: ModalClient, app_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """List the v2 sandboxes of one app, with their tunnels.

    Returns ``(sandboxes, complete)`` with the same contract as :func:`list_sandboxes`.

    Modal's docs are explicit that "V2 sandboxes created with this method are not currently
    returned by ``client.sandboxes.list()``", so `SandboxList` alone silently misses them.
    `SandboxListV2` is the counterpart, and it differs from every other call in this module in
    two ways: ``app_id`` is mandatory, so this fans out per app rather than per environment; and
    it authenticates with an auth-token header rather than the channel credentials, like the
    other v2 sandbox RPCs.

    v2 is still opt-in at the time of writing (created only via
    ``Sandbox._experimental_create``), so most workspaces have none. That is why an empty result
    here is unremarkable rather than a sign something is wrong.
    """
    sandboxes: list[dict[str, Any]] = []
    before_timestamp = 0.0
    complete = False
    for _ in range(_SANDBOX_PAGE_LIMIT):
        request = api_pb2.SandboxListRequest(app_id=app_id, include_finished=False)
        if before_timestamp:
            request.before_timestamp = before_timestamp
        # Fetched per page, like Modal's own `_experimental_list`: a token read once before the
        # loop can expire part-way through a long listing. The manager caches and only renews
        # when needed, so this is not a round trip per page.
        auth_token = await client.raw._auth_token_manager.get_token()
        response = await client.stub.SandboxListV2(
            request, metadata=[("x-modal-auth-token", auth_token)]
        )
        if not response.sandboxes:
            complete = True
            break
        sandboxes.extend(_sandbox_to_dict(info) for info in response.sandboxes)
        oldest = min(info.created_at for info in response.sandboxes)
        if before_timestamp and oldest >= before_timestamp:
            # Timestamps stopped decreasing, so the cursor cannot advance.
            break
        before_timestamp = oldest
    if not complete:
        logger.warning(
            "Modal v2 sandbox enumeration for app %s stopped after %d pages without "
            "exhausting the list; treating it as incomplete so cleanup is skipped.",
            app_id,
            _SANDBOX_PAGE_LIMIT,
        )
    return sandboxes, complete


# =============================================================================
# Named objects
# =============================================================================


async def list_secrets(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List secrets in an environment.

    Uses the private `SecretList` because it is the only source of `last_used_at`, which
    the public `SecretInfo` deliberately omits.

    Modal never returns secret *values* through any read RPC, so no value is available to
    ingest even accidentally.

    Pagination mirrors the public manager in ``modal/secret.py``: pages of 100 walking
    ``created_before`` backwards, stopping on a short page.
    """
    items = await _paginate(
        client,
        client.stub.SecretList,
        api_pb2.SecretListRequest,
        environment_name,
        "items",
    )
    return [
        {
            "id": item.secret_id,
            "name": item.label,
            "created_at": _timestamp(item.created_at),
            "last_used_at": _timestamp(item.last_used_at),
            "created_by": _optional_str(item.metadata.creation_info.created_by),
        }
        for item in items
    ]


async def list_volumes(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List volumes in an environment (private `VolumeList`)."""
    items = await _paginate(
        client,
        client.stub.VolumeList,
        api_pb2.VolumeListRequest,
        environment_name,
        "items",
    )
    return [
        {
            "id": item.volume_id,
            "name": item.label,
            "created_at": _timestamp(item.created_at),
            "created_by": _optional_str(item.metadata.creation_info.created_by),
            "version": _enum_name(api_pb2.VolumeFsVersion, item.metadata.version),
        }
        for item in items
    ]


async def list_nfs(client: ModalClient, environment_name: str) -> list[dict[str, Any]]:
    """List network file systems (private `SharedVolumeList`).

    ``NetworkFileSystem`` has no ``.objects`` manager and its CLI group is hidden, Modal
    having superseded it with Volume. Still enumerated because existing workspaces have
    them.
    """
    response = await client.stub.SharedVolumeList(
        api_pb2.SharedVolumeListRequest(environment_name=environment_name)
    )
    return [
        {
            "id": item.shared_volume_id,
            "name": item.label,
            "created_at": _timestamp(item.created_at),
            "cloud_provider": _enum_name(api_pb2.CloudProvider, item.cloud_provider),
        }
        for item in response.items
    ]


async def list_image_tags(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List named/published image tags (private `ImageListTags`, token-paginated).

    Only *named* images are enumerable; anonymous build images are not. Cleanup is
    therefore safe within the named-image universe only.
    """
    images: list[dict[str, Any]] = []
    page_token = ""
    while True:
        response = await client.stub.ImageListTags(
            api_pb2.ImageListTagsRequest(
                environment_name=environment_name,
                page_token=page_token,
            )
        )
        for item in response.items:
            images.append(
                {
                    "id": item.image_id,
                    "tag": item.tag,
                    "revision_id": _optional_str(item.revision_id),
                    "created_at": _timestamp(item.created_at),
                    "updated_at": _timestamp(item.updated_at),
                }
            )
        page_token = response.next_page_token
        if not page_token:
            break
        await asyncio.sleep(_IMAGE_PAGE_DELAY_SECONDS)
    return images


async def list_dicts(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List dicts in an environment (private `DictList`)."""
    items = await _paginate(
        client,
        client.stub.DictList,
        api_pb2.DictListRequest,
        environment_name,
        "dicts",
    )
    return [
        {
            "id": item.dict_id,
            "name": item.name,
            "created_at": _timestamp(item.created_at),
        }
        for item in items
    ]


async def list_queues(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List queues in an environment (private `QueueList`)."""
    items = await _paginate(
        client,
        client.stub.QueueList,
        api_pb2.QueueListRequest,
        environment_name,
        "queues",
    )
    return [
        {
            "id": item.queue_id,
            "name": item.name,
            "created_at": _timestamp(item.created_at),
            "num_partitions": item.num_partitions or None,
            "total_size": item.total_size or None,
        }
        for item in items
    ]


# =============================================================================
# Tasks, clusters and proxies
# =============================================================================


async def list_tasks(
    client: ModalClient, environment_name: str, app_id: str
) -> list[dict[str, Any]]:
    """List an app's running tasks (private `TaskList`, unpaginated, live only)."""
    response = await client.stub.TaskList(
        api_pb2.TaskListRequest(environment_name=environment_name, app_id=app_id)
    )
    return [
        {
            "id": item.task_id,
            "app_id": _optional_str(item.app_id),
            "app_description": _optional_str(item.app_description),
            "started_at": _timestamp(item.started_at),
            "enqueued_at": _timestamp(item.enqueued_at),
        }
        for item in response.tasks
    ]


async def list_clusters(
    client: ModalClient, environment_name: str
) -> list[dict[str, Any]]:
    """List multi-node clusters in an environment (private `ClusterList`).

    Unlike `TaskList`, this request has no ``app_id`` field, so it is environment-wide and
    is fetched once per environment rather than once per app. Each cluster still carries
    its own ``app_id``.
    """
    response = await client.stub.ClusterList(
        api_pb2.ClusterListRequest(environment_name=environment_name)
    )
    return [
        {
            "id": item.cluster_id,
            "app_id": _optional_str(item.app_id),
            "started_at": _timestamp(item.started_at),
            "task_ids": list(item.task_ids),
        }
        for item in response.clusters
    ]


async def list_proxies(client: ModalClient) -> list[dict[str, Any]]:
    """List proxies with their IPs (private `ProxyList`, workspace-wide).

    ``modal.Proxy`` only offers ``from_name``, so there is no public listing. The response
    is workspace-wide and carries ``environment_name`` per proxy, so callers filter it
    per environment themselves.
    """
    response = await client.stub.ProxyList(Empty())
    return [
        {
            "id": item.proxy_id,
            "name": _optional_str(item.name),
            "created_at": _timestamp(item.created_at),
            "region": _optional_str(item.region),
            "environment_name": _optional_str(item.environment_name),
            "proxy_ips": [
                {
                    "ip_address": ip.proxy_ip,
                    "status": _enum_name(api_pb2.ProxyIpStatus, ip.status),
                    "created_at": _timestamp(ip.created_at),
                }
                for ip in item.proxy_ips
            ],
        }
        for item in response.proxies
    ]
