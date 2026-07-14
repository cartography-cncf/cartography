from dataclasses import dataclass


@dataclass(frozen=True)
class RelConstraint:
    """If a node carrying ontology label `src` has an outward edge toward a
    node carrying ontology label `dst`, that edge MUST be named `label`.

    The constraint never requires the edge to exist; it only constrains the
    name when both endpoints carry the listed ontology labels. Both abstract
    ontology nodes (User, Device, PublicIP, Package) and semantic extra
    labels (Container, ComputePod, ...) are valid src/dst values.
    """

    src: str
    dst: str
    label: str


# Canonical relationship names enforced by test_ontology_rel_constraints.
ONTOLOGY_REL_CONSTRAINTS: tuple[RelConstraint, ...] = (
    # User has one or many UserAccount on different platforms.
    RelConstraint(src="User", dst="UserAccount", label="HAS_ACCOUNT"),
    # Unified workload chain: child workload points at its parent.
    RelConstraint(src="Container", dst="ComputePod", label="WORKLOAD_PARENT"),
    RelConstraint(src="Container", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeNamespace", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputeService", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(
        src="ComputeNamespace", dst="ComputeCluster", label="WORKLOAD_PARENT"
    ),
    # A user account is granted a role.
    RelConstraint(src="UserAccount", dst="PermissionRole", label="HAS_ROLE"),
    # A service account (workload identity) is granted a role. No provider
    # currently wires a direct edge (all go through binding nodes), so this is
    # forward-looking governance for future modules.
    RelConstraint(src="ServiceAccount", dst="PermissionRole", label="HAS_ROLE"),
    # A group is granted a role; members inherit it.
    RelConstraint(src="UserGroup", dst="PermissionRole", label="HAS_ROLE"),
    # A composite/hierarchical role includes other roles.
    RelConstraint(src="PermissionRole", dst="PermissionRole", label="INCLUDES"),
    # A workload consumes a secret (mount method captured as a rel property).
    RelConstraint(src="ComputePod", dst="Secret", label="USES_SECRET"),
    RelConstraint(src="Function", dst="Secret", label="USES_SECRET"),
    RelConstraint(src="ComputeInstance", dst="Secret", label="USES_SECRET"),
    # A secret or data store is encrypted by an encryption key.
    RelConstraint(src="Secret", dst="EncryptionKey", label="ENCRYPTED_BY"),
    RelConstraint(src="Database", dst="EncryptionKey", label="ENCRYPTED_BY"),
    RelConstraint(src="ObjectStorage", dst="EncryptionKey", label="ENCRYPTED_BY"),
    RelConstraint(src="FileStorage", dst="EncryptionKey", label="ENCRYPTED_BY"),
    # An identity is a member of a group; groups nest into other groups.
    RelConstraint(src="UserAccount", dst="UserGroup", label="MEMBER_OF"),
    RelConstraint(src="ServiceAccount", dst="UserGroup", label="MEMBER_OF"),
    RelConstraint(src="UserGroup", dst="UserGroup", label="MEMBER_OF"),
    # An API key / access credential is owned by the identity it authenticates as.
    RelConstraint(src="APIKey", dst="UserAccount", label="OWNED_BY"),
    RelConstraint(src="APIKey", dst="ServiceAccount", label="OWNED_BY"),
    # A workload runs as / assumes the identity of a service account.
    RelConstraint(src="ComputeInstance", dst="ServiceAccount", label="RUNS_AS"),
    RelConstraint(src="ComputePod", dst="ServiceAccount", label="RUNS_AS"),
    RelConstraint(src="Function", dst="ServiceAccount", label="RUNS_AS"),
    RelConstraint(src="ComputeService", dst="ServiceAccount", label="RUNS_AS"),
    # A workload assumes a permission role to obtain its privileges.
    RelConstraint(src="ComputeInstance", dst="PermissionRole", label="ASSUMES"),
    RelConstraint(src="Function", dst="PermissionRole", label="ASSUMES"),
    # A vulnerability finding (CVE) or a rule-based security issue affects a
    # software package. Both finding shapes point at the same canonical Package.
    RelConstraint(src="CVE", dst="Package", label="AFFECTS"),
    RelConstraint(src="SecurityIssue", dst="Package", label="AFFECTS"),
    # A container/function resolves to the concrete single-platform image it
    # runs. Materialized by resolved_image_analysis.json from the raw HAS_IMAGE
    # references (which are whitelisted below as a distinct semantic).
    RelConstraint(src="Container", dst="Image", label="RESOLVED_IMAGE"),
    RelConstraint(src="Function", dst="Image", label="RESOLVED_IMAGE"),
    # An image/function is built from a source code repository (CI provenance).
    RelConstraint(src="Image", dst="CodeRepository", label="PACKAGED_FROM"),
    # NOTE: no UserAccount->CodeRepository constraint. Several distinct edges
    # legitimately span that pair (COMMITTED_TO commit authorship, OWNER
    # ownership, DIRECT_COLLAB_*/OUTSIDE_COLLAB_* access grants), so a single
    # canonical label cannot be enforced here yet.
    # A software package is deployed inside a container image.
    RelConstraint(src="Package", dst="Image", label="DEPLOYED"),
)
