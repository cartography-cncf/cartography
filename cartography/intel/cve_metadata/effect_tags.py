"""Derive `effect_tags` on CVEMetadata: a small, queryable, controlled vocabulary
describing *what a vulnerability lets an attacker do*, anchored in MITRE CWE/ATT&CK.

Two-stage derivation with strict precedence (a node draws from exactly one source):
  1. CWE mapping (preferred) via the in-repo CWE_EFFECT_TAGS table.
  2. CVSS fallback from the decomposed CVSS metrics, only if stage 1 is empty.
  3. Neither -> [] / "none".

See docs/root/modules/cve_metadata/schema.md for the vocabulary + anchoring table.
"""

# Controlled vocabulary. effect_tags values MUST come from this set.
EXECUTE_CODE = "execute-code"
GAIN_PRIVILEGES = "gain-privileges"
ACCESS_CREDENTIALS = "access-credentials"
BYPASS_CONTROL = "bypass-control"
DISCLOSE_DATA = "disclose-data"
TAMPER_DATA = "tamper-data"
DENY_SERVICE = "deny-service"

# Static CWE -> effect_tags bootstrap table, hand-curated from MITRE CWE Common
# Consequences. Covers the CWEs actually observed in current data plus common
# neighbours. Grows over time via PR. Uninformative CWEs (NVD-CWE-noinfo,
# NVD-CWE-Other, generic pillars like CWE-707/CWE-20) are simply absent here and
# so contribute nothing, letting derivation fall through to the CVSS stage.
CWE_EFFECT_TAGS: dict[str, list[str]] = {
    # --- Code / command injection: execution by construction ---
    "CWE-77": [EXECUTE_CODE],  # Command Injection
    "CWE-78": [EXECUTE_CODE],  # OS Command Injection
    "CWE-88": [EXECUTE_CODE],  # Argument Injection
    "CWE-94": [EXECUTE_CODE],  # Code Injection
    "CWE-95": [EXECUTE_CODE],  # Eval Injection
    "CWE-98": [EXECUTE_CODE],  # PHP Remote File Inclusion
    "CWE-434": [EXECUTE_CODE],  # Unrestricted Upload of Dangerous File
    "CWE-502": [EXECUTE_CODE],  # Deserialization of Untrusted Data
    "CWE-917": [EXECUTE_CODE],  # Expression Language Injection
    "CWE-1321": [EXECUTE_CODE],  # Prototype Pollution
    # --- DLL / search-path hijack -> execution ---
    "CWE-426": [EXECUTE_CODE],  # Untrusted Search Path
    "CWE-427": [EXECUTE_CODE],  # Uncontrolled Search Path Element
    # --- Memory corruption: conditional code execution + crash + memory tamper ---
    "CWE-119": [EXECUTE_CODE, TAMPER_DATA, DENY_SERVICE],  # Improper mem bounds
    "CWE-120": [EXECUTE_CODE, DENY_SERVICE],  # Classic Buffer Overflow
    "CWE-121": [EXECUTE_CODE, DENY_SERVICE],  # Stack-based Buffer Overflow
    "CWE-122": [EXECUTE_CODE, DENY_SERVICE],  # Heap-based Buffer Overflow
    "CWE-125": [DISCLOSE_DATA, DENY_SERVICE],  # Out-of-bounds Read
    "CWE-787": [EXECUTE_CODE, TAMPER_DATA, DENY_SERVICE],  # Out-of-bounds Write
    "CWE-416": [EXECUTE_CODE, DENY_SERVICE],  # Use After Free
    "CWE-415": [EXECUTE_CODE, DENY_SERVICE],  # Double Free
    "CWE-476": [DENY_SERVICE],  # NULL Pointer Dereference
    "CWE-190": [EXECUTE_CODE, DENY_SERVICE],  # Integer Overflow
    "CWE-191": [EXECUTE_CODE, DENY_SERVICE],  # Integer Underflow
    "CWE-193": [EXECUTE_CODE, DENY_SERVICE],  # Off-by-one Error
    "CWE-824": [EXECUTE_CODE, DENY_SERVICE],  # Access of Uninitialized Pointer
    # --- Resource exhaustion -> denial of service ---
    "CWE-400": [DENY_SERVICE],  # Uncontrolled Resource Consumption
    "CWE-401": [DENY_SERVICE],  # Missing Release of Memory
    "CWE-404": [DENY_SERVICE],  # Improper Resource Shutdown
    "CWE-674": [DENY_SERVICE],  # Uncontrolled Recursion
    "CWE-770": [DENY_SERVICE],  # Allocation of Resources Without Limits
    "CWE-772": [DENY_SERVICE],  # Missing Release of Resource
    "CWE-834": [DENY_SERVICE],  # Excessive Iteration
    "CWE-835": [DENY_SERVICE],  # Loop with Unreachable Exit (infinite loop)
    # --- Path traversal: read + write files ---
    "CWE-22": [DISCLOSE_DATA, TAMPER_DATA],  # Path Traversal
    "CWE-23": [DISCLOSE_DATA, TAMPER_DATA],  # Relative Path Traversal
    "CWE-36": [DISCLOSE_DATA, TAMPER_DATA],  # Absolute Path Traversal
    "CWE-59": [DISCLOSE_DATA, TAMPER_DATA],  # Link Following
    # --- Information disclosure ---
    "CWE-79": [EXECUTE_CODE, DISCLOSE_DATA],  # Cross-site Scripting
    "CWE-89": [DISCLOSE_DATA, TAMPER_DATA],  # SQL Injection
    "CWE-200": [DISCLOSE_DATA],  # Exposure of Sensitive Information
    "CWE-201": [DISCLOSE_DATA],  # Insertion of Sensitive Info Into Sent Data
    "CWE-209": [DISCLOSE_DATA],  # Error Message Info Exposure
    "CWE-312": [DISCLOSE_DATA],  # Cleartext Storage of Sensitive Information
    "CWE-319": [DISCLOSE_DATA],  # Cleartext Transmission of Sensitive Info
    "CWE-532": [DISCLOSE_DATA],  # Insertion of Sensitive Info into Log File
    "CWE-611": [DISCLOSE_DATA],  # XML External Entity (XXE)
    "CWE-918": [DISCLOSE_DATA],  # Server-Side Request Forgery (SSRF)
    # --- Credential access ---
    "CWE-256": [ACCESS_CREDENTIALS],  # Unprotected Storage of Credentials
    "CWE-257": [ACCESS_CREDENTIALS],  # Storing Passwords in Recoverable Format
    "CWE-259": [ACCESS_CREDENTIALS],  # Use of Hard-coded Password
    "CWE-522": [ACCESS_CREDENTIALS],  # Insufficiently Protected Credentials
    "CWE-798": [ACCESS_CREDENTIALS],  # Use of Hard-coded Credentials
    # --- Privilege escalation ---
    "CWE-250": [GAIN_PRIVILEGES],  # Execution with Unnecessary Privileges
    "CWE-266": [GAIN_PRIVILEGES],  # Incorrect Privilege Assignment
    "CWE-267": [GAIN_PRIVILEGES],  # Privilege Defined With Unsafe Actions
    "CWE-268": [GAIN_PRIVILEGES],  # Privilege Chaining
    "CWE-269": [GAIN_PRIVILEGES],  # Improper Privilege Management
    "CWE-276": [GAIN_PRIVILEGES],  # Incorrect Default Permissions
    "CWE-732": [GAIN_PRIVILEGES],  # Incorrect Permission Assignment
    # --- Access control / authentication bypass ---
    "CWE-284": [BYPASS_CONTROL],  # Improper Access Control
    "CWE-285": [BYPASS_CONTROL],  # Improper Authorization
    "CWE-287": [BYPASS_CONTROL],  # Improper Authentication
    "CWE-290": [BYPASS_CONTROL],  # Authentication Bypass by Spoofing
    "CWE-295": [BYPASS_CONTROL],  # Improper Certificate Validation
    "CWE-306": [BYPASS_CONTROL],  # Missing Authentication for Critical Function
    "CWE-347": [BYPASS_CONTROL],  # Improper Verification of Crypto Signature
    "CWE-352": [TAMPER_DATA],  # Cross-Site Request Forgery
    "CWE-354": [BYPASS_CONTROL, TAMPER_DATA],  # Improper Integrity Check Validation
    "CWE-425": [BYPASS_CONTROL],  # Direct Request (Forced Browsing)
    "CWE-639": [BYPASS_CONTROL],  # Authorization Bypass Through User-Controlled Key
    "CWE-862": [BYPASS_CONTROL],  # Missing Authorization
    "CWE-863": [BYPASS_CONTROL],  # Incorrect Authorization
}


# CWEs that intentionally contribute no effect (no-info markers / generic root-cause
# pillars). Excluded from the "unmapped CWE" warning so it only surfaces genuinely
# missing table entries worth curating, not expected noise.
UNINFORMATIVE_CWES = {
    "NVD-CWE-noinfo",
    "NVD-CWE-Other",
    "CWE-707",
    "CWE-20",
}


def unmapped_cwes(weaknesses: list[str]) -> list[str]:
    """CWEs absent from the mapping table and not known-uninformative: candidates
    to add to CWE_EFFECT_TAGS."""
    return [
        cwe
        for cwe in weaknesses
        if cwe not in CWE_EFFECT_TAGS and cwe not in UNINFORMATIVE_CWES
    ]


def _derive_from_cwe(weaknesses: list[str]) -> list[str]:
    """Union of mapped effects across all CWEs, deduplicated, vocabulary-ordered."""
    tags: set[str] = set()
    for cwe in weaknesses:
        tags.update(CWE_EFFECT_TAGS.get(cwe, []))
    return _ordered(tags)


# Highest impact level per CVSS version: v3/v4 use HIGH, v2 uses COMPLETE.
_HIGH_IMPACT = {"HIGH", "COMPLETE"}


def _derive_from_cvss(cve: dict) -> list[str]:
    """CVSS fallback from decomposed metrics. Degrades gracefully across versions:
    the C/I/A impact mapping applies to all (v2 COMPLETE counts as high, same as
    v3/v4 HIGH); the 'straight-shot' execute-code rule only fires where the required
    exploitability metrics exist (skipped on v2, which lacks privileges_required /
    user_interaction)."""
    tags: set[str] = set()
    integ = cve.get("integrityImpact")
    if cve.get("confidentialityImpact") in _HIGH_IMPACT:
        tags.add(DISCLOSE_DATA)
    if integ in _HIGH_IMPACT:
        tags.add(TAMPER_DATA)
    if cve.get("availabilityImpact") in _HIGH_IMPACT:
        tags.add(DENY_SERVICE)
    if (
        cve.get("attackVector") == "NETWORK"
        and cve.get("privilegesRequired") == "NONE"
        and cve.get("userInteraction") == "NONE"
        and integ in _HIGH_IMPACT
    ):
        tags.add(EXECUTE_CODE)
    return _ordered(tags)


# Stable vocabulary order so output lists are deterministic and reviewable.
_VOCAB_ORDER = [
    EXECUTE_CODE,
    GAIN_PRIVILEGES,
    ACCESS_CREDENTIALS,
    BYPASS_CONTROL,
    DISCLOSE_DATA,
    TAMPER_DATA,
    DENY_SERVICE,
]


def _ordered(tags: set[str]) -> list[str]:
    return [t for t in _VOCAB_ORDER if t in tags]


def derive_effect_tags(cve: dict) -> tuple[list[str], str]:
    """Derive (effect_tags, effect_tags_source) for a transformed CVE dict.

    Precedence: CWE (source="cwe") > CVSS (source="cvss") > none (source="none").
    A node draws from exactly one source.
    """
    cwe_tags = _derive_from_cwe(cve.get("weaknesses", []))
    if cwe_tags:
        return cwe_tags, "cwe"
    cvss_tags = _derive_from_cvss(cve)
    if cvss_tags:
        return cvss_tags, "cvss"
    return [], "none"
