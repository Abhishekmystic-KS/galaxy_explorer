import os
import traceback
from models import update_job
from crossmatch_client import crossmatch_by_name
from data_sources.gaia_client import fetch_gaia_astrometry
from archive_client import download_galaxy_fits
from fits_analyzer import analyze_fits_image, analyze_fits_spectrum
from report_generator import generate_report
from script_generator import generate_script

def run_galaxy_pipeline(job_id: str, query: str):
    """
    Executes the full pipeline for a job.
    Updates the database with progress and results.
    """
    output_dir = os.path.join("output", job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Resolve and Cross-match
        update_job(job_id, status="running", progress=15, step_message="Resolving target and cross-matching databases (SIMBAD/NED)...")
        profile = crossmatch_by_name(query)
        
        # Step 2: Query Gaia astrometry
        update_job(job_id, status="running", progress=35, step_message="Fetching astrometric data from Gaia DR3...")
        gaia_data = fetch_gaia_astrometry(profile["ra"], profile["dec"])
        profile.update(gaia_data)
        
        # Step 3: Fetch FITS files
        update_job(job_id, status="running", progress=55, step_message="Downloading FITS images and spectra from SDSS/DESI...")
        image_fits_path, spec_fits_path = download_galaxy_fits(profile["ra"], profile["dec"], output_dir, prefix=job_id)
        
        # Step 4: Parse FITS images & generate cutout
        update_job(job_id, status="running", progress=75, step_message="Analyzing image FITS and generating high-contrast PNG cutout...")
        cutout_png_path = os.path.join(output_dir, f"{job_id}_cutout.png")
        image_props = analyze_fits_image(image_fits_path, cutout_png_path)
        profile.update(image_props)
        
        # Step 5: Parse FITS spectrum (if available)
        update_job(job_id, status="running", progress=85, step_message="Analyzing spectrum FITS...")
        try:
            spec_props = analyze_fits_spectrum(spec_fits_path)
            profile["classification"] = spec_props.get("classification", "Unknown")
            # Store spectrum data paths/samples in profile rather than full array if too large
            profile["spectrum_points"] = len(spec_props["wavelengths"])
            # Save raw spectrum arrays to a text file or JSON in output directory for chart loading
            # We'll save a lightweight JSON for Chart.js rendering
            import json
            spec_data_path = os.path.join(output_dir, "spectrum.json")
            with open(spec_data_path, "w") as f:
                json.dump({
                    "wavelengths": spec_props["wavelengths"],
                    "flux": spec_props["flux"],
                    "ivar": spec_props["ivar"]
                }, f)
            profile["has_spectrum"] = True
        except Exception as e:
            print(f"Failed to process spectrum: {e}")
            profile["has_spectrum"] = False
            profile["spectrum_points"] = 0
            
        # Step 6: Generate reproducing script & HTML report
        update_job(job_id, status="running", progress=95, step_message="Compiling downloadable report and offline reproduction scripts...")
        
        # Paths for generated outputs
        script_path = os.path.join(output_dir, f"{job_id}_reproduce.py")
        report_path = os.path.join(output_dir, f"{job_id}_report.html")
        
        generate_script(profile, image_fits_path, spec_fits_path if profile["has_spectrum"] else None, script_path)
        generate_report(profile, cutout_png_path, report_path)
        
        # Save relative paths in result data for easy access from UI
        profile["cutout_url"] = f"/output/{job_id}/{job_id}_cutout.png"
        profile["script_url"] = f"/output/{job_id}/{job_id}_reproduce.py"
        profile["report_url"] = f"/output/{job_id}/{job_id}_report.html"
        profile["fits_image_url"] = f"/output/{job_id}/{job_id}_image.fits"
        
        # Complete
        update_job(job_id, status="completed", progress=100, step_message="Analysis completed successfully!", result_data=profile)
        
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        update_job(job_id, status="failed", progress=100, step_message="Failed", error_message=error_msg)
