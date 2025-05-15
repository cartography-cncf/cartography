import re

from cartography.sync import Sync



def test_schema_doc():
    # DOC
    include_regex = re.compile(r"{include} ../modules/(\w+)/schema.md")
    
    with open(f"./docs/root/usage/schema.md", "r") as f:
        content = f.read()
    
    included_modules = include_regex.findall(content)
    existing_modules = []
    for m in Sync.list_intel_modules():
        if m in ('analysis', 'create-indexes',):
            continue
        existing_modules.append(m)
            
    assert sorted(included_modules) == sorted(existing_modules)
