# Pull Request Summary: Tailscale Device Posture Attributes

## Overview
This PR implements support for Tailscale device posture attributes as requested in issue #1821.

## Changes Made

### 1. New Model: `TailscaleDevicePostureAttribute`
**File:** `cartography/models/tailscale/devicepostureattribute.py`

Created a new node model to represent device posture attributes with:
- Properties: `id`, `key`, `value`, `updated`, `lastupdated`
- Relationship: `HAS_POSTURE_ATTRIBUTE` connecting to `TailscaleDevice`

### 2. Updated Intel Module: `devices.py`
**File:** `cartography/intel/tailscale/devices.py`

Added functionality to fetch and load posture attributes:
- `get_posture_attributes()`: Fetches attributes from `/device/{deviceId}/attributes` endpoint
- `load_posture_attributes()`: Loads attributes into the graph
- Updated `sync()` to call these new functions
- Updated `cleanup()` to include the new schema

### 3. Test Data
**File:** `tests/data/tailscale/devicepostureattributes.py`

Added test data with examples from:
- CrowdStrike Falcon (ztaScore, osVersion)
- Microsoft Intune (complianceState, managedDeviceOwnerType)

### 4. Integration Tests
**File:** `tests/integration/cartography/intel/tailscale/test_devicepostureattributes.py`

Created comprehensive tests to verify:
- Posture attributes are loaded correctly
- Relationships with devices are established
- Node properties are set properly

### 5. Documentation
**File:** `docs/root/modules/tailscale/schema.md`

Updated schema documentation:
- Added `TailscaleDevicePostureAttribute` to the mermaid diagram
- Documented all fields and relationships
- Added examples of attribute keys from different providers

## Technical Details

### API Endpoint
The implementation uses the Tailscale API endpoint:
```
GET /device/{deviceId}/attributes
```

### Supported Integrations
The posture attributes can come from any of these integrations:
- CrowdStrike Falcon
- Microsoft Intune
- Jamf Pro
- Kandji
- Kolide
- SentinelOne

### Error Handling
- Gracefully handles devices without posture attributes
- Logs debug messages for HTTP errors (404s expected for devices without attributes)
- Continues processing other devices if one fails

## Verification Steps

1. Code compiles without syntax errors ✓
2. All new files follow project conventions ✓
3. Documentation updated ✓
4. Test coverage added ✓

## Closes
Fixes #1821
