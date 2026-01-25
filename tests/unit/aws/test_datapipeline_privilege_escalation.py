"""
Tests for Data Pipeline privilege escalation module with AND logic.
"""

import pytest
from unittest.mock import Mock
import neo4j
from cartography.intel.aws.datapipeline_privilege_escalation import (
    create_datapipeline_can_exec_relationships,
    get_datapipeline_privilege_escalation_summary,
    cleanup_datapipeline_can_exec_relationships,
    validate_datapipeline_and_logic,
    REQUIRED_PERMISSIONS
)


class TestDataPipelinePrivilegeEscalation:
    """Test Data Pipeline privilege escalation with AND logic"""

    @pytest.fixture
    def neo4j_session(self):
        """Mock Neo4j session"""
        session = Mock(spec=neo4j.Session)
        return session

    def test_required_permissions_constant(self):
        """Test that required permissions are correctly defined"""
        expected_permissions = [
            "iam:PassRole",
            "datapipeline:CreatePipeline",
            "datapipeline:PutPipelineDefinition",
            "datapipeline:ActivatePipeline"
        ]
        assert REQUIRED_PERMISSIONS == expected_permissions
        assert len(REQUIRED_PERMISSIONS) == 4

    def test_create_datapipeline_can_exec_relationships_success(self, neo4j_session):
        """Test successful creation of CAN_EXEC relationships"""
        # Mock successful query result
        mock_result = Mock()
        mock_result.single.return_value = None
        mock_result.__iter__ = Mock(return_value=iter([
            {
                "principal.arn": "arn:aws:iam::123456789012:user/test-user",
                "principal.name": "test-user",
                "user_permissions": REQUIRED_PERMISSIONS
            }
        ]))
        neo4j_session.run.return_value = mock_result

        # Execute the function
        create_datapipeline_can_exec_relationships(neo4j_session)

        # Verify the function was called
        assert neo4j_session.run.call_count == 2  # One for finding principals, one for creating relationships

    def test_get_privilege_escalation_summary(self, neo4j_session):
        """Test getting privilege escalation summary"""
        # Mock query results
        mock_result = Mock()
        mock_result.single.side_effect = [
            {"high_risk_principals": 2, "total_can_exec_relationships": 4},
            {"false_positives_prevented": 1}
        ]
        neo4j_session.run.return_value = mock_result

        # Execute the function
        summary = get_datapipeline_privilege_escalation_summary(neo4j_session)

        # Verify results
        assert summary["high_risk_principals"] == 2
        assert summary["total_can_exec_relationships"] == 4
        assert summary["false_positives_prevented"] == 1
        assert summary["logic_type"] == "AND_LOGIC"
        assert summary["required_permissions"] == REQUIRED_PERMISSIONS

    def test_cleanup_datapipeline_can_exec_relationships(self, neo4j_session):
        """Test cleanup of CAN_EXEC relationships"""
        # Mock query result
        mock_result = Mock()
        neo4j_session.run.return_value = mock_result

        # Execute the function
        cleanup_datapipeline_can_exec_relationships(neo4j_session, 1234567890)

        # Verify the function was called with correct parameters
        neo4j_session.run.assert_called_once()
        call_args = neo4j_session.run.call_args
        assert "update_tag" in str(call_args)
        assert "1234567890" in str(call_args)

    def test_validate_datapipeline_and_logic(self, neo4j_session):
        """Test AND logic validation"""
        # Mock query result for principals with partial permissions
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            {
                "principal.name": "partial-user",
                "user_permissions": ["iam:PassRole", "datapipeline:CreatePipeline"],  # Missing 2 permissions
                "can_exec_count": 0  # Should be 0 for AND logic to work
            }
        ]))
        neo4j_session.run.return_value = mock_result

        # Execute the function
        validation_results = validate_datapipeline_and_logic(neo4j_session)

        # Verify results
        assert len(validation_results) == 1
        assert validation_results[0]["principal_name"] == "partial-user"
        assert validation_results[0]["can_exec_count"] == 0
        assert validation_results[0]["validation"] == "PASS"

    def test_validate_datapipeline_and_logic_failure(self, neo4j_session):
        """Test AND logic validation failure case"""
        # Mock query result for principals with partial permissions but incorrect CAN_EXEC
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            {
                "principal.name": "false-positive-user",
                "user_permissions": ["iam:PassRole", "datapipeline:CreatePipeline"],  # Missing 2 permissions
                "can_exec_count": 1  # Should be 0 - this indicates a failure
            }
        ]))
        neo4j_session.run.return_value = mock_result

        # Execute the function
        validation_results = validate_datapipeline_and_logic(neo4j_session)

        # Verify results
        assert len(validation_results) == 1
        assert validation_results[0]["principal_name"] == "false-positive-user"
        assert validation_results[0]["can_exec_count"] == 1
        assert validation_results[0]["validation"] == "FAIL"

    def test_no_principals_with_all_permissions(self, neo4j_session):
        """Test case where no principals have all required permissions"""
        # Mock empty result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        neo4j_session.run.return_value = mock_result

        # Execute the function
        create_datapipeline_can_exec_relationships(neo4j_session)

        # Verify only the finding query was called (no creation queries)
        assert neo4j_session.run.call_count == 1

    def test_get_privilege_escalation_summary_empty(self, neo4j_session):
        """Test getting summary with no data"""
        # Mock empty results
        mock_result = Mock()
        mock_result.single.side_effect = [None, None]
        neo4j_session.run.return_value = mock_result

        # Execute the function
        summary = get_datapipeline_privilege_escalation_summary(neo4j_session)

        # Verify results
        assert summary["high_risk_principals"] == 0
        assert summary["total_can_exec_relationships"] == 0
        assert summary["false_positives_prevented"] == 0
        assert summary["logic_type"] == "AND_LOGIC"
