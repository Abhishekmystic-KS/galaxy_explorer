import os
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from PIL import Image

def normalize_image(data):
    """Normalize FITS 2D image data using log stretch for better visualization."""
    # Handle NaNs and infinite values
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Clip extreme values (outliers)
    vmin, vmax = np.percentile(data, [1, 99.5])
    data = np.clip(data, vmin, vmax)
    
    # Log stretch: log(1 + data - min)
    min_val = data.min()
    data = data - min_val
    log_data = np.log1p(data)
    
    # Scale to 0-255
    log_max = log_data.max()
    if log_max > 0:
        scaled = (log_data / log_max * 255.0).astype(np.uint8)
    else:
        scaled = np.zeros_like(log_data, dtype=np.uint8)
        
    return scaled

def analyze_fits_image(filepath: str, output_png_path: str) -> dict:
    """
    Parses a 2D image FITS file.
    Saves a contrast-stretched PNG cutout.
    Extracts metadata: RA, Dec, exposure time, photometric filter, etc.
    """
    properties = {
        "type": "image",
        "ra": None,
        "dec": None,
        "filter": None,
        "exptime": None,
        "instrument": None,
        "telescope": None,
        "phot_error": None,  # Photometric error approximation
        "image_quality": "Unknown"
    }
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"FITS file not found at {filepath}")
        
    with fits.open(filepath) as hdul:
        # Look for the first HDU containing 2D image data
        image_hdu = None
        for hdu in hdul:
            if hdu.data is not None and len(hdu.data.shape) == 2:
                image_hdu = hdu
                break
                
        if image_hdu is None:
            # Fallback to primary if empty, or throw error
            image_hdu = hdul[0]
            
        header = image_hdu.header
        
        # Read coordinates
        properties["ra"] = header.get("CRVAL1", header.get("RA", None))
        properties["dec"] = header.get("CRVAL2", header.get("DEC", None))
        
        # Other common keys
        properties["filter"] = header.get("FILTER", header.get("FILTERS", "Unknown"))
        properties["exptime"] = header.get("EXPTIME", header.get("EXPOSURE", None))
        properties["instrument"] = header.get("INSTRUME", "Unknown")
        properties["telescope"] = header.get("TELESCOP", "Unknown")
        
        # Approximate image quality / error
        properties["phot_error"] = header.get("SKYERR", header.get("SIGMA", 0.05))
        
        # Basic quality classification
        seeing = header.get("SEEING", None)
        if seeing is not None:
            properties["image_quality"] = f"Seeing: {seeing}\""
        else:
            properties["image_quality"] = "Nominal"

        # Generate PNG cutout
        if image_hdu.data is not None:
            normalized = normalize_image(image_hdu.data)
            # Create PNG image (grayscale)
            img = Image.fromarray(normalized)
            img.save(output_png_path)
        else:
            # Generate a blank placeholder image if FITS is somehow empty
            img = Image.new("L", (256, 256), color=10)
            img.save(output_png_path)
            
    return properties

def analyze_fits_spectrum(filepath: str) -> dict:
    """
    Parses a 1D or 2D spectrum FITS file.
    Extracts redshift, redshift error, spectral classification, and spectrum data points (wavelength, flux).
    """
    properties = {
        "type": "spectrum",
        "redshift": None,
        "redshift_err": None,
        "classification": "Unknown",
        "wavelengths": [],
        "flux": [],
        "ivar": []
    }
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"FITS file not found at {filepath}")
        
    with fits.open(filepath) as hdul:
        # Search for tabular data containing spectrum (usually in HDU 1)
        spec_table = None
        for hdu in hdul:
            if hdu.data is not None and isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                spec_table = hdu
                break
        
        # Read header keys from primary HDU or table HDU
        header = hdul[0].header
        properties["redshift"] = header.get("Z", header.get("REDSHIFT", None))
        properties["redshift_err"] = header.get("Z_ERR", header.get("REDSHIFT_ERR", None))
        properties["classification"] = header.get("CLASS", header.get("SPECTRAL_CLASS", "Unknown"))
        
        # If no redshift in header, check if there is an alternative table or fallback
        if spec_table is not None:
            # Check column names
            colnames = spec_table.columns.names
            
            # SDSS uses 'flux', 'loglam', 'ivar'
            flux_col = next((c for c in colnames if c.lower() in ('flux', 'flux_density')), None)
            lam_col = next((c for c in colnames if c.lower() in ('loglam', 'wavelength', 'wave')), None)
            ivar_col = next((c for c in colnames if c.lower() in ('ivar', 'error', 'err', 'sig')), None)
            
            if flux_col and lam_col:
                flux_data = spec_table.data[flux_col]
                lam_data = spec_table.data[lam_col]
                
                # If loglam, convert to standard wavelength (Angstroms)
                if lam_col.lower() == 'loglam':
                    wavelengths = 10 ** lam_data
                else:
                    wavelengths = lam_data
                    
                properties["wavelengths"] = wavelengths.tolist()
                properties["flux"] = flux_data.tolist()
                
                if ivar_col:
                    properties["ivar"] = spec_table.data[ivar_col].tolist()
                    
        # Fallback if no table but 1D array in primary HDU (common for simple spectra)
        if not properties["wavelengths"] and len(hdul[0].shape) == 1:
            data = hdul[0].data
            if data is not None:
                # Reconstruct wavelengths from header WCS (CRVAL1, CDELT1)
                crval = header.get("CRVAL1", 1.0)
                cdelt = header.get("CDELT1", 1.0)
                crpix = header.get("CRPIX1", 1)
                
                indices = np.arange(len(data))
                # wavelength = crval + (index - crpix) * cdelt
                # if log-spaced:
                cunit = header.get("CUNIT1", "Angstrom").lower()
                
                log_spaced = "log" in header.get("CTYPE1", "").lower()
                if log_spaced:
                    wavelengths = 10 ** (crval + (indices - crpix) * cdelt)
                else:
                    wavelengths = crval + (indices - crpix) * cdelt
                    
                properties["wavelengths"] = wavelengths.tolist()
                properties["flux"] = data.tolist()
                properties["ivar"] = [1.0] * len(data)

    return properties
