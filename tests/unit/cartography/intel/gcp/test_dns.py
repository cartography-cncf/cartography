from unittest.mock import MagicMock, patch
from googleapiclient.discovery import HttpError
from cartography.intel.gcp.dns import get_dns_rrs, get_dns_zones
import tests.data.gcp.dns
import json


def test_get_dns_zones_success():
    """Test that get_dns_zones successfully retrieves DNS zones."""
    # Arrange
    mock_dns = MagicMock()
    mock_request = MagicMock()
    mock_response = {"managedZones": tests.data.gcp.dns.DNS_ZONES}
    mock_dns.managedZones().list.return_value = mock_request
    mock_request.execute.return_value = mock_response
    mock_dns.managedZones().list_next.return_value = None  # No pagination

    project_id = "test-project"

    # Act
    result = get_dns_zones(mock_dns, project_id)

    # Assert
    assert len(result) == 2
    assert result[0]["id"] == "111111111111111111111"
    assert result[1]["id"] == "2222222222222222222"
    mock_dns.managedZones().list.assert_called_once_with(project=project_id)


def test_get_dns_zones_permission_denied():
    """Test that get_dns_zones handles permission denied errors gracefully."""
    # Arrange
    mock_dns = MagicMock()
    error_content = json.dumps({
        "error": {
            "status": "PERMISSION_DENIED",
            "code": 403,
            "message": "Insufficient permissions"
        }
    }).encode('utf-8')

    http_error = HttpError(
        resp=MagicMock(status=403),
        content=error_content
    )
    mock_dns.managedZones().list.return_value.execute.side_effect = http_error

    project_id = "test-project"

    # Act
    result = get_dns_zones(mock_dns, project_id)

    # Assert
    assert result == []  # Should return empty list, not raise exception


def test_get_dns_zones_other_http_error():
    """Test that get_dns_zones re-raises non-permission HTTP errors."""
    # Arrange
    mock_dns = MagicMock()
    error_content = json.dumps({
        "error": {
            "status": "INTERNAL_ERROR",
            "code": 500,
            "message": "Internal server error"
        }
    }).encode('utf-8')

    http_error = HttpError(
        resp=MagicMock(status=500),
        content=error_content
    )
    mock_dns.managedZones().list.return_value.execute.side_effect = http_error

    project_id = "test-project"

    # Act & Assert
    try:
        get_dns_zones(mock_dns, project_id)
        assert False, "Expected HttpError to be raised"
    except HttpError:
        pass  # This is expected


def test_get_dns_rrs_success():
    """Test that get_dns_rrs successfully retrieves DNS resource records."""
    # Arrange
    mock_dns = MagicMock()
    mock_request = MagicMock()
    mock_response = {"rrsets": tests.data.gcp.dns.DNS_RRS}
    mock_dns.resourceRecordSets().list.return_value = mock_request
    mock_request.execute.return_value = mock_response
    mock_dns.resourceRecordSets().list_next.return_value = None  # No pagination

    dns_zones = [{"id": "test-zone-1"}, {"id": "test-zone-2"}]
    project_id = "test-project"

    # Act
    result = get_dns_rrs(mock_dns, dns_zones, project_id)

    # Assert
    assert len(result) == 6  
    for record in result:
        assert "zone" in record
        assert record["zone"] in ["test-zone-1", "test-zone-2"]


def test_get_dns_rrs_permission_denied():
    """Test that get_dns_rrs handles permission denied errors gracefully."""
    # Arrange
    mock_dns = MagicMock()
    error_content = json.dumps({
        "error": {
            "status": "PERMISSION_DENIED",
            "code": 403,
            "message": "Forbidden"
        }
    }).encode('utf-8')

    http_error = HttpError(
        resp=MagicMock(status=403),
        content=error_content
    )
    mock_dns.resourceRecordSets().list.return_value.execute.side_effect = (
        http_error
    )

    dns_zones = [{"id": "test-zone-1"}]
    project_id = "test-project"

    # Act
    result = get_dns_rrs(mock_dns, dns_zones, project_id)

    # Assert
    assert result == []  


def test_get_dns_rrs_empty_zones():
    """Test that get_dns_rrs handles empty zone list correctly."""
    # Arrange
    mock_dns = MagicMock()
    dns_zones = []
    project_id = "test-project"

    # Act
    result = get_dns_rrs(mock_dns, dns_zones, project_id)

    # Assert
    assert result == []
    
    mock_dns.resourceRecordSets().list.assert_not_called()


def test_get_dns_rrs_other_http_error():
    """Test that get_dns_rrs re-raises non-permission HTTP errors."""
    # Arrange
    mock_dns = MagicMock()
    error_content = json.dumps({
        "error": {
            "status": "INTERNAL_ERROR",
            "code": 500,
            "message": "Internal server error"
        }
    }).encode('utf-8')

    http_error = HttpError(
        resp=MagicMock(status=500),
        content=error_content
    )
    mock_dns.resourceRecordSets().list.return_value.execute.side_effect = (
        http_error
    )

    dns_zones = [{"id": "test-zone-1"}]
    project_id = "test-project"

    # Act & Assert
    try:
        get_dns_rrs(mock_dns, dns_zones, project_id)
        assert False, "Expected HttpError to be raised"
    except HttpError:
        pass  