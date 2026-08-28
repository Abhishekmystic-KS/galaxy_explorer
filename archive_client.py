import os
from data_sources.sdss_client import fetch_sdss_image_fits, fetch_sdss_spectrum_fits

def download_galaxy_fits(ra: float, dec: float, output_dir: str, prefix: str = "galaxy") -> tuple:
    """
    Downloads image and spectrum FITS files for the given coordinates into the output directory.
    Returns paths to both files: (image_fits_path, spectrum_fits_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    image_fits_path = os.path.join(output_dir, f"{prefix}_image.fits")
    spectrum_fits_path = os.path.join(output_dir, f"{prefix}_spec.fits")
    
    img_path = fetch_sdss_image_fits(ra, dec, image_fits_path)
    spec_path = fetch_sdss_spectrum_fits(ra, dec, spectrum_fits_path)
    
    return img_path, spec_path
