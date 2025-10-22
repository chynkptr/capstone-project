from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
import pickle
import numpy as np
from PIL import Image
import io
import base64
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'capstone1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin123@localhost:5432/capstone'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db = SQLAlchemy(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load ML models
models = {}
try:
    with open('model1.pkl', 'rb') as f:
        models['mole'] = pickle.load(f)
    with open('model2.pkl', 'rb') as f:
        models['eye'] = pickle.load(f)
    with open('model3.pkl', 'rb') as f:
        models['period'] = pickle.load(f)
    print("All models loaded successfully")
except Exception as e:
    print(f"Error loading models: {e}")

# User model
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default='user')
    dob = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'dob': self.dob.isoformat(),
            'created_at': self.created_at.isoformat()
        }

# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'Token is invalid!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Helper functions for image processing
def preprocess_image(image_data, target_size=(224, 224)):
    """
    Preprocess image for model prediction
    """
    try:
        # If image_data is base64 string, decode it
        if isinstance(image_data, str):
            image_data = base64.b64decode(image_data)
        
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image
        image = image.resize(target_size)
        
        # Convert to numpy array and normalize
        image_array = np.array(image) / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

# Routes

@app.route('/')
def home():
    return jsonify({
        'message': 'Capstone Medical Prediction API',
        'version': '1.0.0',
        'endpoints': {
            'auth': ['/signup', '/login', '/reset-password'],
            'predictions': ['/mole/predict', '/eye/predict', '/period/predict']
        }
    })

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'dob']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Parse date
        try:
            dob = datetime.strptime(data['dob'], '%d-%m-%Y').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use DD-MM-YYYY'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            user_type=data.get('user_type', 'user'),
            dob=dob
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'user_type': user.user_type,
                'exp': datetime.utcnow() + timedelta(days=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        required_fields = ['username', 'old_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.check_password(data['old_password']):
            return jsonify({'error': 'Invalid old password'}), 401
        
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/mole/predict', methods=['POST'])
@token_required
def predict_mole(current_user):
    try:
        if 'mole' not in models:
            return jsonify({'error': 'Mole classification model not available'}), 503
        
        # Get image data
        if 'image' not in request.files and 'image_data' not in request.json:
            return jsonify({'error': 'No image provided'}), 400
        
        if 'image' in request.files:
            # Handle file upload
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            image_data = file.read()
        else:
            # Handle base64 image data
            image_data = request.json['image_data']
        
        # Preprocess image
        processed_image = preprocess_image(image_data)
        
        # Make prediction
        prediction = models['mole'].predict(processed_image)
        prediction_proba = models['mole'].predict_proba(processed_image)
        
        # Get class labels (adjust based on your model)
        classes = ['Benign', 'Malignant']  # Update with your actual classes
        
        result = {
            'prediction': classes[int(prediction[0])],
            'confidence': float(max(prediction_proba[0])),
            'probabilities': {
                classes[i]: float(prediction_proba[0][i]) 
                for i in range(len(classes))
            },
            'user_id': current_user.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/eye/predict', methods=['POST'])
@token_required
def predict_eye(current_user):
    try:
        if 'eye' not in models:
            return jsonify({'error': 'Eye disease classification model not available'}), 503
        
        # Get image data
        if 'image' not in request.files and 'image_data' not in request.json:
            return jsonify({'error': 'No image provided'}), 400
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            image_data = file.read()
        else:
            image_data = request.json['image_data']
        
        # Preprocess image
        processed_image = preprocess_image(image_data)
        
        # Make prediction
        prediction = models['eye'].predict(processed_image)
        prediction_proba = models['eye'].predict_proba(processed_image)
        
        # Get class labels (adjust based on your model)
        classes = ['Normal', 'Cataract', 'Glaucoma', 'Diabetic Retinopathy']  # Update with your actual classes
        
        result = {
            'prediction': classes[int(prediction[0])],
            'confidence': float(max(prediction_proba[0])),
            'probabilities': {
                classes[i]: float(prediction_proba[0][i]) 
                for i in range(len(classes))
            },
            'user_id': current_user.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/period/predict', methods=['POST'])
@token_required
def predict_period(current_user):
    try:
        if 'period' not in models:
            return jsonify({'error': 'Period tracker model not available'}), 503
        
        data = request.get_json()
        
        # Validate required fields for period prediction
        required_fields = ['cycle_length', 'period_length', 'age']  # Adjust based on your model
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Prepare input data for the model
        input_data = np.array([[
            data['cycle_length'],
            data['period_length'],
            data['age'],
            # Add other features as required by your model
        ]])
        
        # Make prediction
        prediction = models['period'].predict(input_data)
        
        # Format result based on your model output
        result = {
            'next_period_date': prediction[0],  # Adjust based on your model output
            'cycle_regularity': 'Regular',  # Add logic based on your model
            'user_id': current_user.id,
            'timestamp': datetime.utcnow().isoformat(),
            'input_data': data
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Database initialization
def init_db():
    """Initialize database and create default admin user"""
    try:
        db.create_all()
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                user_type='admin',
                dob=datetime.strptime('01-01-2025', '%d-%m-%Y').date()
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created")
        else:
            print("Admin user already exists")
            
    except Exception as e:
        print(f"Error initializing database: {e}")

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db else 'disconnected',
        'models_loaded': list(models.keys()),
        'timestamp': datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    print("Starting Flask app on port 8000")
    app.run(debug=True, host='0.0.0.0', port=8000)