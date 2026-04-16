from cartography.intel.ontology.utils import normalize_source_of_truth


def test_normalize_source_of_truth_maps_entra_to_microsoft():
    assert normalize_source_of_truth(["entra"]) == ["microsoft"]


def test_normalize_source_of_truth_dedupes_aliases():
    assert normalize_source_of_truth(["entra", "microsoft", " entra "]) == [
        "microsoft",
    ]
