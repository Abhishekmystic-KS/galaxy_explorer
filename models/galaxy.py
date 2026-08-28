from pydantic import BaseModel
from typing import List, Optional

class GalaxyProfile(BaseModel):
    name: str
    ra: float
    dec: float
    type: str = "Unknown"
    aliases: List[str] = []
    
    # Redshift details
    redshift: Optional[float] = None
    redshift_err: Optional[float] = None
    classification: Optional[str] = None
    
    # Photometry details
    mag: Optional[float] = None
    mag_err: Optional[float] = None
    phot_error: Optional[float] = None
    filter: Optional[str] = None
    exptime: Optional[float] = None
    
    # Instrument details
    instrument: Optional[str] = None
    telescope: Optional[str] = None
    image_quality: Optional[str] = None
    source: str = "Unknown"
    
    # Gaia Astrometry
    parallax: Optional[float] = None
    parallax_error: Optional[float] = None
    pmra: Optional[float] = None
    pmra_error: Optional[float] = None
    pmdec: Optional[float] = None
    pmdec_error: Optional[float] = None
    phot_g_mean_mag: Optional[float] = None
