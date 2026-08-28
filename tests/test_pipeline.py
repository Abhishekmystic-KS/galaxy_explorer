import os
import shutil
import pytest
from models import init_job_db, create_job, get_job
from data_sources.pipeline import run_galaxy_pipeline

def test_pipeline_success(mock_fits_image, mock_fits_spectrum, tmp_path, mocker):
    test_db_path = str(tmp_path / "test_jobs.db")
    mocker.patch("models.job.DB_PATH", test_db_path)
    mocker.patch("data_sources.cache.DB_PATH", str(tmp_path / "test_cache.db"))
    
    init_job_db()
    
    # Mock Gaia query
    mocker.patch("data_sources.pipeline.fetch_gaia_astrometry", return_value={
        "parallax": 0.05,
        "parallax_error": 0.001,
        "pmra": -1.2,
        "pmra_error": 0.05,
        "pmdec": 2.4,
        "pmdec_error": 0.04,
        "phot_g_mean_mag": 12.3
    })
    
    # Mock download_galaxy_fits to copy our mock FITS fixtures
    def mock_download(ra, dec, output_dir, prefix):
        img_dest = os.path.join(output_dir, f"{prefix}_image.fits")
        spec_dest = os.path.join(output_dir, f"{prefix}_spec.fits")
        shutil.copy(mock_fits_image, img_dest)
        shutil.copy(mock_fits_spectrum, spec_dest)
        return img_dest, spec_dest
        
    mocker.patch("data_sources.pipeline.download_galaxy_fits", side_effect=mock_download)
    
    # Create a job
    job = create_job("M51", "127.0.0.1")
    job_id = job["job_id"]
    
    assert job["status"] == "pending"
    assert job["progress"] == 0
    
    # Run the pipeline
    run_galaxy_pipeline(job_id, "M51")
    
    # Fetch job from database to verify results
    updated_job = get_job(job_id)
    
    assert updated_job["status"] == "completed"
    assert updated_job["progress"] == 100
    assert updated_job["error_message"] is None
    
    # Verify outputs exist
    output_dir = os.path.join("output", job_id)
    assert os.path.exists(output_dir)
    assert os.path.exists(os.path.join(output_dir, f"{job_id}_cutout.png"))
    assert os.path.exists(os.path.join(output_dir, "spectrum.json"))
    assert os.path.exists(os.path.join(output_dir, f"{job_id}_reproduce.py"))
    assert os.path.exists(os.path.join(output_dir, f"{job_id}_report.html"))
    
    # Clean up output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
