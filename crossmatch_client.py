import re
import random
from data_sources.cache import get_cached_value, set_cached_value, resolve_popular_galaxy
from data_sources.simbad_client import query_simbad_by_name, query_simbad_by_coords
from data_sources.ned_client import query_ned_by_name, query_ned_by_coords

def parse_coordinate_query(query: str) -> tuple:
    """
    Tries to parse coordinates from queries like:
    '185.728, 15.823' or 'ra=120.5 dec=-10.2' or '10 40 30 -05 12 10'
    Returns (ra_deg, dec_deg) as floats or None.
    """
    clean = query.strip()
    
    # 1. Decimal coordinates: e.g. "185.728 15.823" or "185.728, -15.823"
    dec_match = re.match(r"^([\+\-]?\d+(?:\.\d+)?)\s*[\s,]\s*([\+\-]?\d+(?:\.\d+)?)$", clean)
    if dec_match:
        try:
            ra = float(dec_match.group(1))
            dec = float(dec_match.group(2))
            if 0 <= ra <= 360 and -90 <= dec <= 90:
                return ra, dec
        except ValueError:
            pass
            
    # 2. Key-value format: e.g. "ra=185.728 dec=15.823" or "ra:185.728, dec:15.823"
    kv_match = re.search(r"(?:ra|dec)\s*[:=]\s*([\+\-]?\d+(?:\.\d+)?)", clean, re.IGNORECASE)
    if kv_match:
        try:
            ra_find = re.findall(r"ra\s*[:=]\s*([\+\-]?\d+(?:\.\d+)?)", clean, re.IGNORECASE)
            dec_find = re.findall(r"dec\s*[:=]\s*([\+\-]?\d+(?:\.\d+)?)", clean, re.IGNORECASE)
            if ra_find and dec_find:
                ra = float(ra_find[0])
                dec = float(dec_find[0])
                if 0 <= ra <= 360 and -90 <= dec <= 90:
                    return ra, dec
        except ValueError:
            pass
            
    return None

def crossmatch_by_name(name: str) -> dict:
    """
    Cross-matches a galaxy by name using cache -> popular -> SIMBAD -> NED -> Mock fallback.
    """
    cache_key = f"name_{name.strip().lower()}"
    cached = get_cached_value(cache_key)
    if cached:
        return cached

    # 1. Popular galaxies resolver
    popular = resolve_popular_galaxy(name)
    if popular:
        set_cached_value(cache_key, popular)
        return popular

    # 2. Check if name is actually a coordinate pair
    parsed_coords = parse_coordinate_query(name)
    if parsed_coords:
        ra, dec = parsed_coords
        res = crossmatch_by_coords(ra, dec)
        # Add original query name as alias
        if res:
            if name not in res.get("aliases", []):
                res.setdefault("aliases", []).append(name)
            set_cached_value(cache_key, res)
            return res

    # 3. Query SIMBAD (Primary)
    simbad_res = query_simbad_by_name(name)
    if simbad_res:
        simbad_res["aliases"] = [name, simbad_res["name"]]
        set_cached_value(cache_key, simbad_res)
        return simbad_res

    # 4. Query NED (Fallback)
    ned_res = query_ned_by_name(name)
    if ned_res:
        ned_res["aliases"] = [name, ned_res["name"]]
        set_cached_value(cache_key, ned_res)
        return ned_res

    # 5. Offline / Unresolved Mock Generator
    # Generate mock values deterministically based on name hash so it's consistent
    seed = sum(ord(c) for c in name)
    random.seed(seed)
    
    mock_ra = random.uniform(0, 360)
    mock_dec = random.uniform(-30, 80) # typical observable sky range
    mock_types = ["Spiral Galaxy", "Elliptical Galaxy", "Lenticular Galaxy", "Irregular Galaxy"]
    
    mock_res = {
        "name": name.upper(),
        "ra": round(mock_ra, 4),
        "dec": round(mock_dec, 4),
        "type": random.choice(mock_types),
        "aliases": [name],
        "redshift": round(random.uniform(0.001, 0.15), 4),
        "redshift_err": 0.0001,
        "mag": round(random.uniform(9.0, 16.0), 2),
        "mag_err": 0.05,
        "source": "SIMULATION"
    }
    
    set_cached_value(cache_key, mock_res)
    return mock_res

def crossmatch_by_coords(ra: float, dec: float) -> dict:
    """
    Cross-matches coordinates to a galaxy profile using cache -> SIMBAD -> NED -> Mock fallback.
    """
    cache_key = f"coords_{ra:.4f}_{dec:.4f}"
    cached = get_cached_value(cache_key)
    if cached:
        return cached

    # 1. Query SIMBAD
    simbad_res = query_simbad_by_coords(ra, dec)
    if simbad_res:
        simbad_res["aliases"] = [simbad_res["name"]]
        set_cached_value(cache_key, simbad_res)
        return simbad_res

    # 2. Query NED
    ned_res = query_ned_by_coords(ra, dec)
    if ned_res:
        ned_res["aliases"] = [ned_res["name"]]
        set_cached_value(cache_key, ned_res)
        return ned_res

    # 3. Coordinate Mock Fallback
    seed = int(ra * 1000) + int(dec * 1000)
    random.seed(seed)
    
    mock_types = ["Spiral Galaxy", "Elliptical Galaxy", "Lenticular Galaxy", "Irregular Galaxy"]
    mock_res = {
        "name": f"GSC {ra:.4f}_{dec:.4f}",
        "ra": ra,
        "dec": dec,
        "type": random.choice(mock_types),
        "aliases": [f"COORD_{ra:.4f}_{dec:.4f}"],
        "redshift": round(random.uniform(0.001, 0.15), 4),
        "redshift_err": 0.0001,
        "mag": round(random.uniform(10.0, 17.0), 2),
        "mag_err": 0.08,
        "source": "SIMULATION"
    }
    
    set_cached_value(cache_key, mock_res)
    return mock_res
