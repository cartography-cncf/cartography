"""
Custom Data Pipeline privilege escalation analysis with AND logic.

This module implements custom AND logic for Data Pipeline privilege escalation,
ensuring that ALL required permissions are present before creating CAN_EXEC relationships.
This prevents false positives that would occur with the default OR logic.
"""

import logging
from typing import Dict, List, Set

import neo4j

from cartography.util import timeit

logger = logging.getLogger(__name__)

# Required permissions for Data Pipeline privilege escalation
REQUIRED_PERMISSIONS = [
    "iam:PassRole",
    "datapipeline:CreatePipeline",
    "datapipeline:PutPipelineDefinition",
    "datapipeline:ActivatePipeline"
]


@timeit
def create_datapipeline_can_exec_relationships(neo4j_session: neo4j.Session) -> None:
    """
    Create CAN_EXEC relationships for Data Pipeline using AND logic.
    
    Only creates CAN_EXEC relationships when the principal has ALL required permissions.
    This prevents false positives from OR logic.
    
    Args:
        neo4j_session: Neo4j session for database operations
    """
    logger.info("Starting Data Pipeline privilege escalation analysis with AND logic")
    
    # Find principals with ALL required permissions using AND logic
    query = """
    MATCH (principal:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
    AND ANY(action IN stmt.action WHERE action IN $required_perms)
    WITH principal, COLLECT(DISTINCT stmt.action) as flat_actions
    WITH principal, REDUCE(actions = [], action IN flat_actions | 
        CASE WHEN action IN actions THEN actions ELSE actions + action END) as user_permissions
    WHERE ALL(perm IN $required_perms WHERE perm IN user_permissions)
    RETURN principal.arn, principal.name, user_permissions
    """
    
    result = neo4j_session.run(query, required_perms=REQUIRED_PERMISSIONS)
    principals_with_all_perms = list(result)
    
    logger.info(f"Found {len(principals_with_all_perms)} principals with ALL required permissions")
    
    # Create CAN_EXEC relationships for qualified principals
    for record in principals_with_all_perms:
        principal_arn = record["principal.arn"]
        principal_name = record["principal.name"]
        user_permissions = record["user_permissions"]
        
        logger.info(f"Creating CAN_EXEC relationships for principal with {len(user_permissions)} required permissions")
        
        # Create CAN_EXEC relationships to ALL DataPipeline nodes
        create_query = """
        MATCH (principal:AWSPrincipal {arn: $arn})
        MATCH (pipeline:DataPipeline)
        MERGE (principal)-[:CAN_EXEC]->(pipeline)
        SET pipeline.lastupdated = timestamp()
        """
        
        neo4j_session.run(create_query, arn=principal_arn)
        logger.info(f"Created CAN_EXEC relationships for principal to all DataPipelines")
    
    logger.info("Data Pipeline privilege escalation analysis completed")


@timeit
def get_datapipeline_privilege_escalation_summary(neo4j_session: neo4j.Session) -> Dict:
    """
    Get summary of Data Pipeline privilege escalation analysis.
    
    Args:
        neo4j_session: Neo4j session for database operations
        
    Returns:
        Dict containing analysis summary
    """
    # Count principals with CAN_EXEC relationships
    result = neo4j_session.run("""
    MATCH (principal:AWSPrincipal)-[:CAN_EXEC]->(pipeline:DataPipeline)
    RETURN count(DISTINCT principal) as high_risk_principals,
           count(pipeline) as total_can_exec_relationships
    """)
    
    summary_record = result.single()
    
    # Count principals with some but not all permissions (false positives prevented)
    result = neo4j_session.run("""
    MATCH (principal:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
    AND ANY(action IN stmt.action WHERE action IN $required_perms)
    WITH principal, COLLECT(DISTINCT stmt.action) as flat_actions
    WITH principal, REDUCE(actions = [], action IN flat_actions | 
        CASE WHEN action IN actions THEN actions ELSE actions + action END) as user_permissions
    WHERE NOT ALL(perm IN $required_perms WHERE perm IN user_permissions)
    OPTIONAL MATCH (principal)-[:CAN_EXEC]->(pipeline:DataPipeline)
    RETURN count(DISTINCT principal) as false_positives_prevented
    """, required_perms=REQUIRED_PERMISSIONS)
    
    false_positives_record = result.single()
    
    return {
        "high_risk_principals": summary_record["high_risk_principals"] if summary_record else 0,
        "total_can_exec_relationships": summary_record["total_can_exec_relationships"] if summary_record else 0,
        "false_positives_prevented": false_positives_record["false_positives_prevented"] if false_positives_record else 0,
        "required_permissions": REQUIRED_PERMISSIONS,
        "logic_type": "AND_LOGIC"
    }


@timeit
def cleanup_datapipeline_can_exec_relationships(neo4j_session: neo4j.Session, update_tag: int) -> None:
    """
    Clean up stale CAN_EXEC relationships for Data Pipeline.
    
    Args:
        neo4j_session: Neo4j session for database operations
        update_tag: Update tag for cleanup
    """
    logger.info("Cleaning up stale Data Pipeline CAN_EXEC relationships")
    
    query = """
    MATCH (principal:AWSPrincipal)-[r:CAN_EXEC]->(pipeline:DataPipeline)
    WHERE pipeline.lastupdated < $update_tag
    DELETE r
    """
    
    neo4j_session.run(query, update_tag=update_tag)
    logger.info("Data Pipeline CAN_EXEC relationship cleanup completed")


@timeit
def validate_datapipeline_and_logic(neo4j_session: neo4j.Session) -> List[Dict]:
    """
    Validate that AND logic is working correctly by checking principals with partial permissions.
    
    Args:
        neo4j_session: Neo4j session for database operations
        
    Returns:
        List of validation results
    """
    validation_results = []
    
    # Check principals with partial permissions (should NOT have CAN_EXEC)
    query = """
    MATCH (principal:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
    AND ANY(action IN stmt.action WHERE action IN $required_perms)
    WITH principal, COLLECT(DISTINCT stmt.action) as flat_actions
    WITH principal, REDUCE(actions = [], action IN flat_actions | 
        CASE WHEN action IN actions THEN actions ELSE actions + action END) as user_permissions
    WHERE NOT ALL(perm IN $required_perms WHERE perm IN user_permissions)
    OPTIONAL MATCH (principal)-[:CAN_EXEC]->(pipeline:DataPipeline)
    RETURN principal.name, user_permissions, count(pipeline) as can_exec_count
    """
    
    result = neo4j_session.run(query, required_perms=REQUIRED_PERMISSIONS)
    
    for record in result:
        validation_results.append({
            "principal_name": record["principal.name"],
            "user_permissions": record["user_permissions"],
            "can_exec_count": record["can_exec_count"],
            "validation": "PASS" if record["can_exec_count"] == 0 else "FAIL"
        })
    
    logger.info(f"AND Logic validation completed for {len(validation_results)} principals")
    return validation_results
