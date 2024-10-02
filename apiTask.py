import os
import logging
from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

users_db = {}
tokens_db = {}

ROLES = {
    'admin': ['create_user', 'process_video', 'view_stats'],
    'user': ['process_video'],
    'viewer': ['view_stats']
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users_db.get(data['username'])
            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if required_role not in ROLES.get(current_user['role'], []):
                return jsonify({'message': 'Permission denied!'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

@app.route('/register', methods=['POST'])
@token_required
@role_required('admin')
def register_user(current_user):
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = {
        'username': data['username'],
        'password': hashed_password,
        'role': data['role']
    }
    users_db[data['username']] = new_user
    return jsonify({'message': 'New user created!'})

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    logger.debug(f"Login attempt for user: {auth.username if auth else 'None'}")
    if not auth or not auth.username or not auth.password:
        logger.warning("Login failed: Missing credentials")
        return jsonify({'message': 'Could not verify'}), 401
    user = users_db.get(auth.username)
    if not user:
        logger.warning(f"Login failed: User not found: {auth.username}")
        return jsonify({'message': 'User not found!'}), 401
    if check_password_hash(user['password'], auth.password):
        token = jwt.encode({'username': user['username'], 'exp': datetime.utcnow() + timedelta(minutes=30)},
                           app.config['SECRET_KEY'], algorithm="HS256")
        logger.info(f"Login successful for user: {auth.username}")
        return jsonify({'token': token})
    logger.warning(f"Login failed: Incorrect password for user: {auth.username}")
    return jsonify({'message': 'Could not verify'}), 401


@app.route('/process_video', methods=['POST'])
@token_required
@role_required('process_video')
def process_video(current_user):
    if 'video' not in request.files:
        return jsonify({'message': 'No video file provided'}), 400
    
    video_file = request.files['video']
    temp_path = f"temp_{video_file.filename}"
    video_file.save(temp_path)
    
    cap = cv2.VideoCapture(temp_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    duration = frame_count / fps
    
    if duration > 1000:
        os.remove(temp_path)
        return jsonify({'message': 'Video duration exceeds 1000 seconds limit'}), 400

    processed_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        processed_frames.append(gray_frame)
    
    cap.release()
    os.remove(temp_path)

    
    return jsonify({'message': 'Video processed successfully', 'frame_count': len(processed_frames)})

@app.route('/stats', methods=['GET'])
@token_required
@role_required('view_stats')
def view_stats(current_user):
    stats = {
        'total_users': len(users_db),
        'total_videos_processed': 42,
        'average_processing_time': 5.7
    }
    return jsonify(stats)

if __name__ == '__main__':
    admin_password = generate_password_hash('admin_password', method='sha256')
    users_db['admin'] = {'username': 'admin', 'password': admin_password, 'role': 'admin'}
    logger.info("Admin user created")
    
    app.run(debug=True)