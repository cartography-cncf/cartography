"""Sovereign-cloud endpoint definitions for Microsoft Graph.

Supports the commercial cloud plus the GCC High / DoD US Government and
China national clouds. Each cloud exposes a distinct Graph endpoint and
AAD authority host — see
https://learn.microsoft.com/en-us/graph/deployments for the authoritative
list.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MicrosoftCloud:
    name: str
    graph_base_url: str
    graph_scope: str
    authority: str


COMMERCIAL = MicrosoftCloud(
    name="commercial",
    graph_base_url="https://graph.microsoft.com/v1.0/",
    graph_scope="https://graph.microsoft.com/.default",
    authority="https://login.microsoftonline.com",
)

USGOV = MicrosoftCloud(
    name="usgov",
    graph_base_url="https://graph.microsoft.us/v1.0/",
    graph_scope="https://graph.microsoft.us/.default",
    authority="https://login.microsoftonline.us",
)

USGOV_DOD = MicrosoftCloud(
    name="usgov-dod",
    graph_base_url="https://dod-graph.microsoft.us/v1.0/",
    graph_scope="https://dod-graph.microsoft.us/.default",
    authority="https://login.microsoftonline.us",
)

CHINA = MicrosoftCloud(
    name="china",
    graph_base_url="https://microsoftgraph.chinacloudapi.cn/v1.0/",
    graph_scope="https://microsoftgraph.chinacloudapi.cn/.default",
    authority="https://login.chinacloudapi.cn",
)

CLOUDS: dict[str, MicrosoftCloud] = {
    c.name: c for c in (COMMERCIAL, USGOV, USGOV_DOD, CHINA)
}

DEFAULT_CLOUD_NAME = COMMERCIAL.name


def get_cloud(name: str | None) -> MicrosoftCloud:
    """Resolve a cloud name to its :class:`MicrosoftCloud` definition.

    :raises ValueError: if the name is not a known cloud.
    """
    key = (name or DEFAULT_CLOUD_NAME).lower()
    try:
        return CLOUDS[key]
    except KeyError:
        valid = ", ".join(sorted(CLOUDS))
        raise ValueError(f"Unknown Microsoft cloud {name!r}. Valid values: {valid}.")
