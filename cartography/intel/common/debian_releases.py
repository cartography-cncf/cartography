"""
Debian release codenames and their major versions.

The security tracker keys its data by release codename, while a Debian system reports
its release in /etc/debian_version: a point release such as `12.7` on stable, or
`<codename>/sid` on testing and unstable. Both map to the major version here, so data
keyed either way can be joined on it.
"""

# From etch (4) on: earlier releases used two-part version numbers and are not in the
# tracker's data or in container images. sid never gets a version.
RELEASE_VERSIONS: dict[str, str] = {
    "etch": "4",
    "lenny": "5",
    "squeeze": "6",
    "wheezy": "7",
    "jessie": "8",
    "stretch": "9",
    "buster": "10",
    "bullseye": "11",
    "bookworm": "12",
    "trixie": "13",
    "forky": "14",
    "duke": "15",
}


def release_version(codename: str) -> str | None:
    return RELEASE_VERSIONS.get(codename)


def major_release(debian_version: str | None) -> str | None:
    """
    `12.7` gives `12` and `trixie/sid` gives `13`. Testing and unstable both report
    the codename of the release in preparation, so `<codename>/sid` maps to that
    release rather than to sid.
    """
    if not debian_version:
        return None
    name = debian_version.strip().lower()
    major = name.split(".", 1)[0]
    if major.isdigit():
        return major
    return RELEASE_VERSIONS.get(name.split("/", 1)[0])
