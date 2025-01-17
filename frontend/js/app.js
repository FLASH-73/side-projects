import { SimulationManager } from './simulationManager.js';
import { Visualizer } from './visualizer.js';

class App {
    constructor() {
        this.visualizer = new Visualizer('visualizationArea');
        this.simulationManager = new SimulationManager();
        this.setupEventListeners();
        this.setupSimulationTypes();
        this.updateParameterFields(); // Initialize with default simulation type
    }

    setupEventListeners() {
        const form = document.getElementById('simulationForm');
        const simTypeSelect = document.getElementById('simulationType');

        form.addEventListener('submit', (e) => this.handleSimulationSubmit(e));
        simTypeSelect.addEventListener('change', () => this.updateParameterFields());
    }

    setupSimulationTypes() {
        this.simulationParameters = {
            fluid_dynamics: [
                { name: 'reynolds_number', label: 'Reynolds Number', type: 'number', default: 1000 },
                { name: 'viscosity', label: 'Viscosity (m²/s)', type: 'number', default: 1.0 },
                { name: 'density', label: 'Density (kg/m³)', type: 'number', default: 1.0 }
            ],
            electromagnetic: [
                { name: 'frequency', label: 'Frequency (Hz)', type: 'number', default: 60 },
                { name: 'voltage', label: 'Voltage (V)', type: 'number', default: 220 },
                { name: 'current', label: 'Current (A)', type: 'number', default: 10 }
            ],
            stress_analysis: [
                { name: 'youngs_modulus', label: 'Young\'s Modulus (GPa)', type: 'number', default: 200 },
                { name: 'poisson_ratio', label: 'Poisson\'s Ratio', type: 'number', default: 0.3 },
                { name: 'load', label: 'Applied Load (N)', type: 'number', default: 1000 }
            ]
        };
    }

    updateParameterFields() {
        const simType = document.getElementById('simulationType').value;
        const container = document.getElementById('parametersContainer');
        container.innerHTML = '';

        this.simulationParameters[simType].forEach(param => {
            const div = document.createElement('div');
            div.className = 'parameter-input';
            div.innerHTML = `
                <label class="block text-sm font-medium text-gray-700">${param.label}</label>
                <input type="${param.type}" 
                       name="${param.name}"
                       value="${param.default}"
                       class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            `;
            container.appendChild(div);
        });
    }

    async handleSimulationSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const simulationType = formData.get('simulationType');
        const parameters = {};
        const meshFile = document.getElementById('meshFile').files[0];
        
        // Collect parameters
        this.simulationParameters[simulationType].forEach(param => {
            parameters[param.name] = Number(formData.get(param.name));
        });

        try {
            this.updateStatus('Starting simulation...', 'info');
            console.log('Form data:', { simulationType, parameters, meshFile });
            
            if (simulationType === 'stress_analysis' && !meshFile) {
                throw new Error('Please select a mesh file for stress analysis');
            }
            
            // Start simulation with mesh file
            const response = await this.simulationManager.startSimulation(
                simulationType,
                parameters,
                meshFile
            );
            
            console.log('Simulation response:', response);
            
            if (response.status === 'completed' && response.job_id) {
                // Get results immediately since our mock backend completes simulations instantly
                const result = await this.simulationManager.getSimulationStatus(response.job_id);
                console.log('Simulation results:', result);
                
                if (result.results) {
                    this.visualizer.updateVisualization(result.results);
                    this.updateStatus('Simulation completed successfully', 'success');
                } else {
                    this.updateStatus('Simulation completed but no results were returned', 'error');
                }
            } else {
                console.error('Invalid simulation response:', response);
                this.updateStatus('Failed to start simulation: Invalid response from server', 'error');
            }
        } catch (error) {
            console.error('Simulation error:', error);
            this.updateStatus(`Error: ${error.message}`, 'error');
        }
    }

    updateStatus(message, type = 'info') {
        const resultsPanel = document.getElementById('resultsPanel');
        const bgColor = {
            'error': 'bg-red-100 text-red-700',
            'success': 'bg-green-100 text-green-700',
            'info': 'bg-blue-100 text-blue-700'
        }[type];

        resultsPanel.innerHTML = `
            <div class="p-4 rounded ${bgColor}">
                ${message}
            </div>
        `;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
