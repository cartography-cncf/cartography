"""Helpers for reading Snowflake object references back out of API payloads.

Several schema-level objects point at other objects by *name* rather than by id:
a task lists its predecessors as fully-qualified names, a function lists the
secrets it may read, a Cortex Search service names its source table. Those
strings have to be turned back into the exact node id the referenced object was
loaded under, which means round-tripping them through
:func:`cartography.intel.snowflake.util.sf_fqn` rather than string-concatenating
them.
"""

import logging
from typing import Any

from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id

logger = logging.getLogger(__name__)


def split_qualified_name(qualified_name: str) -> list[str]:
    """Split a dotted Snowflake identifier into its logical components.

    Double quotes delimit a case-sensitive component, with ``""`` standing for a
    literal quote, and a dot inside quotes is part of the name rather than a
    separator. An unquoted component is folded to uppercase, which is what
    Snowflake itself does, so that the component can be fed back through
    ``sf_fqn`` and produce the same text the referenced object's own id used.
    """
    parts: list[str] = []
    current: list[str] = []
    was_quoted = False
    in_quotes = False
    index = 0
    while index < len(qualified_name):
        char = qualified_name[index]
        if in_quotes:
            if char == '"':
                if qualified_name[index + 1 : index + 2] == '"':
                    current.append('"')
                    index += 2
                    continue
                in_quotes = False
            else:
                current.append(char)
        elif char == '"':
            in_quotes = True
            was_quoted = True
        elif char == ".":
            parts.append("".join(current) if was_quoted else "".join(current).upper())
            current = []
            was_quoted = False
        else:
            current.append(char)
        index += 1
    parts.append("".join(current) if was_quoted else "".join(current).upper())
    return parts


def schema_object_fqn(
    database_name: str,
    schema_name: str,
    reference: str | None,
) -> str | None:
    """Resolve a reference to a schema-level object into a qualified name.

    Snowflake accepts a one-, two- or three-part reference depending on how the
    referring object was defined, so the missing leading components are filled in
    from the schema the referring object lives in. Returns None when the
    reference is not a plain object name (a Cortex Search service can be defined
    over a query rather than a table, for instance), so the caller suppresses the
    edge instead of pointing it at a node that does not exist.
    """
    if not reference:
        return None
    parts = split_qualified_name(reference)
    if len(parts) == 1:
        parts = [database_name, schema_name, parts[0]]
    elif len(parts) == 2:
        parts = [database_name, *parts]
    elif len(parts) != 3:
        return None
    if not all(parts):
        return None
    return sf_fqn(*parts)


def share_key(provider_account: str | None, share_name: str) -> str:
    """Build the qualified-name half of a share's node id.

    A share name is only unique within the account that owns it. ``SHOW SHARES``
    reports the bare name plus a separate ``owner_account``, so two providers can
    both expose a share called ``SAMPLE_DATA`` to this account; keying on the name
    alone would merge them onto one node.

    The provider account is reduced to its last component because the two sources
    that name a share qualify it differently: ``owner_account`` may be
    organization-qualified (``SNOW.MY_TEST_ACCOUNT``) while a database's ``origin``
    carries only the account token. Taking the account token from each is what makes
    a share's own id and the id recomputed from ``origin`` agree.

    Falls back to the bare name when the provider is unknown, which keeps a share
    addressable rather than dropping it.
    """
    account_token = (
        split_qualified_name(provider_account)[-1] if provider_account else ""
    )
    if not account_token:
        return sf_fqn(share_name)
    return sf_fqn(account_token, share_name)


def share_key_from_origin(origin: str | None) -> str | None:
    """Recompute a share's key from a database's ``origin`` reference.

    ``origin`` is ``<provider_account>.<share_name>``, where the provider account
    may itself be dotted, so the share name is taken as the final component and the
    provider as the one before it. Returns None when ``origin`` is absent or has no
    share component, so the caller suppresses the edge instead of pointing it at a
    node that does not exist.
    """
    if not origin:
        return None
    parts = split_qualified_name(origin)
    if not parts or not parts[-1]:
        return None
    provider = parts[-2] if len(parts) >= 2 else None
    return share_key(provider, parts[-1])


def name_list(value: Any) -> list[str]:
    """Normalise a Snowflake list-of-names field into a list of plain strings.

    Fields such as ``external_access_integrations`` come back as a JSON array on
    the object API but as a rendered ``[A, B]`` string on the SQL API, so both are
    reduced to the same list here.
    """
    if isinstance(value, list):
        return [str(item).strip() for item in value if item]
    if isinstance(value, str) and value.strip():
        return [
            part.strip()
            for part in value.strip().strip("[]()").split(",")
            if part.strip()
        ]
    return []


def secret_references(secrets: Any) -> list[str]:
    """Return the object references named in a routine's SECRETS clause.

    Snowflake binds each secret to a variable name the handler reads it by, so the
    payload is a mapping of variable name to secret reference and only the values
    identify actual secret objects.
    """
    if isinstance(secrets, dict):
        return [str(value).strip() for value in secrets.values() if value]
    references: list[str] = []
    for item in secrets if isinstance(secrets, list) else name_list(secrets):
        if isinstance(item, dict):
            value = item.get("secret_name") or item.get("secret") or item.get("value")
        else:
            value = item
        if not value:
            continue
        # A rendered clause keeps the variable name: "cred = db.schema.my_secret".
        references.append(str(value).partition("=")[2].strip() or str(value).strip())
    return references


def external_access_integration_ids(
    external_access_integrations: Any,
    account_id: str,
) -> list[str]:
    """Resolve external access integration names to their node ids.

    External access integrations are account-level objects, so the name Snowflake
    reports is already the whole identifier.
    """
    return [
        sf_id(account_id, "external_access_integration", name)
        for name in name_list(external_access_integrations)
    ]


def secret_ids(
    secrets: Any,
    database_name: str,
    schema_name: str,
    account_id: str,
) -> list[str]:
    """Resolve the secret references in a SECRETS clause to secret node ids.

    A reference may be written relative to the referring object's own schema, so
    the missing leading components are filled in before the id is built.
    """
    ids: list[str] = []
    for reference in secret_references(secrets):
        qualified_name = schema_object_fqn(database_name, schema_name, reference)
        if not qualified_name:
            logger.warning(
                "Skipping Snowflake secret reference %s: not an object name.",
                reference,
            )
            continue
        ids.append(sf_id(account_id, "secret", qualified_name))
    return ids


def _split_top_level(text: str) -> list[str]:
    """Split on commas that are not nested inside parentheses.

    ``NUMBER(38,0)`` carries a comma of its own, so a plain ``str.split(",")``
    would tear one argument type in half.
    """
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def normalize_signature(signature: Any) -> str:
    """Render a routine's argument list as a deterministic ``(TYPE,TYPE)`` string.

    A Snowflake function or procedure name is unique only together with its
    argument types, because the same name can be overloaded several times in one
    schema. Snowflake describes those arguments in more than one shape depending
    on the endpoint (a list of ``{name, datatype}`` objects, or a rendered
    ``(A VARCHAR, B NUMBER)`` string), so both are reduced here to the same
    comma-separated list of uppercase type names with no whitespace.
    """
    datatypes: list[str] = []
    if isinstance(signature, list):
        for argument in signature:
            if isinstance(argument, dict):
                datatype = argument.get("datatype") or argument.get("type")
            else:
                datatype = argument
            if datatype:
                datatypes.append(str(datatype))
    elif signature:
        text = str(signature).strip()
        if text.startswith("(") and text.endswith(")"):
            text = text[1:-1]
        for argument in _split_top_level(text):
            tokens = argument.split()
            if tokens:
                # A rendered signature names each argument before its type, while
                # a bare type list does not, so the type is always the last token.
                datatypes.append(tokens[-1])
    return "(" + ",".join(datatype.strip().upper() for datatype in datatypes) + ")"


def routine_qualified_name(
    database_name: str,
    schema_name: str,
    name: str,
    signature: Any,
) -> str:
    """Return the overload-aware qualified name of a function or procedure."""
    return sf_fqn(database_name, schema_name, name) + normalize_signature(signature)
