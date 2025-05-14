import json
import re
from typing import Any
from typing import Dict
from typing import List


class ACLParser:
    # DOC
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
                if member.startswith("group:"):
                    sub_groups.append(member)
                elif member.startswith("*@"):
                    domain_members.append(member[2:])
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
