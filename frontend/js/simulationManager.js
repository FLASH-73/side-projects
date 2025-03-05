export class SimulationManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
    }

    async uploadMeshFile(file) {
        if (!file) return null;

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('Uploading mesh file:', file.name);
            const response = await fetch(`${this.apiBaseUrl}/upload-mesh`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Upload failed:', errorText);
                throw new Error(`Upload failed: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('Upload successful:', data);
            return data.filename;
        } catch (error) {
            console.error('Error uploading mesh file:', error);
            throw new Error(`File upload failed: ${error.message}`);
        }
    }

    async startSimulation(simulationType, parameters, meshFile = null) {
        try {
            console.log('Starting simulation with:', { simulationType, parameters, meshFile });
            let meshFilePath = null;
            
            if (meshFile) {
                console.log('Uploading mesh file before simulation');
                meshFilePath = await this.uploadMeshFile(meshFile);
            }

            const requestBody = {
                simulation_type: simulationType,
                parameters: parameters,
                mesh_file: meshFilePath
            };
            
            console.log('Sending simulation request:', requestBody);
            
            const response = await fetch(`${this.apiBaseUrl}/simulations/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Simulation request failed:', errorText);
                throw new Error(`Simulation failed: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('Simulation started successfully:', data);
            return data;
        } catch (error) {
            console.error('Error starting simulation:', error);
            throw new Error(`Failed to start simulation: ${error.message}`);
        }
    }

    async getSimulationStatus(jobId) {
        try {
            console.log('Checking simulation status for job:', jobId);
            const response = await fetch(`${this.apiBaseUrl}/simulations/${jobId}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Status check failed:', errorText);
                throw new Error(`Status check failed: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('Received simulation status:', data);
            return data;
        } catch (error) {
            console.error('Error getting simulation status:', error);
            throw new Error(`Failed to get simulation status: ${error.message}`);
        }
    }
}
