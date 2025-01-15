document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Get form elements
    const form = document.getElementById('calculationForm');
    const includePropertyCheckbox = document.getElementById('include_property');
    const propertyAreaGroup = document.getElementById('property_area_group');
    const resultCard = document.getElementById('resultCard');

    // Function to format currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('de-DE', { 
            style: 'currency', 
            currency: 'EUR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2 
        }).format(amount);
    }

    // Toggle property area input based on checkbox
    includePropertyCheckbox.addEventListener('change', function() {
        propertyAreaGroup.style.display = this.checked ? 'block' : 'none';
        if (!this.checked) {
            document.getElementById('property_area').value = '';
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset animation classes
        resultCard.classList.remove('animate__animated', 'animate__fadeIn');

        // Get form values
        const formData = {
            property_area: includePropertyCheckbox.checked ? parseFloat(document.getElementById('property_area').value || 0) : 0,
            living_area: parseFloat(document.getElementById('living_area').value || 0),
            window_area: parseFloat(document.getElementById('window_area').value || 0),
            location: document.getElementById('location').value,
            isolation_type: document.getElementById('isolation_type').value,
            include_property: includePropertyCheckbox.checked,
            equity: parseFloat(document.getElementById('equity').value || 0),
            credit_years: parseInt(document.getElementById('credit_years').value || 30)
        };

        // Validate required fields
        if (!formData.living_area || !formData.window_area || !formData.location || !formData.isolation_type) {
            alert('Bitte füllen Sie alle erforderlichen Felder aus.');
            return;
        }

        // Validate property area if included
        if (formData.include_property && !formData.property_area) {
            alert('Bitte geben Sie die Grundstücksfläche ein.');
            return;
        }

        try {
            const response = await fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();

            // Update result fields
            document.getElementById('houseCost').textContent = formatCurrency(result.house_cost);
            document.getElementById('propertyCost').textContent = formatCurrency(result.property_cost);
            document.getElementById('totalCost').textContent = formatCurrency(result.total_cost);
            document.getElementById('creditAmount').textContent = formatCurrency(result.credit_amount);
            document.getElementById('interestRate').textContent = result.interest_rate + '%';
            document.getElementById('monthlyPayment').textContent = formatCurrency(result.monthly_payment);
            document.getElementById('totalInterest').textContent = formatCurrency(result.total_interest);

            // Show result card with animation
            resultCard.style.display = 'block';
            void resultCard.offsetWidth; // Trigger reflow
            resultCard.classList.add('animate__animated', 'animate__fadeIn');

            // Scroll to results
            resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Error:', error);
            alert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        }
    });

    // Add input validation for numerical fields
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
});
