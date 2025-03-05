# Physics Simulation Platform

A cloud-based platform for running advanced physics simulations using high-performance computing (HPC) and AI. The platform supports various types of physics simulations including fluid dynamics, electromagnetic simulations, and stress analysis.

## Features

- Multiple simulation types supported:
  - Fluid Dynamics
  - Electromagnetic Simulations
  - Stress Analysis
- Real-time 3D visualization of simulation results
- AI-enhanced simulation processing
- Cloud-based computation for heavy workloads
- Intuitive web-based interface
- RESTful API for integration with other tools

## Prerequisites

- Python 3.9+
- Node.js 14+
- Redis server
- MongoDB

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd physics-sim-platform
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the Redis server:
```bash
redis-server
```

4. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

5. Start the Celery worker:
```bash
celery -A worker worker --loglevel=info
```

6. Open the frontend:
```bash
cd frontend
python -m http.server 8080
```

Visit `http://localhost:8080` in your web browser to access the platform.

## Usage

1. Select the type of simulation you want to run (Fluid Dynamics, Electromagnetic, or Stress Analysis)
2. Configure the simulation parameters
3. Optionally upload a mesh file for custom geometry
4. Click "Run Simulation" to start the computation
5. View the results in real-time through the 3D visualization interface

## API Documentation

The platform provides a RESTful API for programmatic access:

- `POST /api/simulations/`: Start a new simulation
- `GET /api/simulations/{job_id}`: Get simulation status and results
- `POST /api/upload-mesh`: Upload custom mesh files

For detailed API documentation, visit `http://localhost:8000/docs` when the server is running.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
