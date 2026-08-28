import os

def generate_script(profile: dict, fits_image_path: str, fits_spec_path: str, output_path: str):
    """
    Generates a reproducible offline Python script using matplotlib
    to visualize the downloaded FITS image and FITS spectrum.
    """
    # Use relative paths for the offline script
    img_basename = os.path.basename(fits_image_path) if fits_image_path else None
    spec_basename = os.path.basename(fits_spec_path) if fits_spec_path else None
    
    script_content = f'''#!/usr/bin/env python3
"""
Galaxy Intelligence Platform - Reproducible Offline Plotting Script
Galaxy: {profile.get("name", "Unknown")}
Source: {profile.get("source", "Simulation")}
RA/Dec: {profile.get("ra", 0.0)}, {profile.get("dec", 0.0)}
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

# Meta
GALAXY_NAME = "{profile.get("name", "Unknown")}"
RA = {profile.get("ra", 0.0)}
DEC = {profile.get("dec", 0.0)}
REDSHIFT = {profile.get("redshift", "None")}
MAGNITUDE = {profile.get("mag", "None")}

def normalize_image(data):
    # Handle NaNs
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    vmin, vmax = np.percentile(data, [1, 99.5])
    data = np.clip(data, vmin, vmax)
    # Log stretch
    return np.log1p(data - data.min())

def main():
    print(f"Loading files for galaxy: {{GALAXY_NAME}}")
    print(f"RA/Dec: {{RA}}, {{DEC}}")
    print(f"Redshift: {{REDSHIFT}} | Magnitude: {{MAGNITUDE}}")
    
    image_file = "{img_basename}"
    spec_file = "{spec_basename}"
    
    has_image = os.path.exists(image_file)
    has_spec = spec_file and os.path.exists(spec_file)
    
    if not has_image and not has_spec:
        print("Error: FITS files not found in the current directory.")
        print("Please place the downloaded FITS files in the same directory as this script.")
        return

    # Create figure
    num_plots = 0
    if has_image: num_plots += 1
    if has_spec: num_plots += 1
    
    fig = plt.figure(figsize=(12 if num_plots > 1 else 6, 6))
    plot_idx = 1
    
    # 1. Plot FITS image cutout
    if has_image:
        print(f"Reading image FITS: {{image_file}}")
        ax = fig.add_subplot(1, num_plots, plot_idx)
        with fits.open(image_file) as hdul:
            image_hdu = None
            for hdu in hdul:
                if hdu.data is not None and len(hdu.data.shape) == 2:
                    image_hdu = hdu
                    break
            if image_hdu is None:
                image_hdu = hdul[0]
                
            img_data = image_hdu.data
            if img_data is not None:
                norm_data = normalize_image(img_data)
                im = ax.imshow(norm_data, cmap='gray', origin='lower')
                ax.set_title(f"{{GALAXY_NAME}} - Image Cutout")
                ax.set_xlabel("Pixels")
                ax.set_ylabel("Pixels")
                plt.colorbar(im, ax=ax, label="Log Intensity")
            else:
                ax.text(0.5, 0.5, "Empty Image HDU", ha='center', va='center')
        plot_idx += 1

    # 2. Plot FITS spectrum
    if has_spec:
        print(f"Reading spectrum FITS: {{spec_file}}")
        ax = fig.add_subplot(1, num_plots, plot_idx)
        with fits.open(spec_file) as hdul:
            spec_table = None
            for hdu in hdul:
                if hdu.data is not None and isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    spec_table = hdu
                    break
                    
            if spec_table is not None:
                colnames = spec_table.columns.names
                flux_col = next((c for c in colnames if c.lower() in ('flux', 'flux_density')), None)
                lam_col = next((c for c in colnames if c.lower() in ('loglam', 'wavelength', 'wave')), None)
                
                if flux_col and lam_col:
                    flux_data = spec_table.data[flux_col]
                    lam_data = spec_table.data[lam_col]
                    if lam_col.lower() == 'loglam':
                        wavelengths = 10 ** lam_data
                    else:
                        wavelengths = lam_data
                        
                    ax.plot(wavelengths, flux_data, color='blue', alpha=0.8)
                    ax.set_title(f"{{GALAXY_NAME}} - Spectrum")
                    ax.set_xlabel("Wavelength (\\\\u212b)")
                    ax.set_ylabel("Flux (10^-17 erg/s/cm^2/\\\\u212b)")
                    ax.grid(True, alpha=0.3)
                    
                    # If redshift is known, mark key emission lines
                    if REDSHIFT is not None and str(REDSHIFT) != "None":
                        # Standard lines
                        lines = [
                            ("H-\\\\u03b1", 6563),
                            ("[OIII]", 5007),
                            ("H-\\\\u03b2", 4861),
                            ("[OII]", 3727)
                        ]
                        for label, rest_w in lines:
                            obs_w = rest_w * (1 + REDSHIFT)
                            if wavelengths.min() < obs_w < wavelengths.max():
                                ax.axvline(obs_w, color='red', linestyle='--', alpha=0.6)
                                ax.text(obs_w, plt.ylim()[1]*0.8, label, rotation=90, color='red', fontsize=8, ha='right')
            else:
                # 1D array in primary HDU fallback
                header = hdul[0].header
                data = hdul[0].data
                if data is not None and len(data.shape) == 1:
                    crval = header.get("CRVAL1", 1.0)
                    cdelt = header.get("CDELT1", 1.0)
                    crpix = header.get("CRPIX1", 1)
                    indices = np.arange(len(data))
                    log_spaced = "log" in header.get("CTYPE1", "").lower()
                    if log_spaced:
                        wavelengths = 10 ** (crval + (indices - crpix) * cdelt)
                    else:
                        wavelengths = crval + (indices - crpix) * cdelt
                    ax.plot(wavelengths, data, color='blue', alpha=0.8)
                    ax.set_title(f"{{GALAXY_NAME}} - Spectrum")
                    ax.set_xlabel("Wavelength")
                    ax.set_ylabel("Flux")
                    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    print("Displaying plots...")
    plt.show()

if __name__ == '__main__':
    main()
'''
    
    with open(output_path, "w") as f:
        f.write(script_content)
    
    # Make executable on Unix systems
    try:
        os.chmod(output_path, 0o755)
    except Exception:
        pass
