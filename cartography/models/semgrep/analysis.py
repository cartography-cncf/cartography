from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect

SEMGREP_SCOPE = AnalysisScope("SemgrepDeployment", "DEPLOYMENT_ID")

SEMGREP_SAST_RISK_ANALYSIS = AnalysisJob(
    name="Semgrep SAST findings risk analysis based on severity and repository archive status.",
    short_name="semgrep_sast_risk_analysis",
    scope=SEMGREP_SCOPE,
    effect=PropertyEffect("SemgrepSASTFinding", ("risk_severity",)),
    statements=(
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:true})<-[:FOUND_IN]-(s:SemgrepSASTFinding{lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) SET s.risk_severity = 'INFO' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository)<-[:FOUND_IN]-(s:SemgrepSASTFinding{lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE g.archived = false OR g.archived IS NULL SET s.risk_severity = s.severity return COUNT(*) as TotalCompleted",
        ),
    ),
)

SEMGREP_SCA_RISK_ANALYSIS = AnalysisJob(
    name="Semgrep SCA findings reachability risk analysis based on likelihood and impact. Impact = Severity, Likelihood = reachability + reachability_check",
    short_name="semgrep_sca_risk_analysis",
    scope=SEMGREP_SCOPE,
    effect=PropertyEffect("SemgrepSCAFinding", ("reachability_risk",)),
    statements=(
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:true})<-[:FOUND_IN]-(s:SemgrepSCAFinding{lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) SET s.reachability_risk = 'INFO' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (s:SemgrepSCAFinding{reachability:'UNREACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) SET s.reachability_risk = 'INFO' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'UNREACHABLE', reachability_check:'NO REACHABILITY ANALYSIS', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity IN ['LOW', 'MEDIUM', 'HIGH'] SET s.reachability_risk = 'INFO' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'UNREACHABLE', reachability_check:'NO REACHABILITY ANALYSIS', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity = 'CRITICAL' SET s.reachability_risk = 'LOW' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity IN ['LOW', 'MEDIUM'] SET s.reachability_risk = 'LOW' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity = 'HIGH' SET s.reachability_risk = 'MEDIUM' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'CONDITIONALLY REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity = 'CRITICAL' SET s.reachability_risk = 'HIGH' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity IN ['LOW','MEDIUM'] SET s.reachability_risk = 'LOW' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity = 'HIGH' SET s.reachability_risk = 'MEDIUM' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'ALWAYS REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) WHERE s.severity = 'CRITICAL' SET s.reachability_risk = 'CRITICAL' return COUNT(*) as TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (g:GitHubRepository{archived:false})<-[:FOUND_IN]-(s:SemgrepSCAFinding{reachability:'REACHABLE', reachability_check:'REACHABLE', lastupdated:$UPDATE_TAG})<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) SET s.reachability_risk = s.severity return COUNT(*) as TotalCompleted",
        ),
    ),
)
