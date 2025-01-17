from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import numpy as np
import uuid
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Physics Simulation Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store simulations in memory (for demo purposes)
simulations = {}
UPLOAD_DIR = "uploads"

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SimulationRequest(BaseModel):
    simulation_type: str
    parameters: Dict[str, Any]
    mesh_file: Optional[str] = None

def run_mock_simulation(sim_type: str, parameters: Dict[str, Any], mesh_file: Optional[str] = None):
    """Mock simulation function for demonstration"""
    logger.debug(f"Running mock simulation with type: {sim_type}, parameters: {parameters}, mesh_file: {mesh_file}")
    
    if sim_type == "fluid_dynamics":
        return {
            "type": "fluid_dynamics",
            "particles": [
                {"x": float(np.random.random()), "y": float(np.random.random()), "z": float(np.random.random())}
                for _ in range(100)
            ]
        }
    elif sim_type == "electromagnetic":
        return {
            "type": "electromagnetic",
            "fieldLines": [
                {"x": float(np.random.random()), "y": float(np.random.random()), "z": float(np.random.random())}
                for _ in range(50)
            ]
        }
    else:  # stress_analysis
        return {
            "type": "stress_analysis",
            "stressValues": [float(np.random.random()) for _ in range(100)],
            "maxStress": 1.0,
            "meshFile": mesh_file
        }

@app.get("/")
async def root():
    return {"message": "Physics Simulation Platform API"}

@app.post("/api/upload-mesh")
async def upload_mesh(file: UploadFile = File(...)):
    try:
        logger.debug(f"Receiving upload request for file: {file.filename}")
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.debug(f"File saved successfully at: {file_path}")
        return {"filename": file_path}
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/simulations/")
async def create_simulation(simulation: SimulationRequest):
    try:
        logger.debug(f"Received simulation request: {simulation}")
        job_id = str(uuid.uuid4())
        simulations[job_id] = {
            "status": "running",
            "start_time": time.time(),
            "type": simulation.simulation_type,
            "parameters": simulation.parameters,
            "mesh_file": simulation.mesh_file
        }
        
        logger.debug(f"Created simulation job with ID: {job_id}")
        
        # Run mock simulation
        results = run_mock_simulation(
            simulation.simulation_type, 
            simulation.parameters,
            simulation.mesh_file
        )
        
        simulations[job_id]["results"] = results
        simulations[job_id]["status"] = "completed"
        
        logger.debug(f"Simulation completed for job ID: {job_id}")
        return {"job_id": job_id, "status": "completed"}
    except Exception as e:
        logger.error(f"Error during simulation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/simulations/{job_id}")
async def get_simulation_status(job_id: str):
    logger.debug(f"Checking status for job ID: {job_id}")
    
    if job_id not in simulations:
        logger.error(f"Job ID not found: {job_id}")
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations[job_id]
    logger.debug(f"Returning simulation results for job ID: {job_id}")
    
    return {
        "status": sim["status"],
        "results": sim.get("results", None),
        "progress": 1.0 if sim["status"] == "completed" else 0.5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
