import json
import re
from typing import Any
from typing import Dict
from typing import List


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

    def __init__(self, raw_acl: str) -> None:
        # Tailscale ACL use comments and trailing commas
        # that are not valid JSON
        filtered_json_string = self.RE_SINGLE_LINE_COMMENT.sub(r"\1", raw_acl)
        filtered_json_string = self.RE_MULTI_LINE_COMMENT.sub(
            r"\1", filtered_json_string
        )
        filtered_json_string = self.RE_TRAILING_COMMA.sub("", filtered_json_string)
        self.data = json.loads(filtered_json_string)

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Get all groups from the ACL

        :return: list of groups
        """
        result: List[Dict[str, Any]] = []
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

    def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags from the ACL

        :return: list of tags
        """
        result: List[Dict[str, Any]] = []
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
