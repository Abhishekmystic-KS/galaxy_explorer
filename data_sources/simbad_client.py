from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u

# Set up Simbad query with extra fields
def _get_custom_simbad():
    custom_simbad = Simbad()
    # Remove existing fields if needed or just add new ones
    # Simbad default fields include MAIN_ID, RA, DEC
    custom_simbad.add_votable_fields('z_value', 'z_err', 'otype', 'flux(V)', 'flux(R)', 'fe_err(V)', 'fe_err(R)')
    return custom_simbad

def query_simbad_by_name(name: str) -> dict:
    """
    Queries SIMBAD for a galaxy by name.
    Returns metadata dict, or None if not found or query fails.
    """
    try:
        simbad = _get_custom_simbad()
        result = simbad.query_object(name)
        if result is not None and len(result) > 0:
            row = result[0]
            
            # Extract RA / Dec
            ra_str = str(row["RA"])
            dec_str = str(row["DEC"])
            
            # Convert RA/Dec to degrees
            try:
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                ra_deg = float(coord.ra.deg)
                dec_deg = float(coord.dec.deg)
            except Exception:
                # If coordinate parsing fails, try float conversion or fallback
                ra_deg = float(row.get("RA_d", 0.0))
                dec_deg = float(row.get("DEC_d", 0.0))
            
            # Extract redshift and error
            z = float(row["Z_VALUE"]) if not row["Z_VALUE"].mask else None
            z_err = float(row["Z_ERR"]) if not row["Z_ERR"].mask else None
            
            # Extract magnitude (V band first, then R band)
            mag = None
            mag_err = None
            if not row["FLUX_V"].mask:
                mag = float(row["FLUX_V"])
                mag_err = float(row["FE_ERR_V"]) if "FE_ERR_V" in row.colnames and not row["FE_ERR_V"].mask else None
            elif not row["FLUX_R"].mask:
                mag = float(row["FLUX_R"])
                mag_err = float(row["FE_ERR_R"]) if "FE_ERR_R" in row.colnames and not row["FE_ERR_R"].mask else None
                
            return {
                "name": str(row["MAIN_ID"]),
                "ra": ra_deg,
                "dec": dec_deg,
                "type": str(row["OTYPE"]) if not row["OTYPE"].mask else "Galaxy",
                "redshift": z,
                "redshift_err": z_err,
                "mag": mag,
                "mag_err": mag_err,
                "source": "SIMBAD"
            }
    except Exception as e:
        print(f"SIMBAD query by name failed: {e}")
        
    return None

def query_simbad_by_coords(ra: float, dec: float, radius_arcsec: float = 10.0) -> dict:
    """
    Queries SIMBAD for a galaxy near coordinates.
    """
    try:
        simbad = _get_custom_simbad()
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        result = simbad.query_region(coord, radius=radius_arcsec*u.arcsec)
        if result is not None and len(result) > 0:
            row = result[0]
            
            ra_str = str(row["RA"])
            dec_str = str(row["DEC"])
            try:
                c = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                ra_deg = float(c.ra.deg)
                dec_deg = float(c.dec.deg)
            except Exception:
                ra_deg = ra
                dec_deg = dec
                
            z = float(row["Z_VALUE"]) if not row["Z_VALUE"].mask else None
            z_err = float(row["Z_ERR"]) if not row["Z_ERR"].mask else None
            
            mag = None
            mag_err = None
            if not row["FLUX_V"].mask:
                mag = float(row["FLUX_V"])
                mag_err = float(row["FE_ERR_V"]) if "FE_ERR_V" in row.colnames and not row["FE_ERR_V"].mask else None
            elif not row["FLUX_R"].mask:
                mag = float(row["FLUX_R"])
                mag_err = float(row["FE_ERR_R"]) if "FE_ERR_R" in row.colnames and not row["FE_ERR_R"].mask else None
                
            return {
                "name": str(row["MAIN_ID"]),
                "ra": ra_deg,
                "dec": dec_deg,
                "type": str(row["OTYPE"]) if not row["OTYPE"].mask else "Galaxy",
                "redshift": z,
                "redshift_err": z_err,
                "mag": mag,
                "mag_err": mag_err,
                "source": "SIMBAD"
            }
    except Exception as e:
        print(f"SIMBAD query by coords failed: {e}")
        
    return None
