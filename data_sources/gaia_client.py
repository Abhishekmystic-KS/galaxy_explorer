from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
import astropy.units as u

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
        "phot_g_mean_mag": None
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
            properties["parallax"] = float(best_match["parallax"]) if not best_match["parallax"].mask else None
            properties["parallax_error"] = float(best_match["parallax_error"]) if not best_match["parallax_error"].mask else None
            properties["pmra"] = float(best_match["pmra"]) if not best_match["pmra"].mask else None
            properties["pmra_error"] = float(best_match["pmra_error"]) if not best_match["pmra_error"].mask else None
            properties["pmdec"] = float(best_match["pmdec"]) if not best_match["pmdec"].mask else None
            properties["pmdec_error"] = float(best_match["pmdec_error"]) if not best_match["pmdec_error"].mask else None
            properties["phot_g_mean_mag"] = float(best_match["phot_g_mean_mag"]) if not best_match["phot_g_mean_mag"].mask else None
            
    except Exception as e:
        print(f"Gaia query failed: {e}. Using fallback/empty astrometry.")
        
    return properties
