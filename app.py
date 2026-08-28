import os
import uvicorn
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import init_job_db, create_job, get_job, get_recent_jobs, check_rate_limit
from data_sources.pipeline import run_galaxy_pipeline

# Initialize database
init_job_db()

# Create output and static directories if they don't exist yet to avoid mounting crashes
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Galaxy Intelligence Platform", version="1.0.0")

# Mount static and output folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Rate limiting dependency (5 jobs per minute per IP)
def rate_limit_check(request: Request):
    # Get client IP address
    client_ip = request.client.host if request.client else "127.0.0.1"
    # Allow 5 submissions per minute (60 seconds)
    if not check_rate_limit(client_ip, limit=5, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Maximum 5 job submissions per minute per IP.")
    return client_ip

@app.get("/")
def read_root(request: Request, rate_limited: bool = False):
    """Dashboard homepage - shows search box and recent jobs."""
    jobs = get_recent_jobs(limit=10)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"jobs": jobs, "rate_limited": rate_limited}
    )

@app.post("/job")
def submit_job(
    request: Request,
    background_tasks: BackgroundTasks,
    query: str = Form(...),
):
    """Submits a new galaxy query and runs the background processing pipeline."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Check rate limit manually to redirect gracefully rather than returning 429 page
    if not check_rate_limit(client_ip, limit=5, window_seconds=60):
        return RedirectResponse(url="/?rate_limited=true", status_code=303)
        
    if not query.strip():
        return RedirectResponse(url="/", status_code=303)
        
    # Create the job in the database
    job = create_job(query.strip(), client_ip)
    job_id = job["job_id"]
    
    # Add pipeline execution to background tasks
    background_tasks.add_task(run_galaxy_pipeline, job_id, query.strip())
    
    # Redirect to the status/polling page
    return RedirectResponse(url=f"/job/{job_id}", status_code=303)

@app.get("/job/{job_id}")
def read_job(request: Request, job_id: str):
    """Displays job progress polling screen or the final profile page if finished."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job["status"] == "completed":
        # Load result
        return templates.TemplateResponse(request=request, name="result.html", context={"job": job})
    else:
        # Polling progress page (also handles failed job messages)
        return templates.TemplateResponse(request=request, name="status.html", context={"job": job})

@app.get("/api/status/{job_id}")
def get_job_status(job_id: str):
    """API endpoint for frontend status polling."""
    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
        
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "step_message": job["step_message"],
        "error_message": job["error_message"]
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
