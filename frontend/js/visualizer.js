export class Visualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.setupScene();
        this.animate();
        window.addEventListener('resize', () => this.onWindowResize());
    }

    setupScene() {
        // Set up Three.js scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // Set up camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 0, 5);

        // Set up renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        // Add lights
        const ambientLight = new THREE.AmbientLight(0x404040);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(ambientLight);
        this.scene.add(directionalLight);

        // Add orbit controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // Initialize mesh
        this.mesh = null;
        this.stlLoader = new THREE.STLLoader();
    }

    updateVisualization(results) {
        console.log('Updating visualization with results:', results);

        // Remove existing mesh if any
        if (this.mesh) {
            this.scene.remove(this.mesh);
            if (this.mesh.geometry) this.mesh.geometry.dispose();
            if (this.mesh.material) this.mesh.material.dispose();
        }

        if (results.type === 'stress_analysis') {
            this.visualizeStressAnalysis(results);
        } else if (results.type === 'fluid_dynamics') {
            this.visualizeFluidDynamics(results);
        } else if (results.type === 'electromagnetic') {
            this.visualizeElectromagnetic(results);
        }
    }

    visualizeStressAnalysis(results) {
        console.log('Visualizing stress analysis:', results);
        
        // Create default cube geometry
        const geometry = new THREE.BoxGeometry(2, 2, 2);
        
        // Create vertex colors array
        const colors = new Float32Array(geometry.attributes.position.count * 3);
        const stressValues = results.stressValues;
        const maxStress = results.maxStress || Math.max(...stressValues);
        
        // Normalize stress values and create colors
        for (let i = 0; i < geometry.attributes.position.count; i++) {
            const stressValue = stressValues[i % stressValues.length] / maxStress;
            const color = new THREE.Color();
            // Use a color gradient from blue (low stress) to red (high stress)
            color.setHSL(0.6 * (1 - stressValue), 1, 0.5);
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }
        
        // Add colors to geometry
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        // Create material
        const material = new THREE.MeshPhongMaterial({
            vertexColors: true,
            side: THREE.DoubleSide,
            shininess: 50
        });
        
        // Create mesh
        this.mesh = new THREE.Mesh(geometry, material);
        
        // Add wireframe
        const wireframe = new THREE.WireframeGeometry(geometry);
        const line = new THREE.LineSegments(
            wireframe,
            new THREE.LineBasicMaterial({ color: 0x000000, linewidth: 1 })
        );
        this.mesh.add(line);
        
        // Center and add to scene
        this.scene.add(this.mesh);
        
        // Reset camera position
        this.camera.position.set(0, 0, 5);
        this.controls.reset();
    }

    visualizeFluidDynamics(results) {
        const geometry = new THREE.BufferGeometry();
        const vertices = new Float32Array(results.particles.length * 3);
        
        results.particles.forEach((particle, i) => {
            vertices[i * 3] = (particle.x - 0.5) * 4;
            vertices[i * 3 + 1] = (particle.y - 0.5) * 4;
            vertices[i * 3 + 2] = (particle.z - 0.5) * 4;
        });
        
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        const material = new THREE.PointsMaterial({
            color: 0x0088ff,
            size: 0.1,
            transparent: true,
            opacity: 0.6
        });
        
        this.mesh = new THREE.Points(geometry, material);
        this.scene.add(this.mesh);
    }

    visualizeElectromagnetic(results) {
        const geometry = new THREE.BufferGeometry();
        const vertices = new Float32Array(results.fieldLines.length * 3);
        
        results.fieldLines.forEach((point, i) => {
            vertices[i * 3] = (point.x - 0.5) * 4;
            vertices[i * 3 + 1] = (point.y - 0.5) * 4;
            vertices[i * 3 + 2] = (point.z - 0.5) * 4;
        });
        
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        const material = new THREE.LineBasicMaterial({
            color: 0xff0000,
            linewidth: 2
        });
        
        this.mesh = new THREE.Line(geometry, material);
        this.scene.add(this.mesh);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.mesh) {
            // Gentle rotation
            this.mesh.rotation.y += 0.002;
        }
        
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
}
