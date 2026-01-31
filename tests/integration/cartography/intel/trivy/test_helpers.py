from neo4j import Session

from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def assert_trivy_findings(neo4j_session: Session) -> None:
    """Assert TrivyImageFinding nodes exist with expected values."""
    assert check_nodes(
        neo4j_session, "TrivyImageFinding", ["id", "name", "severity"]
    ) == {
        ("TIF|CVE-2023-29383", "CVE-2023-29383", "LOW"),
        ("TIF|CVE-2023-4039", "CVE-2023-4039", "LOW"),
        ("TIF|CVE-2023-4641", "CVE-2023-4641", "MEDIUM"),
        ("TIF|CVE-2024-12133", "CVE-2024-12133", "MEDIUM"),
        ("TIF|CVE-2024-13176", "CVE-2024-13176", "MEDIUM"),
        ("TIF|CVE-2024-26462", "CVE-2024-26462", "MEDIUM"),
        ("TIF|CVE-2024-56406", "CVE-2024-56406", "HIGH"),
        ("TIF|CVE-2025-24528", "CVE-2025-24528", "MEDIUM"),
        ("TIF|CVE-2025-31115", "CVE-2025-31115", "HIGH"),
        ("TIF|CVE-2025-43859", "CVE-2025-43859", "CRITICAL"),
    }


def assert_trivy_packages(neo4j_session: Session) -> None:
    """Assert Package nodes exist with expected values."""
    assert check_nodes(neo4j_session, "Package", ["id", "name", "version"]) == {
        ("0.14.0|h11", "h11", "0.14.0"),
        ("1.20.1-2+deb12u2|krb5-locales", "krb5-locales", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libk5crypto3", "libk5crypto3", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libkrb5-3", "libkrb5-3", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libkrb5support0", "libkrb5support0", "1.20.1-2+deb12u2"),
        ("12.2.0-14|gcc-12-base", "gcc-12-base", "12.2.0-14"),
        ("12.2.0-14|libstdc++6", "libstdc++6", "12.2.0-14"),
        ("1:4.13+dfsg1-1+b1|login", "login", "1:4.13+dfsg1-1+b1"),
        ("1:4.13+dfsg1-1+b1|passwd", "passwd", "1:4.13+dfsg1-1+b1"),
        ("3.0.15-1~deb12u1|libssl3", "libssl3", "3.0.15-1~deb12u1"),
        ("3.0.15-1~deb12u1|openssl", "openssl", "3.0.15-1~deb12u1"),
        ("4.19.0-2|libtasn1-6", "libtasn1-6", "4.19.0-2"),
        ("5.36.0-7+deb12u1|perl-base", "perl-base", "5.36.0-7+deb12u1"),
        ("5.4.1-0.2|liblzma5", "liblzma5", "5.4.1-0.2"),
    }


def assert_all_trivy_relationships(neo4j_session: Session) -> None:
    """Assert all Trivy relationships are correctly created."""
    # Package to ECRImage relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        (
            "0.14.0|h11",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|krb5-locales",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libk5crypto3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libkrb5-3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libkrb5support0",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "12.2.0-14|gcc-12-base",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "12.2.0-14|libstdc++6",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1:4.13+dfsg1-1+b1|login",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1:4.13+dfsg1-1+b1|passwd",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "3.0.15-1~deb12u1|libssl3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "3.0.15-1~deb12u1|openssl",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "4.19.0-2|libtasn1-6",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "5.36.0-7+deb12u1|perl-base",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "5.4.1-0.2|liblzma5",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    # Package to TrivyFix relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyFix",
        "id",
        "SHOULD_UPDATE_TO",
        rel_direction_right=True,
    ) == {
        ("0.14.0|h11", "0.16.0|h11"),
        ("1.20.1-2+deb12u2|krb5-locales", "1.20.1-2+deb12u3|krb5-locales"),
        ("1.20.1-2+deb12u2|libk5crypto3", "1.20.1-2+deb12u3|libk5crypto3"),
        ("1.20.1-2+deb12u2|libkrb5-3", "1.20.1-2+deb12u3|libkrb5-3"),
        ("1.20.1-2+deb12u2|libkrb5support0", "1.20.1-2+deb12u3|libkrb5support0"),
        ("12.2.0-14|gcc-12-base", "12.2.0-14+deb12u1|gcc-12-base"),
        ("12.2.0-14|libstdc++6", "12.2.0-14+deb12u1|libstdc++6"),
        ("1:4.13+dfsg1-1+b1|login", "1:4.13+dfsg1-1+deb12u1|login"),
        ("1:4.13+dfsg1-1+b1|passwd", "1:4.13+dfsg1-1+deb12u1|passwd"),
        ("3.0.15-1~deb12u1|libssl3", "3.0.16-1~deb12u1|libssl3"),
        ("3.0.15-1~deb12u1|openssl", "3.0.16-1~deb12u1|openssl"),
        ("4.19.0-2|libtasn1-6", "4.19.0-2+deb12u1|libtasn1-6"),
        ("5.36.0-7+deb12u1|perl-base", "5.36.0-7+deb12u2|perl-base"),
        ("5.4.1-0.2|liblzma5", "5.4.1-1|liblzma5"),
    }

    # TrivyFix to TrivyImageFinding relationships
    assert check_rels(
        neo4j_session,
        "TrivyFix",
        "id",
        "TrivyImageFinding",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        ("0.16.0|h11", "TIF|CVE-2025-43859"),
        ("1.20.1-2+deb12u3|krb5-locales", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|krb5-locales", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libk5crypto3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libk5crypto3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libkrb5-3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libkrb5-3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libkrb5support0", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libkrb5support0", "TIF|CVE-2025-24528"),
        ("12.2.0-14+deb12u1|gcc-12-base", "TIF|CVE-2023-4039"),
        ("12.2.0-14+deb12u1|libstdc++6", "TIF|CVE-2023-4039"),
        ("1:4.13+dfsg1-1+deb12u1|login", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+deb12u1|login", "TIF|CVE-2023-4641"),
        ("1:4.13+dfsg1-1+deb12u1|passwd", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+deb12u1|passwd", "TIF|CVE-2023-4641"),
        ("3.0.16-1~deb12u1|libssl3", "TIF|CVE-2024-13176"),
        ("3.0.16-1~deb12u1|openssl", "TIF|CVE-2024-13176"),
        ("4.19.0-2+deb12u1|libtasn1-6", "TIF|CVE-2024-12133"),
        ("5.36.0-7+deb12u2|perl-base", "TIF|CVE-2024-56406"),
        ("5.4.1-1|liblzma5", "TIF|CVE-2025-31115"),
    }

    # Package to TrivyImageFinding relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyImageFinding",
        "id",
        "AFFECTS",
        rel_direction_right=False,
    ) == {
        ("0.14.0|h11", "TIF|CVE-2025-43859"),
        ("1.20.1-2+deb12u2|krb5-locales", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|krb5-locales", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libk5crypto3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libk5crypto3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libkrb5-3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libkrb5-3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libkrb5support0", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libkrb5support0", "TIF|CVE-2025-24528"),
        ("12.2.0-14|gcc-12-base", "TIF|CVE-2023-4039"),
        ("12.2.0-14|libstdc++6", "TIF|CVE-2023-4039"),
        ("1:4.13+dfsg1-1+b1|login", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+b1|login", "TIF|CVE-2023-4641"),
        ("1:4.13+dfsg1-1+b1|passwd", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+b1|passwd", "TIF|CVE-2023-4641"),
        ("3.0.15-1~deb12u1|libssl3", "TIF|CVE-2024-13176"),
        ("3.0.15-1~deb12u1|openssl", "TIF|CVE-2024-13176"),
        ("4.19.0-2|libtasn1-6", "TIF|CVE-2024-12133"),
        ("5.36.0-7+deb12u1|perl-base", "TIF|CVE-2024-56406"),
        ("5.4.1-0.2|liblzma5", "TIF|CVE-2025-31115"),
    }

    # TrivyImageFinding to ECRImage relationships
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "ECRImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (
            "TIF|CVE-2023-29383",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2023-4039",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2023-4641",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-12133",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-13176",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-26462",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-56406",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-24528",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-31115",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-43859",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }


def assert_trivy_finding_extended_fields(neo4j_session: Session) -> None:
    """Assert TrivyImageFinding nodes have extended fields populated."""
    result = neo4j_session.run(
        """
        MATCH (f:TrivyImageFinding)
        WHERE f.cwe_ids IS NOT NULL
        RETURN f.id AS id, f.cwe_ids AS cwe_ids, f.status AS status,
               f.data_source_id AS data_source_id, f.data_source_name AS data_source_name,
               f.layer_digest AS layer_digest, f.references AS refs
        LIMIT 5
        """
    ).data()
    # Verify at least one finding has the extended fields
    assert len(result) > 0, "Expected at least one finding with extended fields"
    for row in result:
        assert row["cwe_ids"] is not None, f"cwe_ids should be set for {row['id']}"
        assert row["status"] is not None, f"status should be set for {row['id']}"
        assert (
            row["data_source_id"] is not None
        ), f"data_source_id should be set for {row['id']}"
        assert (
            row["data_source_name"] is not None
        ), f"data_source_name should be set for {row['id']}"


def assert_trivy_package_extended_fields(neo4j_session: Session) -> None:
    """Assert Package nodes have extended fields populated."""
    result = neo4j_session.run(
        """
        MATCH (p:Package)
        WHERE p.purl IS NOT NULL
        RETURN p.id AS id, p.purl AS purl, p.pkg_id AS pkg_id
        LIMIT 5
        """
    ).data()
    # Verify at least one package has the extended fields
    assert len(result) > 0, "Expected at least one package with extended fields"
    for row in result:
        assert row["purl"] is not None, f"purl should be set for {row['id']}"
        assert row["pkg_id"] is not None, f"pkg_id should be set for {row['id']}"


def assert_trivy_gcp_image_relationships(
    neo4j_session: Session,
    expected_package_rels: set,
    expected_finding_rels: set,
) -> None:
    """
    Assert Trivy relationships to GCP image nodes are correctly created.
    Checks both ContainerImage and PlatformImage nodes, combining results.
    """
    # Package to GCPArtifactRegistryContainerImage relationships (DEPLOYED)
    container_image_package_rels = check_rels(
        neo4j_session,
        "Package",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    # Package to GCPArtifactRegistryPlatformImage relationships (DEPLOYED)
    platform_image_package_rels = check_rels(
        neo4j_session,
        "Package",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "digest",
        "DEPLOYED",
        rel_direction_right=True,
    )

    # Combine both sets of relationships
    actual_package_rels = container_image_package_rels | platform_image_package_rels
    assert actual_package_rels == expected_package_rels

    # TrivyImageFinding to GCPArtifactRegistryContainerImage relationships (AFFECTS)
    container_image_finding_rels = check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "AFFECTS",
        rel_direction_right=True,
    )

    # TrivyImageFinding to GCPArtifactRegistryPlatformImage relationships (AFFECTS)
    platform_image_finding_rels = check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "GCPArtifactRegistryPlatformImage",
        "digest",
        "AFFECTS",
        rel_direction_right=True,
    )

    # Combine both sets of relationships
    actual_finding_rels = container_image_finding_rels | platform_image_finding_rels
    assert actual_finding_rels == expected_finding_rels


def assert_trivy_gitlab_image_relationships(
    neo4j_session: Session,
    expected_package_rels: set,
    expected_finding_rels: set,
) -> None:
    """Assert Trivy relationships to GitLabContainerImage are correctly created."""
    # Package to GitLabContainerImage relationships (DEPLOYED)
    assert (
        check_rels(
            neo4j_session,
            "Package",
            "id",
            "GitLabContainerImage",
            "id",
            "DEPLOYED",
            rel_direction_right=True,
        )
        == expected_package_rels
    )

    # TrivyImageFinding to GitLabContainerImage relationships (AFFECTS)
    assert (
        check_rels(
            neo4j_session,
            "TrivyImageFinding",
            "id",
            "GitLabContainerImage",
            "id",
            "AFFECTS",
            rel_direction_right=True,
        )
        == expected_finding_rels
    )
