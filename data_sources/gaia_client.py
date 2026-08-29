from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
import astropy.units as u
import math


def _masked_float(value):
    if value is None:
        return None
    if getattr(value, "mask", False):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_satellite_points(rows, center_ra: float, center_dec: float, limit: int = 120):
    satellite_points = []
    cos_dec = math.cos(math.radians(center_dec))
    colnames = set(getattr(rows, "colnames", []))

    for idx, row in enumerate(rows[:limit]):
        ra_value = _masked_float(row["ra"]) if "ra" in colnames else None
        dec_value = _masked_float(row["dec"]) if "dec" in colnames else None
        if ra_value is None or dec_value is None:
            continue

        delta_ra_deg = ra_value - center_ra
        if delta_ra_deg > 180:
            delta_ra_deg -= 360
        elif delta_ra_deg < -180:
            delta_ra_deg += 360

        x = delta_ra_deg * 3600 * cos_dec
        y = (dec_value - center_dec) * 3600

        parallax = _masked_float(row["parallax"]) if "parallax" in colnames else None
        mag = _masked_float(row["phot_g_mean_mag"]) if "phot_g_mean_mag" in colnames else None
        if parallax is not None and parallax > 0:
            z = min(2500.0, 1000.0 / parallax)
        else:
            fallback_mag = mag if mag is not None else 15.0
            z = max(10.0, min(2500.0, (fallback_mag + 1.0) * 65.0 + (idx % 7) * 12.0))

        satellite_points.append({
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "mag": round(mag, 3) if mag is not None else None,
            "parallax": round(parallax, 4) if parallax is not None else None
        })

    return satellite_points

def fetch_gaia_astrometry(ra: float, dec: float, radius_arcsec: float = 5.0) -> dict:
    """
    Queries Gaia DR3 at the given coordinates to retrieve proper motion and parallax.
    Falls back to mock/empty properties if it fails.
    """
    properties = {
        "parallax": None,
        "parallax_error": None,
        "pmra": None,
        "pmra_error": None,
        "pmdec": None,
        "pmdec_error": None,
        "phot_g_mean_mag": None,
        "satellite_points": []
    }
    
    try:
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        # Query Gaia cone search
        j = Gaia.cone_search_async(coord, radius=radius_arcsec*u.arcsec)
        r = j.get_results()
        
        if r is not None and len(r) > 0:
            # Sort by distance from center if multiple matches (usually the closest is the center galaxy / bright core)
            # Take the first entry
            best_match = r[0]
            properties["parallax"] = _masked_float(best_match["parallax"])
            properties["parallax_error"] = _masked_float(best_match["parallax_error"])
            properties["pmra"] = _masked_float(best_match["pmra"])
            properties["pmra_error"] = _masked_float(best_match["pmra_error"])
            properties["pmdec"] = _masked_float(best_match["pmdec"])
            properties["pmdec_error"] = _masked_float(best_match["pmdec_error"])
            properties["phot_g_mean_mag"] = _masked_float(best_match["phot_g_mean_mag"])
            properties["satellite_points"] = _build_satellite_points(r, ra, dec)
            
    except Exception as e:
        print(f"Gaia query failed: {e}. Using fallback/empty astrometry.")
        
    return properties
