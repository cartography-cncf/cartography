from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

SEMGREP_SAST_RISK_ANALYSIS = AnalysisJob(
    name="Semgrep SAST findings risk analysis based on severity and repository archive status.",
    short_name="semgrep_sast_risk_analysis",
    scope=ScopeById("SemgrepDeployment", "DEPLOYMENT_ID", scope_on="s"),
    statements=(
        AnalysisStatement(
            match="MATCH (g:GitHubRepository{archived:true})<-[:FOUND_IN]-(s:SemgrepSASTFinding)",
            effects=(
                SetProperty("s", "risk_severity", "INFO", label="SemgrepSASTFinding"),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSASTFinding) WHERE g.archived = false OR g.archived IS NULL",
            effects=(
                SetProperty(
                    "s", "risk_severity", Var("s.severity"), label="SemgrepSASTFinding"
                ),
            ),
            incremental_on="s",
        ),
    ),
)
SEMGREP_SCA_RISK_ANALYSIS = AnalysisJob(
    name="Semgrep SCA findings reachability risk analysis based on likelihood and impact. Impact = Severity, Likelihood = reachability + reachability_check",
    short_name="semgrep_sca_risk_analysis",
    scope=ScopeById("SemgrepDeployment", "DEPLOYMENT_ID", scope_on="s"),
    statements=(
        AnalysisStatement(
            match="MATCH (g:GitHubRepository{archived:true})<-[:FOUND_IN]-(s:SemgrepSCAFinding)",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "INFO", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (s:SemgrepSCAFinding{reachability:'UNREACHABLE'})",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "INFO", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'UNREACHABLE', reachability_check:'NO REACHABILITY ANALYSIS'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity IN ['LOW', 'MEDIUM', 'HIGH']",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "INFO", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'UNREACHABLE', reachability_check:'NO REACHABILITY ANALYSIS'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity = 'CRITICAL'",
            effects=(
                SetProperty("s", "reachability_risk", "LOW", label="SemgrepSCAFinding"),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity IN ['LOW', 'MEDIUM']",
            effects=(
                SetProperty("s", "reachability_risk", "LOW", label="SemgrepSCAFinding"),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity = 'HIGH'",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "MEDIUM", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity = 'CRITICAL'",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "HIGH", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity IN ['LOW','MEDIUM']",
            effects=(
                SetProperty("s", "reachability_risk", "LOW", label="SemgrepSCAFinding"),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity = 'HIGH'",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "MEDIUM", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE'}) WHERE (g.archived = false OR g.archived IS NULL) AND s.severity = 'CRITICAL'",
            effects=(
                SetProperty(
                    "s", "reachability_risk", "CRITICAL", label="SemgrepSCAFinding"
                ),
            ),
            incremental_on="s",
        ),
        AnalysisStatement(
            match="MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'REACHABLE'}) WHERE g.archived = false OR g.archived IS NULL",
            effects=(
                SetProperty(
                    "s",
                    "reachability_risk",
                    Var("s.severity"),
                    label="SemgrepSCAFinding",
                ),
            ),
            incremental_on="s",
        ),
    ),
)
