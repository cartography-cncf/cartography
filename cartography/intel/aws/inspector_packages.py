"""Package URLs for the vulnerable packages that AWS Inspector reports."""

from typing import Any
from typing import Dict

from packageurl import PackageURL

# Inspector names an operating system by platform, such as AMAZON_LINUX_2023 or
# DEBIAN_12. The namespaces are the ones Trivy uses, so the same package from both
# scanners reaches the same PackageVersion.
_OS_PACKAGE_TYPES = (
    ("AMAZON_LINUX", "rpm", "amazon"),
    ("RHEL", "rpm", "redhat"),
    ("CENTOS", "rpm", "centos"),
    ("ORACLE", "rpm", "oracle"),
    ("ROCKY", "rpm", "rocky"),
    ("ALMA", "rpm", "alma"),
    ("FEDORA", "rpm", "fedora"),
    ("OPENSUSE", "rpm", "opensuse"),
    ("SLES", "rpm", "suse"),
    ("SUSE", "rpm", "suse"),
    ("DEBIAN", "deb", "debian"),
    ("UBUNTU", "deb", "ubuntu"),
    ("ALPINE", "apk", "alpine"),
)

# Debian names architectures differently from rpm and apk, and its package URLs use
# the Debian names.
_DEB_ARCHITECTURES = {"x86_64": "amd64", "aarch64": "arm64"}

# Findings name language package managers both by ecosystem (NODE, PYTHON, JAVA, GO,
# C_SHARP) and by tool (NPM, PIP, JAR, GOBINARY).
_LANGUAGE_PACKAGE_TYPES = {
    "NODE": "npm",
    "PYTHON": "pypi",
    "JAVA": "maven",
    "GO": "golang",
    "C_SHARP": "nuget",
    "PIP": "pypi",
    "PIPENV": "pypi",
    "POETRY": "pypi",
    "PYTHONPKG": "pypi",
    "NPM": "npm",
    "YARN": "npm",
    "PNPM": "npm",
    "NODEPKG": "npm",
    "JAR": "maven",
    "GRADLE": "maven",
    "POM": "maven",
    "GOBINARY": "golang",
    "GOMOD": "golang",
    "NUGET": "nuget",
    "DOTNET_CORE": "nuget",
    "GEMSPEC": "gem",
    "BUNDLER": "gem",
    "CARGO": "cargo",
    "COMPOSER": "composer",
}


def resource_platform(finding: Dict[str, Any]) -> str | None:
    details = finding["resources"][0].get("details") or {}
    for resource_type in ("awsEc2Instance", "awsEcrContainerImage"):
        platform = (details.get(resource_type) or {}).get("platform")
        if platform:
            return platform
    return None


def os_distribution(platform: str | None) -> tuple[str, str] | None:
    """Return the package URL type and namespace of an operating system platform."""
    return next(
        (
            (purl_type, namespace)
            for prefix, purl_type, namespace in _OS_PACKAGE_TYPES
            if (platform or "").startswith(prefix)
        ),
        None,
    )


def _split_namespace(purl_type: str, name: str) -> tuple[str | None, str]:
    if purl_type == "maven" and ":" in name:
        group, artifact = name.split(":", 1)
        return group, artifact
    if purl_type == "npm" and name.startswith("@") and "/" in name:
        scope, package = name.split("/", 1)
        return scope, package
    if purl_type in ("golang", "composer") and "/" in name:
        namespace, package = name.rsplit("/", 1)
        return namespace, package
    return None, name


def package_url(package: Dict[str, Any], platform: str | None) -> str | None:
    """Return the package URL of an Inspector vulnerable package, or None when unknown.

    Operating system packages need the resource's platform to name their distribution.
    """
    manager = package.get("packageManager")
    version = package["version"]
    qualifiers: Dict[str, str] = {}
    purl_type: str | None
    namespace: str | None
    if manager == "OS":
        distribution = os_distribution(platform)
        if distribution is None:
            return None
        purl_type, namespace = distribution
        name = package["name"]
        if package.get("release"):
            version = f"{version}-{package['release']}"
        if package.get("arch"):
            arch = str(package["arch"]).lower()
            if purl_type == "deb":
                arch = _DEB_ARCHITECTURES.get(arch, arch)
            qualifiers["arch"] = arch
        if package.get("epoch"):
            qualifiers["epoch"] = str(package["epoch"])
    else:
        purl_type = _LANGUAGE_PACKAGE_TYPES.get(manager or "")
        if purl_type is None:
            return None
        namespace, name = _split_namespace(purl_type, package["name"])
        # A Maven artifact is named only together with its group.
        if purl_type == "maven" and not namespace:
            return None
    if not name or not version:
        return None
    return PackageURL(
        type=purl_type,
        namespace=namespace or None,
        name=name,
        version=version,
        qualifiers=qualifiers or None,
    ).to_string()
