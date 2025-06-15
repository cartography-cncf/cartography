def load_ontology_mapping(module_name: str) -> dict:
    # DOC
    import json
    import pkgutil

    data = pkgutil.get_data("cartography.data.ontology", f"{module_name}.json")
    if data is None:
        raise ValueError(f"Mapping file for {module_name} not found.")

    return json.loads(data.decode("utf-8"))
