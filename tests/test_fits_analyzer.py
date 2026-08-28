import os
import pytest
from PIL import Image
from fits_analyzer import analyze_fits_image, analyze_fits_spectrum

def test_analyze_fits_image(mock_fits_image, tmp_path):
    output_png = tmp_path / "cutout.png"
    properties = analyze_fits_image(mock_fits_image, str(output_png))
    
    assert properties["type"] == "image"
    assert properties["ra"] == pytest.approx(185.728)
    assert properties["dec"] == pytest.approx(15.823)
    assert properties["filter"] == "r"
    assert properties["exptime"] == pytest.approx(53.9)
    assert properties["instrument"] == "MOCK_CAM"
    assert properties["telescope"] == "MOCK_TEL"
    assert properties["phot_error"] == pytest.approx(0.03)
    assert properties["image_quality"] == 'Seeing: 1.2"'
    
    # Check that png is created and has correct dimensions
    assert os.path.exists(output_png)
    with Image.open(output_png) as img:
        assert img.size == (100, 100)

def test_analyze_fits_spectrum(mock_fits_spectrum):
    properties = analyze_fits_spectrum(mock_fits_spectrum)
    
    assert properties["type"] == "spectrum"
    assert properties["redshift"] == pytest.approx(0.045)
    assert properties["redshift_err"] == pytest.approx(0.00008)
    assert properties["classification"] == "GALAXY"
    
    assert len(properties["wavelengths"]) == 100
    assert len(properties["flux"]) == 100
    assert len(properties["ivar"]) == 100
    # Wavelength should be scaled back from loglam (10^3.5 ~= 3162, 10^4.0 ~= 10000)
    assert properties["wavelengths"][0] == pytest.approx(3500.0)
    assert properties["wavelengths"][-1] == pytest.approx(9000.0)
