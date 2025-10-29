#!/usr/bin/env python3
"""
Validation script to check the Google Workspace module duplication
"""

import sys
import os

# Add the cartography directory to the path
sys.path.insert(0, '/Users/jchapeau/src/cartography')

def test_model_imports():
    """Test that our data model schemas can be imported"""
    try:
        from cartography.models.googleworkspace.tenant import GoogleWorkspaceTenantSchema
        from cartography.models.googleworkspace.user import GoogleWorkspaceUserSchema  
        from cartography.models.googleworkspace.group import GoogleWorkspaceGroupSchema
        print("✅ All data model schemas import successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import data models: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    base_path = "/Users/jchapeau/src/cartography"
    required_files = [
        "cartography/models/googleworkspace/__init__.py",
        "cartography/models/googleworkspace/tenant.py",
        "cartography/models/googleworkspace/user.py", 
        "cartography/models/googleworkspace/group.py",
        "cartography/intel/googleworkspace/__init__.py",
        "cartography/intel/googleworkspace/users.py",
        "cartography/intel/googleworkspace/groups.py",
        "tests/data/googleworkspace/__init__.py",
        "tests/data/googleworkspace/api.py",
        "tests/integration/cartography/intel/googleworkspace/__init__.py",
        "tests/integration/cartography/intel/googleworkspace/test_api.py",
        "docs/root/modules/googleworkspace/index.md",
        "docs/root/modules/googleworkspace/config.md", 
        "docs/root/modules/googleworkspace/schema.md",
        "cartography/data/jobs/analysis/googleworkspace_human_link.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_cli_changes():
    """Test that CLI changes are present"""
    cli_path = "/Users/jchapeau/src/cartography/cartography/cli.py"
    with open(cli_path, 'r') as f:
        cli_content = f.read()
    
    required_strings = [
        "--googleworkspace-auth-method",
        "--googleworkspace-tokens-env-var",
        "googleworkspace_tokens_env_var",
        "googleworkspace_config"
    ]
    
    missing = []
    for required in required_strings:
        if required not in cli_content:
            missing.append(required)
    
    if missing:
        print(f"❌ Missing CLI strings: {missing}")
        return False
    else:
        print("✅ CLI changes are present")
        return True

def test_config_changes():
    """Test that config changes are present"""
    config_path = "/Users/jchapeau/src/cartography/cartography/config.py"
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    required_strings = [
        "googleworkspace_auth_method",
        "googleworkspace_config",
        "self.googleworkspace_auth_method",
        "self.googleworkspace_config"
    ]
    
    missing = []
    for required in required_strings:
        if required not in config_content:
            missing.append(required)
    
    if missing:
        print(f"❌ Missing config strings: {missing}")
        return False
    else:
        print("✅ Config changes are present")
        return True

def test_sync_changes():
    """Test that sync changes are present"""
    sync_path = "/Users/jchapeau/src/cartography/cartography/sync.py"
    with open(sync_path, 'r') as f:
        sync_content = f.read()
    
    required_strings = [
        "import cartography.intel.googleworkspace",
        '"googleworkspace": cartography.intel.googleworkspace.start_googleworkspace_ingestion'
    ]
    
    missing = []
    for required in required_strings:
        if required not in sync_content:
            missing.append(required)
    
    if missing:
        print(f"❌ Missing sync strings: {missing}")
        return False
    else:
        print("✅ Sync changes are present")
        return True

def main():
    """Run all validation tests"""
    print("🚀 Validating Google Workspace module duplication...")
    print()
    
    tests = [
        test_file_structure,
        test_model_imports,
        test_cli_changes,
        test_config_changes,
        test_sync_changes
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    total = len(tests)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Google Workspace module duplication is complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())