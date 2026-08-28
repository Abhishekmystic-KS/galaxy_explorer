import os
import pytest
import numpy as np
from astropy.io import fits

@pytest.fixture
def mock_fits_image(tmp_path):
    """Generates a temporary valid FITS image file."""
    filepath = tmp_path / "mock_image.fits"
    
    # Generate 100x100 synthetic galaxy image
    y, x = np.ogrid[-50:50, -50:50]
    # Simple Gaussian profile for a galaxy
    data = 100.0 * np.exp(-(x**2 + y**2) / 100.0) + np.random.normal(0, 2.0, (100, 100))
    
    hdu = fits.PrimaryHDU(data)
    hdu.header['CRVAL1'] = 185.728
    hdu.header['CRVAL2'] = 15.823
    hdu.header['FILTER'] = 'r'
    hdu.header['EXPTIME'] = 53.9
    hdu.header['INSTRUME'] = 'MOCK_CAM'
    hdu.header['TELESCOP'] = 'MOCK_TEL'
    hdu.header['SKYERR'] = 0.03
    hdu.header['SEEING'] = 1.2
    
    hdu.writeto(filepath, overwrite=True)
    return str(filepath)

@pytest.fixture
def mock_fits_spectrum(tmp_path):
    """Generates a temporary valid FITS binary table spectrum file."""
    filepath = tmp_path / "mock_spec.fits"
    
    # Wavelength in log space (approx 3100 to 10000 Angstroms)
    loglam = np.linspace(np.log10(3500), np.log10(9000), 100)
    flux = 10.0 + 5.0 * np.sin(loglam * 20.0) + np.random.normal(0, 0.5, 100)
    ivar = 1.0 / (0.5**2) * np.ones(100)
    
    col1 = fits.Column(name='flux', format='E', array=flux)
    col2 = fits.Column(name='loglam', format='E', array=loglam)
    col3 = fits.Column(name='ivar', format='E', array=ivar)
    
    tbhdu = fits.BinTableHDU.from_columns([col1, col2, col3])
    
    prihdu = fits.PrimaryHDU()
    prihdu.header['Z'] = 0.045
    prihdu.header['Z_ERR'] = 0.00008
    prihdu.header['CLASS'] = 'GALAXY'
    
    hdul = fits.HDUList([prihdu, tbhdu])
    hdul.writeto(filepath, overwrite=True)
    return str(filepath)
