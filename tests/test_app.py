import pytest
from fastapi.testclient import TestClient
from app import app
from models import init_job_db, create_job, get_job, update_job

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, mocker):
    # Set up temporary databases for testing app.py routes
    test_db = str(tmp_path / "test_app_jobs.db")
    mocker.patch("models.job.DB_PATH", test_db)
    mocker.patch("data_sources.cache.DB_PATH", str(tmp_path / "test_app_cache.db"))
    init_job_db()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Galaxy Intelligence Platform" in response.text


def test_submit_job_and_poll(mocker):
    # Mock background pipeline task to prevent real execution
    mock_run = mocker.patch("app.run_galaxy_pipeline")
    
    response = client.post("/job", data={"query": "M51"}, follow_redirects=False)
    assert response.status_code == 303
    
    location = response.headers["location"]
    assert location.startswith("/job/")
    
    job_id = location.split("/")[-1]
    
    # Check status endpoint
    status_response = client.get(f"/api/status/{job_id}")
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "pending"
    assert data["progress"] == 0
    
    # Verify background task was scheduled
    mock_run.assert_called_once_with(job_id, "M51")


def test_job_completed_render(mocker):
    # Create and update a job to completed state
    job = create_job("M31", "127.0.0.1")
    job_id = job["job_id"]
    
    update_job(
        job_id,
        status="completed",
        progress=100,
        step_message="Done",
        result_data={
            "name": "M 31",
            "ra": 10.684,
            "dec": 41.268,
            "type": "Spiral Galaxy",
            "aliases": ["M31", "Andromeda"],
            "redshift": -0.001,
            "redshift_err": 0.0,
            "mag": 3.44,
            "phot_error": 0.02,
            "image_quality": "Nominal",
            "filter": "r",
            "instrument": "SDSS",
            "telescope": "SDSS",
            "source": "SIMBAD",
            "parallax": 0.0,
            "parallax_error": 0.0,
            "pmra": 0.0,
            "pmra_error": 0.0,
            "pmdec": 0.0,
            "pmdec_error": 0.0,
            "phot_g_mean_mag": 0.0,
            "has_spectrum": False,
            "spectrum_points": 0
        }
    )
    
    response = client.get(f"/job/{job_id}")
    assert response.status_code == 200
    assert "M 31" in response.text
    assert "Andromeda" in response.text
    assert "Gaia DR3 Astrometry" in response.text


def test_rate_limiting(mocker):
    mocker.patch("app.run_galaxy_pipeline")
    
    # Submit 5 jobs (allowed)
    for _ in range(5):
        response = client.post("/job", data={"query": "M31"}, follow_redirects=False)
        assert response.status_code == 303
        
    # The 6th submission should be rate-limited and redirected to root with rate_limited query parameter
    response = client.post("/job", data={"query": "M31"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/?rate_limited=true"
