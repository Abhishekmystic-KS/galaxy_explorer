import os
import pytest
from unittest.mock import MagicMock
from data_sources.sdss_client import fetch_sdss_image_fits, fetch_sdss_spectrum_fits
from data_sources.gaia_client import fetch_gaia_astrometry

def test_fetch_sdss_image_fits_fallback(tmp_path, mocker):
    # Mock requests.get to fail to trigger fallback
    mocker.patch("requests.get", side_effect=Exception("Connection error"))
    mocker.patch("astroquery.sdss.SDSS.query_region", side_effect=Exception("SDSS offline"))
    
    output_fits = tmp_path / "test_image.fits"
    path = fetch_sdss_image_fits(185.728, 15.823, str(output_fits))
    
    assert os.path.exists(path)
    assert path == str(output_fits)


def test_fetch_sdss_spectrum_fits_fallback(tmp_path, mocker):
    mocker.patch("astroquery.sdss.SDSS.query_specobj", side_effect=Exception("SDSS offline"))
    
    output_fits = tmp_path / "test_spec.fits"
    path = fetch_sdss_spectrum_fits(185.728, 15.823, str(output_fits))
    
    assert os.path.exists(path)
    assert path == str(output_fits)


def test_fetch_gaia_astrometry_fallback(mocker):
    mocker.patch("astroquery.gaia.Gaia.cone_search_async", side_effect=Exception("Gaia offline"))
    
    data = fetch_gaia_astrometry(185.728, 15.823)
    
    assert isinstance(data, dict)
    assert "parallax" in data
    assert data["parallax"] is None
