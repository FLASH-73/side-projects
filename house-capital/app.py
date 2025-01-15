from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///house_capital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_area = db.Column(db.Float)
    living_area = db.Column(db.Float)
    location = db.Column(db.String(50))
    isolation_type = db.Column(db.String(20))
    window_area = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    house_cost = db.Column(db.Float)
    property_cost = db.Column(db.Float)
    credit_years = db.Column(db.Integer)
    equity = db.Column(db.Float)
    credit_amount = db.Column(db.Float)
    monthly_payment = db.Column(db.Float)
    total_interest = db.Column(db.Float)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Get input values with validation
        try:
            property_area = float(data.get('property_area', 0))
            living_area = float(data.get('living_area', 0))
            window_area = float(data.get('window_area', 0))
            location = data.get('location', '')
            isolation_type = data.get('isolation_type', '')
            include_property = bool(data.get('include_property', True))
            equity = float(data.get('equity', 0))
            credit_years = int(data.get('credit_years', 30))
        except (ValueError, TypeError) as e:
            return jsonify({'error': 'Invalid input data'}), 400

        # Validate required fields
        if not all([living_area, window_area, location, isolation_type]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Location factors (price per square meter)
        location_factors = {
            'München': 9000,
            'Hamburg': 7000,
            'Berlin': 6000,
            'Frankfurt': 8000,
            'Köln': 5500,
            'Stuttgart': 7500,
            'Düsseldorf': 6500,
            'Dresden': 4000,
            'Leipzig': 4200,
            'Hannover': 4800
        }

        # Isolation type factors
        isolation_factors = {
            'basic': 1.0,
            'enhanced': 1.15,
            'premium': 1.3
        }

        # Calculate base house cost
        base_house_cost = living_area * 3000  # Base construction cost per m²
        window_cost = window_area * 800  # Window cost per m²
        
        # Apply isolation factor
        isolation_factor = isolation_factors.get(isolation_type, 1.0)
        house_cost = (base_house_cost + window_cost) * isolation_factor

        # Calculate property cost if included
        property_cost = 0
        if include_property and property_area > 0:
            location_factor = location_factors.get(location, 5000)
            property_cost = property_area * location_factor

        # Calculate total cost
        total_cost = house_cost + property_cost

        # Calculate credit details
        credit_amount = max(0, total_cost - equity)
        
        # Interest rate calculation based on credit years
        base_interest_rate = 0.035  # 3.5% base rate
        if credit_years <= 10:
            interest_rate = base_interest_rate - 0.005
        elif credit_years <= 15:
            interest_rate = base_interest_rate
        elif credit_years <= 20:
            interest_rate = base_interest_rate + 0.005
        else:
            interest_rate = base_interest_rate + 0.01

        # Calculate monthly payment using the PMT formula
        if credit_amount > 0:
            monthly_rate = interest_rate / 12
            num_payments = credit_years * 12
            monthly_payment = (credit_amount * monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            total_interest = (monthly_payment * num_payments) - credit_amount
        else:
            monthly_payment = 0
            total_interest = 0

        # Save calculation to database
        try:
            calculation = Calculation(
                property_area=property_area if include_property else 0,
                living_area=living_area,
                location=location,
                isolation_type=isolation_type,
                window_area=window_area,
                total_cost=total_cost,
                house_cost=house_cost,
                property_cost=property_cost,
                credit_years=credit_years,
                equity=equity,
                credit_amount=credit_amount,
                monthly_payment=monthly_payment,
                total_interest=total_interest
            )
            db.session.add(calculation)
            db.session.commit()
        except Exception as e:
            print(f"Database error: {e}")
            # Continue even if database save fails
            pass

        # Return results
        return jsonify({
            'house_cost': round(house_cost, 2),
            'property_cost': round(property_cost, 2),
            'total_cost': round(total_cost, 2),
            'credit_amount': round(credit_amount, 2),
            'interest_rate': round(interest_rate * 100, 2),
            'monthly_payment': round(monthly_payment, 2),
            'total_interest': round(total_interest, 2)
        })

    except Exception as e:
        print(f"Error in calculation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)
