import json
import re
from ast import literal_eval
from typing import Any


class ACLParser:
    """ACLParser is a class that parses Tailscale ACLs to extract data.

    It removes comments and trailing commas from the ACL string
    and converts it to a JSON object. It then provides methods
    to extract groups and tags from the ACL.
    The ACL string is expected to be in a format similar to JSON,
    but with some Tailscale-specific syntax. The parser handles
    single-line comments (//) and multi-line comments (/* */)
    and removes trailing commas from the JSON-like structure.
    The parser also handles Tailscale-specific syntax for groups
    and tags, which may include user and group identifiers.
    The parser is initialized with a raw ACL string, which is
    processed to remove comments and trailing commas.

    Args:
        raw_acl (str): The raw ACL string to be parsed.

    Attributes:
        data (dict): The parsed JSON object representing the ACL.
    """

    RE_SINGLE_LINE_COMMENT = re.compile(r'("(?:(?=(\\?))\2.)*?")|(?:\/{2,}.*)')
    RE_MULTI_LINE_COMMENT = re.compile(
        r'("(?:(?=(\\?))\2.)*?")|(?:\/\*(?:(?!\*\/).)+\*\/)', flags=re.M | re.DOTALL
    )
    RE_TRAILING_COMMA = re.compile(r",(?=\s*?[\}\]])")
    RE_NOT_IN = re.compile(
        r"^(?P<attribute>[A-Za-z0-9:_-]+)\s+NOT\s+IN\s+(?P<value>\[.*\])$",
        flags=re.IGNORECASE,
    )
    RE_IN = re.compile(
        r"^(?P<attribute>[A-Za-z0-9:_-]+)\s+IN\s+(?P<value>\[.*\])$",
        flags=re.IGNORECASE,
    )
    RE_IS_SET = re.compile(
        r"^(?P<attribute>[A-Za-z0-9:_-]+)\s+IS\s+SET$",
        flags=re.IGNORECASE,
    )
    RE_NOT_SET = re.compile(
        r"^(?P<attribute>[A-Za-z0-9:_-]+)\s+NOT\s+SET$",
        flags=re.IGNORECASE,
    )
    RE_BINARY = re.compile(
        r"^(?P<attribute>[A-Za-z0-9:_-]+)\s*(?P<operator>==|!=|>=|<=|>|<)\s*(?P<value>.+)$",
    )

    def __init__(self, raw_acl: str) -> None:
        # Tailscale ACL use comments and trailing commas
        # that are not valid JSON
        filtered_json_string = self.RE_SINGLE_LINE_COMMENT.sub(r"\1", raw_acl)
        filtered_json_string = self.RE_MULTI_LINE_COMMENT.sub(
            r"\1", filtered_json_string
        )
        filtered_json_string = self.RE_TRAILING_COMMA.sub("", filtered_json_string)
        self.data = json.loads(filtered_json_string)

    def get_groups(self) -> list[dict[str, Any]]:
        """
        Get all groups from the ACL

        :return: list of groups
        """
        result: list[dict[str, Any]] = []
        groups = self.data.get("groups", {})
        for group_id, members in groups.items():
            group_name = group_id.split(":")[-1]
            users_members = []
            sub_groups = []
            domain_members = []
            for member in members:
                if member.startswith("group:") or member.startswith("autogroup:"):
                    sub_groups.append(member)
                elif member.startswith("user:*@"):
                    domain_members.append(member[7:])
                elif member.startswith("user:"):
                    users_members.append(member[5:])
                else:
                    users_members.append(member)
            result.append(
                {
                    "id": group_id,
                    "name": group_name,
                    "members": users_members,
                    "sub_groups": sub_groups,
                    "domain_members": domain_members,
                }
            )
        return result

    def get_tags(self) -> list[dict[str, Any]]:
        """
        Get all tags from the ACL

        :return: list of tags
        """
        result: list[dict[str, Any]] = []
        for tag, owners in self.data.get("tagOwners", {}).items():
            tag_name = tag.split(":")[-1]
            user_owners = []
            group_owners = []
            domain_owners = []
            for owner in owners:
                if owner.startswith("group:") or owner.startswith("autogroup:"):
                    group_owners.append(owner)
                elif owner.startswith("user:*@"):
                    domain_owners.append(owner[7:])
                elif owner.startswith("user:"):
                    user_owners.append(owner[5:])
                else:
                    user_owners.append(owner)
            result.append(
                {
                    "id": tag,
                    "name": tag_name,
                    "owners": user_owners,
                    "group_owners": group_owners,
                    "domain_owners": domain_owners,
                }
            )
        return result

    def get_grants(self) -> list[dict[str, Any]]:
        """
        Get all grants from the ACL/policy file.

        Tailscale grants define access rules with sources, destinations,
        and capabilities (network and/or application layer).

        Each grant is assigned a stable ID based on a hash of its content
        (src + dst + ip + app + srcPosture), so reordering grants in the
        policy file does not change their identity.

        :return: list of grants with parsed source/destination selectors
        """
        import hashlib

        result: list[dict[str, Any]] = []
        grants = self.data.get("grants", [])
        for grant in grants:
            sources = grant.get("src", [])
            destinations = grant.get("dst", [])

            # Classify sources
            source_users: list[str] = []
            source_groups: list[str] = []
            source_tags: list[str] = []
            source_any = False
            for src in sources:
                if src.startswith("group:") or src.startswith("autogroup:"):
                    source_groups.append(src)
                elif src.startswith("tag:"):
                    source_tags.append(src)
                elif src == "*":
                    source_any = True
                else:
                    # Treat as user email
                    source_users.append(src)

            # Classify destinations
            destination_tags: list[str] = []
            destination_groups: list[str] = []
            destination_services: list[str] = []
            destination_hosts: list[str] = []
            for dst in destinations:
                if dst.startswith("tag:"):
                    destination_tags.append(dst)
                elif dst.startswith("group:") or dst.startswith("autogroup:"):
                    destination_groups.append(dst)
                elif dst.startswith("svc:"):
                    destination_services.append(dst)
                else:
                    destination_hosts.append(dst)

            # Parse capabilities
            ip_rules = grant.get("ip", [])
            app_capabilities = grant.get("app", {})
            src_posture = grant.get("srcPosture", [])

            # Compute stable ID from grant content
            hash_input = json.dumps(
                {
                    "src": sorted(sources),
                    "dst": sorted(destinations),
                    "ip": sorted(ip_rules),
                    "app": app_capabilities,
                    "srcPosture": sorted(src_posture),
                },
                sort_keys=True,
            )
            grant_id = (
                "grant:"
                + hashlib.sha256(
                    hash_input.encode(),
                ).hexdigest()[:12]
            )

            result.append(
                {
                    "id": grant_id,
                    "sources": sources,
                    "destinations": destinations,
                    "source_users": source_users,
                    "source_groups": source_groups,
                    "source_tags": source_tags,
                    "source_any": source_any,
                    "destination_tags": destination_tags,
                    "destination_groups": destination_groups,
                    "destination_services": destination_services,
                    "destination_hosts": destination_hosts,
                    "ip_rules": ip_rules,
                    "app_capabilities": app_capabilities,
                    "src_posture": src_posture,
                },
            )
        return result

    def get_postures(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Get logical postures and their atomic conditions from the ACL.

        Returns:
            A tuple ``(postures, conditions)`` where:
            - ``postures`` contains one item per posture block
            - ``conditions`` contains one item per posture assertion
        """
        postures: list[dict[str, Any]] = []
        conditions: list[dict[str, Any]] = []

        for posture_id, raw_conditions in self.data.get("postures", {}).items():
            condition_ids: list[str] = []
            descriptions: list[str] = []

            for index, raw_condition in enumerate(raw_conditions):
                parsed = self._parse_posture_condition(raw_condition)
                if not parsed:
                    continue

                condition_id = f"{posture_id}:{index}"
                condition_ids.append(condition_id)
                descriptions.append(raw_condition)
                conditions.append(
                    {
                        "id": condition_id,
                        "posture_id": posture_id,
                        "name": parsed["attribute"],
                        "provider": parsed["provider"],
                        "operator": parsed["operator"],
                        "value": parsed["value"],
                    },
                )

            postures.append(
                {
                    "id": posture_id,
                    "name": posture_id.split(":", 1)[-1],
                    "description": "; ".join(descriptions),
                    "condition_ids": condition_ids,
                },
            )

        return postures, conditions

    @classmethod
    def _parse_posture_condition(
        cls,
        raw_condition: str,
    ) -> dict[str, Any] | None:
        condition = raw_condition.strip()

        not_in_match = cls.RE_NOT_IN.match(condition)
        if not_in_match:
            attribute = not_in_match.group("attribute")
            return {
                "attribute": attribute,
                "provider": derive_provider(attribute),
                "operator": "NOT IN",
                "value": _stringify_condition_value(
                    _parse_condition_value(not_in_match.group("value")),
                ),
            }

        in_match = cls.RE_IN.match(condition)
        if in_match:
            attribute = in_match.group("attribute")
            return {
                "attribute": attribute,
                "provider": derive_provider(attribute),
                "operator": "IN",
                "value": _stringify_condition_value(
                    _parse_condition_value(in_match.group("value")),
                ),
            }

        is_set_match = cls.RE_IS_SET.match(condition)
        if is_set_match:
            attribute = is_set_match.group("attribute")
            return {
                "attribute": attribute,
                "provider": derive_provider(attribute),
                "operator": "IS SET",
                "value": None,
            }

        not_set_match = cls.RE_NOT_SET.match(condition)
        if not_set_match:
            attribute = not_set_match.group("attribute")
            return {
                "attribute": attribute,
                "provider": derive_provider(attribute),
                "operator": "NOT SET",
                "value": None,
            }

        binary_match = cls.RE_BINARY.match(condition)
        if binary_match:
            attribute = binary_match.group("attribute")
            return {
                "attribute": attribute,
                "provider": derive_provider(attribute),
                "operator": binary_match.group("operator"),
                "value": _stringify_condition_value(
                    _parse_condition_value(binary_match.group("value")),
                ),
            }

        # Tailscale posture booleans are sometimes expressed as a bare attribute.
        if condition:
            return {
                "attribute": condition,
                "provider": derive_provider(condition),
                "operator": "==",
                "value": "true",
            }

        return None


def role_to_group(role: str) -> list[str]:
    """Convert Tailscale role to group

    This function is used to convert Tailscale role to autogroup
    group. The autogroup is used to manage the access control
    in Tailscale.

    Args:
        role (str): The role of the user in Tailscale. (eg: owner, admin, member, etc)

    Returns:
        list[str]: The list of autogroup that the user belongs to. (eg: autogroup:admin, autogroup:member, etc)
    """
    result: list[str] = []
    result.append(f"autogroup:{role}")
    if role == "owner":
        result.append("autogroup:admin")
        result.append("autogroup:member")
    elif role in ("admin", "auditor", "billing-admin", "it-admin", "network-admin"):
        result.append("autogroup:member")
    return result


def derive_provider(attribute: str) -> str:
    provider_aliases = {
        "sentinelone": "sentinelone",
        "falcon": "falcon",
        "kolide": "kolide",
        "fleet": "fleet",
        "huntress": "huntress",
        "kandji": "kandji",
        "jamfpro": "jamfpro",
        "intune": "intune",
        "node": "node",
        "ip": "ip",
    }
    if ":" in attribute:
        provider = attribute.split(":", 1)[0].lower()
        return provider_aliases.get(provider, provider)
    if "_" in attribute:
        provider = attribute.split("_", 1)[0].lower()
        return provider_aliases.get(provider, provider)
    return "custom"


def _parse_condition_value(raw_value: str) -> Any:
    value = raw_value.strip()

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null":
        return None

    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip("'\"")


def _stringify_condition_value(value: Any) -> str | None:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return str(value)
