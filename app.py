from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import openai
import base64
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
# Use /tmp for uploads in production (Vercel), local folder for development
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
CORS(app)

# Create upload folder if it doesn't exist (only if not on Vercel or using /tmp)
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except OSError:
    # If we can't create the directory (e.g., on Vercel), use /tmp
    app.config['UPLOAD_FOLDER'] = '/tmp'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

openai.api_key = os.getenv('OPENAI_API_KEY')

# In-memory storage (will be replaced with Firebase)
videos = []
# Store uploaded file data in memory for Vercel
uploaded_files = {}  # filename -> file_data
settings = {
    'channel_name': '',
    'channel_description': '',
    'default_font': 'Mohave',
    'default_template': 'text_over_image',
    'default_colors': {
        'primary': '#DC2626',
        'secondary': '#000000'
    },
    'schedule': {
        'cadence': 'daily',
        'custom_days': [],
        'deadline_time': '18:00',
        'reminder_60': True,
        'reminder_10': True
    },
    'streak': {
        'current': 0,
        'best': 0,
        'last_publish': None
    },
    'reference_faces': []  # List of {name: str, filename: str}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files from the upload folder or memory"""
    # First check if file is in memory (for Vercel)
    if filename in uploaded_files:
        import io
        from flask import send_file
        return send_file(
            io.BytesIO(uploaded_files[filename]['data']),
            mimetype=uploaded_files[filename]['mimetype'],
            as_attachment=False,
            download_name=filename
        )
    # Otherwise try to serve from disk
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/videos', methods=['GET', 'POST'])
def handle_videos():
    if request.method == 'GET':
        return jsonify(videos)
    elif request.method == 'POST':
        video = request.json
        video['id'] = len(videos) + 1
        video['created_at'] = datetime.now().isoformat()
        video['status'] = video.get('status', 'idea')
        videos.append(video)
        return jsonify(video), 201

@app.route('/api/videos/<int:video_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_video(video_id):
    video = next((v for v in videos if v['id'] == video_id), None)
    
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    if request.method == 'GET':
        return jsonify(video)
    elif request.method == 'PUT':
        data = request.json
        video.update(data)
        return jsonify(video)
    elif request.method == 'DELETE':
        videos.remove(video)
        return jsonify({'message': 'Video deleted'}), 200

@app.route('/api/ai/generate-titles', methods=['POST'])
def generate_titles():
    data = request.json
    topic = data.get('topic', '')
    audience = data.get('audience', '')
    key_points = data.get('key_points', [])
    
    if not openai.api_key or openai.api_key == 'your_openai_api_key_here':
        return jsonify({
            'titles': [
                f"How to {topic} - Complete Guide",
                f"{topic} for {audience or 'Beginners'}",
                f"Top Tips for {topic}",
                f"Master {topic} in 2025"
            ]
        })
    
    try:
        client = openai.OpenAI()
        prompt = f"Generate 4 YouTube video titles for a video about {topic} targeted at {audience}. Key points: {', '.join(key_points)}. Make them catchy and clickable."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube title expert. Generate only titles, one per line."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        
        titles = response.choices[0].message.content.strip().split('\n')
        titles = [t.strip() for t in titles if t.strip()][:4]
        
        return jsonify({'titles': titles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/generate-description', methods=['POST'])
def generate_description():
    data = request.json
    title = data.get('title', '')
    topic = data.get('topic', '')
    key_points = data.get('key_points', [])
    
    if not openai.api_key or openai.api_key == 'your_openai_api_key_here':
        return jsonify({
            'description': f"In this video, we explore {topic}.\n\nTopics covered:\n" + 
                          '\n'.join([f"• {point}" for point in key_points]) +
                          "\n\nDon't forget to like and subscribe!"
        })
    
    try:
        client = openai.OpenAI()
        prompt = f"Write a YouTube video description for a video titled '{title}' about {topic}. Include these key points: {', '.join(key_points)}. Make it engaging and SEO-friendly."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube description writer. Create engaging, SEO-friendly descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        description = response.choices[0].message.content.strip()
        return jsonify({'description': description})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/generate-thumbnail-text', methods=['POST'])
def generate_thumbnail_text():
    data = request.json
    title = data.get('title', '')
    
    if not openai.api_key or openai.api_key == 'your_openai_api_key_here':
        return jsonify({
            'suggestions': [
                title[:20] + '...' if len(title) > 20 else title,
                'MUST WATCH',
                'SHOCKING RESULTS',
                'YOU WON\'T BELIEVE'
            ]
        })
    
    try:
        client = openai.OpenAI()
        prompt = f"Generate 4 short, punchy thumbnail text options for a YouTube video titled '{title}'. Each should be 2-4 words maximum."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate short, punchy YouTube thumbnail text. Maximum 2-4 words each. One per line."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.9
        )
        
        suggestions = response.choices[0].message.content.strip().split('\n')
        suggestions = [s.strip() for s in suggestions if s.strip()][:4]
        
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'PUT'])
def handle_settings():
    if request.method == 'GET':
        return jsonify(settings)
    elif request.method == 'PUT':
        settings.update(request.json)
        return jsonify(settings)

@app.route('/api/streak', methods=['GET', 'POST'])
def handle_streak():
    if request.method == 'GET':
        return jsonify(settings['streak'])
    elif request.method == 'POST':
        action = request.json.get('action')
        if action == 'increment':
            settings['streak']['current'] += 1
            if settings['streak']['current'] > settings['streak']['best']:
                settings['streak']['best'] = settings['streak']['current']
            settings['streak']['last_publish'] = datetime.now().isoformat()
        elif action == 'reset':
            settings['streak']['current'] = 0
        return jsonify(settings['streak'])

@app.route('/api/reference-faces', methods=['GET', 'POST', 'DELETE'])
def handle_reference_faces():
    if request.method == 'GET':
        return jsonify(settings['reference_faces'])
    
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        name = request.form.get('name', 'Unknown')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Read file data into memory
            file_data = file.read()
            file.seek(0)  # Reset file pointer
            
            # Store in memory for Vercel
            uploaded_files[filename] = {
                'data': file_data,
                'mimetype': file.mimetype or 'image/jpeg'
            }
            
            # Also try to save to disk if possible (for local development)
            try:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            except:
                pass  # Ignore if we can't save to disk (e.g., on Vercel)
            
            # Add to settings
            settings['reference_faces'].append({
                'name': name,
                'filename': filename,
                'url': f"/uploads/{filename}"  # Changed to use our custom route
            })
            
            return jsonify({'message': 'Face uploaded successfully', 'filename': filename}), 201
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    elif request.method == 'DELETE':
        filename = request.json.get('filename')
        settings['reference_faces'] = [f for f in settings['reference_faces'] if f['filename'] != filename]
        
        # Delete from memory
        if filename in uploaded_files:
            del uploaded_files[filename]
        
        # Try to delete file from disk (if it exists)
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass  # Ignore if we can't delete from disk
        
        return jsonify({'message': 'Face deleted successfully'}), 200

@app.route('/api/ai/generate-thumbnail', methods=['POST'])
def generate_thumbnail():
    data = request.json
    prompt = data.get('prompt', '')
    template = data.get('template', 'text_over_image')
    include_faces = data.get('include_faces', [])
    
    if not openai.api_key or openai.api_key == 'your_openai_api_key_here':
        return jsonify({
            'error': 'OpenAI API key not configured',
            'suggestion': 'Please add your OpenAI API key in settings'
        }), 400
    
    try:
        client = openai.OpenAI()
        
        # Build the prompt including reference faces if selected
        full_prompt = f"YouTube thumbnail: {prompt}"
        if include_faces:
            face_names = [f['name'] for f in settings['reference_faces'] if f['filename'] in include_faces]
            if face_names:
                full_prompt += f". Include these people: {', '.join(face_names)}"
        
        if template == 'text_behind_subject':
            full_prompt += ". Place text behind the main subject."
        elif template == 'text_over_image':
            full_prompt += ". Overlay text on the image."
        
        full_prompt += ". Style: professional, eye-catching, high contrast."
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1792x1024",  # 16:9 aspect ratio
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        return jsonify({'image_url': image_url})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)