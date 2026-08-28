from astroquery.ned import Ned
from astropy.coordinates import SkyCoord
import astropy.units as u

def query_ned_by_name(name: str) -> dict:
    """
    Queries NASA/IPAC Extragalactic Database (NED) for a galaxy by name.
    """
    try:
        result = Ned.query_object(name)
        if result is not None and len(result) > 0:
            row = result[0]
            
            ra_deg = float(row["RA"]) if "RA" in row.colnames else None
            dec_deg = float(row["DEC"]) if "DEC" in row.colnames else None
            
            z = float(row["Redshift"]) if "Redshift" in row.colnames and not row["Redshift"].mask else None
            # NED doesn't always provide z_err directly in the main query table
            z_err = None
            
            # Extract magnitude if present
            mag = None
            if "Magnitude and Filter" in row.colnames:
                mag_str = str(row["Magnitude and Filter"])
                try:
                    # e.g. "14.5 (V)" or "13.2 g"
                    parts = mag_str.split()
                    if parts:
                        mag = float(parts[0])
                except ValueError:
                    pass
                    
            return {
                "name": str(row["Object Name"]) if "Object Name" in row.colnames else name,
                "ra": ra_deg,
                "dec": dec_deg,
                "type": str(row["Type"]) if "Type" in row.colnames else "Galaxy",
                "redshift": z,
                "redshift_err": z_err,
                "mag": mag,
                "mag_err": None,
                "source": "NED"
            }
    except Exception as e:
        print(f"NED query by name failed: {e}")
        
    return None

def query_ned_by_coords(ra: float, dec: float, radius_arcsec: float = 10.0) -> dict:
    """
    Queries NED for a galaxy near coordinates.
    """
    try:
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        result = Ned.query_region(coord, radius=radius_arcsec*u.arcsec)
        if result is not None and len(result) > 0:
            row = result[0]
            
            ra_deg = float(row["RA"]) if "RA" in row.colnames else ra
            dec_deg = float(row["DEC"]) if "DEC" in row.colnames else dec
            
            z = float(row["Redshift"]) if "Redshift" in row.colnames and not row["Redshift"].mask else None
            
            mag = None
            if "Magnitude and Filter" in row.colnames:
                mag_str = str(row["Magnitude and Filter"])
                try:
                    parts = mag_str.split()
                    if parts:
                        mag = float(parts[0])
                except ValueError:
                    pass
                    
            return {
                "name": str(row["Object Name"]) if "Object Name" in row.colnames else f"NED {ra:.4f} {dec:.4f}",
                "ra": ra_deg,
                "dec": dec_deg,
                "type": str(row["Type"]) if "Type" in row.colnames else "Galaxy",
                "redshift": z,
                "redshift_err": None,
                "mag": mag,
                "mag_err": None,
                "source": "NED"
            }
    except Exception as e:
        print(f"NED query by coords failed: {e}")
        
    return None
