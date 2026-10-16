# Semgrep Analysis

## SAST Risk Severity

Semgrep Cloud SAST findings receive a `risk_severity` property from post-ingestion analysis. Findings in archived GitHub repositories are assigned `INFO`; otherwise, the value follows the finding severity.

## SCA Reachability Risk

Semgrep SCA findings receive a `reachability_risk` property based on severity, reachability, and the reachability check. Findings in archived repositories or findings confirmed as unreachable are assigned `INFO`.

Other combinations use the risk levels defined by `SEMGREP_SCA_RISK_ANALYSIS`, based on the likelihood and impact approach from NIST SP 800-30 Revision 1 and Semgrep reachability exposure guidance.
