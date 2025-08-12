import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
import requests

load_dotenv()

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate('brodeo-yt-firebase-adminsdk-fbsvc-cb6d523df0.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Routes for pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/backlog')
def backlog():
    return render_template('backlog.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# API Routes
@app.route('/api/ideas', methods=['GET', 'POST'])
def manage_ideas():
    if request.method == 'POST':
        data = request.json
        idea = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'tags': data.get('tags', []),
            'priority': data.get('priority', 'medium'),
            'status': data.get('status', 'Idea'),
            'assets': data.get('assets', {}),
            'schedule_date': data.get('schedule_date'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection('ideas').add(idea)
        return jsonify({'id': doc_ref[1].id, **idea}), 201
    
    # GET request
    ideas = []
    docs = db.collection('ideas').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        idea = doc.to_dict()
        idea['id'] = doc.id
        ideas.append(idea)
    return jsonify(ideas)

@app.route('/api/ideas/<idea_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_idea(idea_id):
    doc_ref = db.collection('ideas').document(idea_id)
    
    if request.method == 'GET':
        doc = doc_ref.get()
        if doc.exists:
            idea = doc.to_dict()
            idea['id'] = doc.id
            return jsonify(idea)
        return jsonify({'error': 'Idea not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.update(data)
        return jsonify({'message': 'Idea updated successfully'})
    
    elif request.method == 'DELETE':
        doc_ref.delete()
        return jsonify({'message': 'Idea deleted successfully'})

@app.route('/api/generate/title', methods=['POST'])
def generate_title():
    data = request.json
    topic = data.get('topic', '')
    audience = data.get('audience', '')
    key_points = data.get('key_points', '')
    
    prompt = f"""Generate 5 YouTube video titles for:
    Topic: {topic}
    Target Audience: {audience}
    Key Points: {key_points}
    
    Make them catchy, SEO-optimized, and under 60 characters each.
    Return as JSON array of strings."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube content optimization expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/description', methods=['POST'])
def generate_description():
    data = request.json
    title = data.get('title', '')
    topic = data.get('topic', '')
    key_points = data.get('key_points', '')
    
    prompt = f"""Generate a YouTube video description for:
    Title: {title}
    Topic: {topic}
    Key Points: {key_points}
    
    Include: hook, main content overview, timestamps placeholder, call-to-action, and relevant hashtags.
    Keep it under 500 characters for preview, with full description up to 2000 characters.
    Return as JSON with 'preview' and 'full' fields."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube content optimization expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/thumbnail-text', methods=['POST'])
def generate_thumbnail_text():
    data = request.json
    title = data.get('title', '')
    
    prompt = f"""Generate 3 compelling thumbnail text options for YouTube video titled: "{title}"
    
    Each should be:
    - 2-5 words maximum
    - High impact and emotional
    - Creates curiosity
    - Works with or without the title
    
    Return as JSON array of strings."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube thumbnail optimization expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule', methods=['GET', 'POST', 'PUT'])
def manage_schedule():
    doc_ref = db.collection('settings').document('schedule')
    
    if request.method == 'POST' or request.method == 'PUT':
        data = request.json
        schedule = {
            'cadence': data.get('cadence', 'daily'),
            'custom_days': data.get('custom_days', []),
            'post_by_time': data.get('post_by_time', '18:00'),
            'reminders': data.get('reminders', {'60min': True, '10min': True}),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(schedule)
        return jsonify(schedule)
    
    # GET request
    doc = doc_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict())
    return jsonify({
        'cadence': 'daily',
        'custom_days': [],
        'post_by_time': '18:00',
        'reminders': {'60min': True, '10min': True}
    })

@app.route('/api/streak', methods=['GET', 'POST'])
def manage_streak():
    doc_ref = db.collection('settings').document('streak')
    
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        doc = doc_ref.get()
        current_streak = doc.to_dict().get('count', 0) if doc.exists else 0
        
        if action == 'increment':
            new_streak = current_streak + 1
        elif action == 'reset':
            new_streak = 0
        else:
            new_streak = current_streak
        
        doc_ref.set({
            'count': new_streak,
            'last_update': firestore.SERVER_TIMESTAMP
        })
        return jsonify({'count': new_streak})
    
    # GET request
    doc = doc_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict())
    return jsonify({'count': 0})

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    doc_ref = db.collection('settings').document('general')
    
    if request.method == 'POST':
        data = request.json
        settings = {
            'channel_name': data.get('channel_name', ''),
            'channel_description': data.get('channel_description', ''),
            'default_font': data.get('default_font', 'Mohave'),
            'default_template': data.get('default_template', 'text-over-image'),
            'theme_colors': data.get('theme_colors', {'primary': '#DC2626', 'background': '#000000'}),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(settings)
        return jsonify(settings)
    
    # GET request
    doc = doc_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict())
    return jsonify({
        'channel_name': '',
        'channel_description': '',
        'default_font': 'Mohave',
        'default_template': 'text-over-image',
        'theme_colors': {'primary': '#DC2626', 'background': '#000000'}
    })

@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    # This is a placeholder for background removal
    # In production, you'd use a service like remove.bg API or implement with rembg library
    data = request.json
    image_data = data.get('image')
    
    # For now, return the same image
    # You can integrate with remove.bg API or use rembg library
    return jsonify({'image': image_data, 'message': 'Background removal placeholder'})

if __name__ == '__main__':
    app.run(debug=True)