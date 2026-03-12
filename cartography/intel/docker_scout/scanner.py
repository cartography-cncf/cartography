import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.trivy.util import make_normalized_package_id
from cartography.models.docker_scout.finding import DockerScoutFindingSchema
from cartography.models.docker_scout.fix import DockerScoutFixSchema
from cartography.models.docker_scout.image import DockerScoutPublicImageSchema
from cartography.models.docker_scout.package import DockerScoutPackageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform_public_image(
    sbom_data: dict[str, Any],
    image_digest: str,
) -> dict[str, Any] | None:
    """
    Extract the public image info from the scanned image's SBOM annotations.
    Returns a single dict for the DockerScoutPublicImage node, or None if no public image found.
    """
    annotations = (
        sbom_data.get("source", {})
        .get("image", {})
        .get("manifest", {})
        .get("annotations", {})
    )
    base_name_full = annotations.get("org.opencontainers.image.base.name")
    if not base_name_full or base_name_full == "scratch":
        logger.info("No public image found (image is built FROM scratch)")
        return None

    # Parse public image reference into name and tag components
    if ":" in base_name_full:
        name, tag = base_name_full.rsplit(":", 1)
    else:
        name = base_name_full
        tag = "latest"

    base_digest = annotations.get("org.opencontainers.image.base.digest")
    version = annotations.get("org.opencontainers.image.version")

    return {
        "id": base_name_full,
        "name": name,
        "tag": tag,
        "version": version,
        "digest": base_digest,
        "ImageDigest": image_digest,
    }


def transform_packages(
    sbom_data: dict[str, Any],
    image_digest: str,
    public_image_id: str,
) -> list[dict[str, Any]]:
    """
    Transform SBOM artifacts into DockerScoutPackage dicts.
    Works with both full SBOM data (with locations) and CVE artifact data (without locations).
    """
    artifacts = sbom_data.get("artifacts", [])
    packages = []

    for artifact in artifacts:
        purl = artifact.get("purl")
        name = artifact.get("name", "")
        version = artifact.get("version", "")
        pkg_type = artifact.get("type", "")

        # Build package ID using "{version}|{name}" format for consistency with Trivy
        pkg_id = f"{version}|{name}"

        # Get layer info from the first location
        locations = artifact.get("locations", [])
        layer_digest = None
        layer_diff_id = None
        if locations:
            layer_digest = locations[0].get("digest")
            layer_diff_id = locations[0].get("diff_id")

        normalized_id = make_normalized_package_id(
            purl=purl,
            name=name,
            version=version,
            pkg_type=pkg_type,
        )

        packages.append(
            {
                "id": pkg_id,
                "name": name,
                "version": version,
                "namespace": artifact.get("namespace"),
                "type": pkg_type,
                "purl": purl,
                "normalized_id": normalized_id,
                "layer_digest": layer_digest,
                "layer_diff_id": layer_diff_id,
                "ImageDigest": image_digest,
                "BaseImageId": public_image_id,
            }
        )

    logger.info("Transformed %d packages", len(packages))
    return packages


def transform_findings(
    cves_data: dict[str, Any],
    image_digest: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Transform CVE data into DockerScoutFinding and DockerScoutFix dicts.
    """
    vuln_packages = cves_data.get("vulnerabilities", [])
    findings = []
    fixes = []

    # Build a purl -> package_id lookup from the SBOM artifacts embedded in the CVE output
    purl_to_pkg_id = {}
    for artifact in cves_data.get("artifacts", []):
        purl = artifact.get("purl")
        if purl:
            name = artifact.get("name", "")
            version = artifact.get("version", "")
            purl_to_pkg_id[purl] = f"{version}|{name}"

    for vuln_pkg in vuln_packages:
        pkg_purl = vuln_pkg.get("purl", "")
        package_id = purl_to_pkg_id.get(pkg_purl)

        for vuln in vuln_pkg.get("vulnerabilities", []):
            source_id = vuln["source_id"]
            finding_id = f"DSF|{source_id}"

            # Extract severity and CVSS version from nested cvss object
            cvss = vuln.get("cvss", {})
            severity = cvss.get("severity")
            cvss_version = cvss.get("version")

            # Extract EPSS (Exploit Prediction Scoring System) from nested epss object
            epss = vuln.get("epss", {})
            epss_score = epss.get("score")
            epss_percentile = epss.get("percentile")

            # Extract CWE IDs from nested cwes array (only present when fix exists)
            cwes = vuln.get("cwes", [])
            cwe_ids = [c.get("cwe_id") for c in cwes if c.get("cwe_id")]

            findings.append(
                {
                    "id": finding_id,
                    "source_id": source_id,
                    "source": vuln.get("source"),
                    "description": vuln.get("description"),
                    "url": vuln.get("url"),
                    "published_at": vuln.get("published_at"),
                    "updated_at": vuln.get("updated_at"),
                    "severity": severity,
                    "cvss_version": cvss_version,
                    "vulnerable_range": vuln.get("vulnerable_range"),
                    "cwe_ids": cwe_ids or None,
                    "epss_score": epss_score,
                    "epss_percentile": epss_percentile,
                    "ImageDigest": image_digest,
                    "PackageId": package_id,
                }
            )

            # Only create a fix entry when a patched version is available
            fixed_by = vuln.get("fixed_by")
            if fixed_by and package_id:
                fix_id = f"{fixed_by}|{package_id}"
                fixes.append(
                    {
                        "id": fix_id,
                        "fixed_by": fixed_by,
                        "PackageId": package_id,
                        "FindingId": finding_id,
                    }
                )

    logger.info(
        "Transformed %d findings and %d fixes from CVE data",
        len(findings),
        len(fixes),
    )
    return findings, fixes


@timeit
def load_public_image(
    neo4j_session: neo4j.Session,
    public_image_data: dict[str, Any],
    update_tag: int,
) -> None:
    """Load a single DockerScoutPublicImage node into Neo4j."""
    load(
        neo4j_session,
        DockerScoutPublicImageSchema(),
        [public_image_data],
        lastupdated=update_tag,
    )


@timeit
def load_packages(
    neo4j_session: neo4j.Session,
    packages_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """Load DockerScoutPackage nodes into Neo4j."""
    load(
        neo4j_session,
        DockerScoutPackageSchema(),
        packages_list,
        lastupdated=update_tag,
    )


@timeit
def load_findings(
    neo4j_session: neo4j.Session,
    findings_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """Load DockerScoutFinding nodes into Neo4j."""
    load(
        neo4j_session,
        DockerScoutFindingSchema(),
        findings_list,
        lastupdated=update_tag,
    )


@timeit
def load_fixes(
    neo4j_session: neo4j.Session,
    fixes_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """Load DockerScoutFix nodes into Neo4j."""
    load(
        neo4j_session,
        DockerScoutFixSchema(),
        fixes_list,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """Run cleanup jobs to remove stale Docker Scout nodes. Uses global cleanup to emulate Trivy module."""
    logger.info("Running Docker Scout cleanup")
    GraphJob.from_node_schema(
        DockerScoutPublicImageSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(DockerScoutPackageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(DockerScoutFindingSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(DockerScoutFixSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_from_file(
    neo4j_session: neo4j.Session,
    scout_data: dict[str, Any],
    source: str,
    update_tag: int,
) -> bool:
    """
    Sync Docker Scout data from a pre-generated JSON file.

    Expects a combined JSON dict with keys:
        - "sbom": output of `docker scout sbom --format json <image>`
        - "cves": output of `docker scout cves --only-base --format sbom <image>`

    Returns True if data was successfully loaded, False if the file was skipped.
    """
    sbom_data = scout_data.get("sbom")
    cves_data = scout_data.get("cves")
    if not sbom_data or not cves_data:
        logger.warning(
            "Skipping %s: expected JSON with 'sbom' and 'cves' keys",
            source,
        )
        return False

    image_digest = sbom_data.get("source", {}).get("image", {}).get("digest")
    if not image_digest:
        logger.warning("Skipping %s: no image digest found in sbom data", source)
        return False

    # Extract base image info from SBOM annotations
    public_image = transform_public_image(sbom_data, image_digest)
    if public_image is None:
        logger.info(
            "Skipping %s: no public image detected (built FROM scratch)",
            source,
        )
        return False

    public_image_id = public_image["id"]

    # Merge packages from SBOM (all packages, has location data) and CVE artifacts (vulnerable only),
    # deduplicating by package ID and preferring SBOM entries since they have richer context.
    sbom_packages = transform_packages(sbom_data, image_digest, public_image_id)
    cve_packages = transform_packages(cves_data, image_digest, public_image_id)
    packages_by_id: dict[str, dict[str, Any]] = {}
    for pkg in cve_packages:
        packages_by_id[pkg["id"]] = pkg
    for pkg in sbom_packages:
        packages_by_id[pkg["id"]] = pkg
    packages = list(packages_by_id.values())
    findings, fixes = transform_findings(cves_data, image_digest)

    load_public_image(neo4j_session, public_image, update_tag)
    load_packages(neo4j_session, packages, update_tag)
    load_findings(neo4j_session, findings, update_tag)
    load_fixes(neo4j_session, fixes, update_tag)

    logger.info(
        "Completed Docker Scout sync for %s: "
        "public_image=%s, %d packages, %d findings, %d fixes",
        source,
        public_image_id,
        len(packages),
        len(findings),
        len(fixes),
    )
    return True
