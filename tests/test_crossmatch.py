import os
import pytest
from crossmatch_client import parse_coordinate_query, crossmatch_by_name, crossmatch_by_coords
from data_sources.cache import get_cached_value, set_cached_value, DB_PATH

def test_parse_coordinate_query():
    # Valid formats
    assert parse_coordinate_query("185.728 15.823") == (185.728, 15.823)
    assert parse_coordinate_query("185.728, -15.823") == (185.728, -15.823)
    assert parse_coordinate_query("ra=120.5 dec=-10.2") == (120.5, -10.2)
    assert parse_coordinate_query("  RA: 202.46  ,  DEC: 47.19  ") == (202.46, 47.19)
    
    # Invalid formats
    assert parse_coordinate_query("NGC 4321") is None
    assert parse_coordinate_query("185.728") is None
    assert parse_coordinate_query("370.0 45.0") is None  # RA out of bounds
    assert parse_coordinate_query("120.0 -95.0") is None  # Dec out of bounds


def test_popular_galaxy_resolution():
    res = crossmatch_by_name("M51")
    assert res is not None
    assert "Whirlpool Galaxy" in res["aliases"]
    assert res["ra"] == pytest.approx(202.4696)
    assert res["dec"] == pytest.approx(47.1952)
    assert res["mag"] == 8.4


def test_cache_set_get():
    test_key = "test_key_123"
    test_val = {"name": "Test Galaxy", "val": 42}
    
    set_cached_value(test_key, test_val)
    cached = get_cached_value(test_key)
    
    assert cached == test_val


def test_crossmatch_simulation_fallback(mocker):
    # Mock external query calls to guarantee fallback is tested
    mocker.patch("data_sources.simbad_client.query_simbad_by_name", return_value=None)
    mocker.patch("data_sources.ned_client.query_ned_by_name", return_value=None)
    
    res = crossmatch_by_name("UnknownGalaxyXYZ123")
    
    assert res is not None
    assert res["name"] == "UNKNOWNGALAXYXYZ123"
    assert res["source"] == "SIMULATION"
    assert 0 <= res["ra"] <= 360
    assert -90 <= res["dec"] <= 90
