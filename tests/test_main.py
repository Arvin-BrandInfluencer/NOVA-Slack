import pytest
from main import normalize_market_name, process_routing_params

@pytest.mark.parametrize("input_name, expected_name", [
    ("uk", "UK"),
    ("United Kingdom", "UK"),
    ("france", "France"),
    ("FR", "France"),
    ("sweden", "Sweden"),
    ("NORWAY", "Norway"),
    ("Denmark", "Denmark"),
    ("NORDICS", "Nordics"),
    ("germany", "Germany"), # Test fallback to capitalize
    (None, None),
    (123, 123),
])
def test_normalize_market_name(input_name, expected_name):
    assert normalize_market_name(input_name) == expected_name

def test_process_routing_params_applies_defaults():
    params = {"market": "uk"}
    processed = process_routing_params(params)
    assert processed["market"] == "UK"
    assert processed["year"] == 2025 # Default year applied

def test_process_routing_params_preserves_existing_year():
    params = {"market": "france", "year": 2024}
    processed = process_routing_params(params)
    assert processed["market"] == "France"
    assert processed["year"] == 2024
