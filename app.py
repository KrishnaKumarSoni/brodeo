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
try:
    # Check if we have Firebase environment variables (production)
    if os.getenv('FIREBASE_PROJECT_ID'):
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n') if os.getenv('FIREBASE_PRIVATE_KEY') else None,
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": "googleapis.com"
        }
        cred = credentials.Certificate(firebase_config)
    # Try using service account key file (for local development)
    elif os.path.exists('brodeo-yt-firebase-adminsdk-fbsvc-cb6d523df0.json'):
        cred = credentials.Certificate('brodeo-yt-firebase-adminsdk-fbsvc-cb6d523df0.json')
    else:
        raise Exception("No Firebase credentials found")
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    # Create a mock db for development if Firebase fails
    db = None

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Simple in-memory store for thumbnails (temporary solution)
# This will be replaced with proper Firestore storage
thumbnail_store = {}

def store_thumbnail_in_firestore(idea_id, thumbnail_data):
    """Store thumbnail as a separate document to avoid size limits"""
    try:
        # Store thumbnail in a separate collection
        thumbnail_doc = {
            'idea_id': idea_id,
            'data': thumbnail_data,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        db.collection('thumbnails').document(idea_id).set(thumbnail_doc)
        return True
    except Exception as e:
        print(f"Error storing thumbnail: {e}")
        # Fallback to memory store
        thumbnail_store[idea_id] = thumbnail_data
        return False

def get_thumbnail_from_firestore(idea_id):
    """Retrieve thumbnail from Firestore"""
    try:
        doc = db.collection('thumbnails').document(idea_id).get()
        if doc.exists:
            return doc.to_dict().get('data')
    except Exception as e:
        print(f"Error retrieving thumbnail: {e}")
    
    # Fallback to memory store
    return thumbnail_store.get(idea_id)

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
        
        # Handle assets separately to avoid Firestore size limits
        assets = data.get('assets', {})
        thumbnail_data = None
        if assets and 'thumbnail' in assets and assets['thumbnail']:
            # Store thumbnail separately
            thumbnail_data = assets['thumbnail']
            # Mark that this idea has a thumbnail
            assets['has_thumbnail'] = True
            # Don't store the actual data in the idea document
            del assets['thumbnail']
        
        idea = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'tags': data.get('tags', []),
            'priority': data.get('priority', 'medium'),
            'status': data.get('status', 'Idea'),
            'topic': data.get('topic', ''),
            'audience': data.get('audience', ''),
            'key_points': data.get('key_points', ''),
            'assets': assets,
            'schedule_date': data.get('schedule_date'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        try:
            doc_ref = db.collection('ideas').add(idea)
            idea_id = doc_ref[1].id
            
            # Store thumbnail separately if provided
            if thumbnail_data:
                store_thumbnail_in_firestore(idea_id, thumbnail_data)
            
            # Return only serializable data, not SERVER_TIMESTAMP
            response_data = {k: v for k, v in idea.items() if k not in ['created_at', 'updated_at']}
            response_data['id'] = idea_id
            
            # Include thumbnail in response
            if thumbnail_data:
                response_data['assets']['thumbnail'] = thumbnail_data
                
            return jsonify(response_data), 201
        except Exception as e:
            # If still failing, remove assets entirely and try again
            print(f"Firestore error with assets: {e}")
            idea_without_assets = {k: v for k, v in idea.items() if k != 'assets'}
            doc_ref = db.collection('ideas').add(idea_without_assets)
            response_data = {k: v for k, v in idea_without_assets.items() if k not in ['created_at', 'updated_at']}
            response_data['id'] = doc_ref[1].id
            return jsonify(response_data), 201
    
    # GET request
    ideas = []
    docs = db.collection('ideas').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        idea = doc.to_dict()
        idea['id'] = doc.id
        
        # Restore thumbnail if available
        if 'assets' in idea and idea['assets'] and idea['assets'].get('has_thumbnail'):
            thumbnail = get_thumbnail_from_firestore(doc.id)
            if thumbnail:
                idea['assets']['thumbnail'] = thumbnail
                
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
            
            print(f"Retrieved idea from Firestore: {idea}")
            
            # Restore thumbnail if available
            if 'assets' in idea and idea['assets'] and idea['assets'].get('has_thumbnail'):
                print(f"Looking for thumbnail for idea: {doc.id}")
                thumbnail = get_thumbnail_from_firestore(doc.id)
                if thumbnail:
                    idea['assets']['thumbnail'] = thumbnail
                    print("Thumbnail restored successfully")
                else:
                    print("No thumbnail found")
            else:
                print("No thumbnail marker found in assets")
                    
            return jsonify(idea)
        return jsonify({'error': 'Idea not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        
        # Handle assets separately to avoid Firestore size limits
        thumbnail_data = None
        if 'assets' in data:
            assets = data['assets']
            if assets and 'thumbnail' in assets and assets['thumbnail']:
                thumbnail_data = assets['thumbnail']
                # Mark that this idea has a thumbnail
                assets['has_thumbnail'] = True
                # Don't store the actual data in the idea document
                del assets['thumbnail']
        
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        try:
            doc_ref.update(data)
            
            # Store thumbnail separately if provided
            if thumbnail_data:
                store_thumbnail_in_firestore(idea_id, thumbnail_data)
                
            return jsonify({'message': 'Idea updated successfully'})
        except Exception as e:
            # If still failing, remove assets and try again
            print(f"Firestore update error with assets: {e}")
            if 'assets' in data:
                del data['assets']
            doc_ref.update(data)
            return jsonify({'message': 'Idea updated successfully (without assets)'})
    
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

@app.route('/api/generate/everything', methods=['POST'])
def generate_everything():
    data = request.json
    free_text_idea = data.get('idea', '')
    
    if not free_text_idea:
        return jsonify({'error': 'No idea provided'}), 400
    
    # First, extract structured data from free text
    structure_prompt = f"""Analyze this YouTube video idea and extract structured information:

    Idea: "{free_text_idea}"

    Extract and return JSON with:
    {{
        "topic": "clear topic (max 50 chars)",
        "audience": "target audience (max 50 chars)", 
        "key_points": "main points to cover (max 200 chars)",
        "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
        "priority": "high|medium|low",
        "estimated_length": "short|medium|long"
    }}"""
    
    try:
        # Step 1: Extract structure
        structure_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube content strategist. Extract structured data from video ideas."},
                {"role": "user", "content": structure_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        structure_data = json.loads(structure_response.choices[0].message.content)
        
        # Step 2: Generate titles
        title_prompt = f"""Generate 5 YouTube video titles for:
        Topic: {structure_data.get('topic', '')}
        Audience: {structure_data.get('audience', '')}
        Key Points: {structure_data.get('key_points', '')}
        
        Make them catchy, SEO-optimized, and under 60 characters each.
        Return as JSON: {{"titles": ["title1", "title2", ...]}}"""
        
        titles_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube title optimization expert."},
                {"role": "user", "content": title_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        titles_data = json.loads(titles_response.choices[0].message.content)
        
        # Step 3: Generate descriptions
        desc_prompt = f"""Generate a YouTube video description for:
        Topic: {structure_data.get('topic', '')}
        Audience: {structure_data.get('audience', '')}
        Key Points: {structure_data.get('key_points', '')}
        
        Include: hook, main content overview, timestamps placeholder, call-to-action, and relevant hashtags.
        Return as JSON: {{"preview": "first 125 chars", "full": "complete description"}}"""
        
        desc_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube description optimization expert."},
                {"role": "user", "content": desc_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        desc_data = json.loads(desc_response.choices[0].message.content)
        
        # Step 4: Generate image concepts
        image_concepts_prompt = f"""Generate 3 modern, visually compelling thumbnail image concepts for this YouTube video:
        Topic: {structure_data.get('topic', '')}
        Audience: {structure_data.get('audience', '')}
        Key Points: {structure_data.get('key_points', '')}
        
        IMPORTANT REQUIREMENTS:
        - NO TEXT, typography, words, letters, or written elements should appear in the image concepts
        - Focus purely on visual elements: objects, people, scenes, colors, lighting, composition
        - Each concept should be modern, cinematic, and professionally designed
        - Use contemporary visual trends: dramatic lighting, vibrant colors, dynamic compositions
        - Ensure concepts are click-worthy and attention-grabbing
        - Each description should be complete sentences with full details
        - Avoid truncated or incomplete descriptions
        
        Return as JSON: {{"concepts": [
            {{"title": "Engaging Concept Name", "description": "Complete detailed visual description focusing on modern cinematography, lighting, composition, and visual elements without any text components. Describe the scene, colors, mood, and visual style in full sentences.", "style": "photography|illustration|graphic"}},
            ...
        ]}}"""
        
        concepts_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a YouTube thumbnail design expert specializing in modern, text-free visual concepts. You create cinematic, attention-grabbing thumbnail ideas that rely purely on visual storytelling without any text elements. Focus on contemporary aesthetics, dramatic lighting, and compelling compositions."},
                {"role": "user", "content": image_concepts_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        concepts_data = json.loads(concepts_response.choices[0].message.content)
        
        # Combine all results
        result = {
            **structure_data,
            **titles_data,
            **desc_data,
            **concepts_data,
            "original_idea": free_text_idea
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/image-prompt', methods=['POST'])
def generate_image_prompt():
    data = request.json
    concept = data.get('concept', {})
    topic = data.get('topic', '')
    has_reference = data.get('has_reference_image', False)
    
    reference_context = ""
    if has_reference:
        reference_context = """
    - INCLUDE the person from the reference image as the main subject
    - Ensure the person is prominently featured and recognizable
    - Position the person in a way that complements the thumbnail concept
    - Maintain the person's likeness while fitting the overall composition
    """
    
    # Modern 2025 ChatGPT-style prompt generation
    style_guidelines = {
        'photography': "hyperrealistic photography, cinematic lighting, professional DSLR quality, bokeh depth of field, 8K resolution, trending on ArtStation",
        'illustration': "modern digital illustration, vibrant colors, clean vector style, trending on Behance, professional concept art quality",
        'graphic': "contemporary graphic design, bold geometric shapes, minimalist composition, Swiss design principles, modern UI/UX aesthetic",
        'mixed': "mixed media artwork, combining photorealistic elements with digital art, creative composite, trending visual style"
    }
    
    modern_style = style_guidelines.get(concept.get('style', 'photography'), style_guidelines['photography'])
    
    prompt = f"""Generate a modern, high-impact YouTube thumbnail prompt for:

    Topic: {topic}
    Concept: {concept.get('title', '')} - {concept.get('description', '')}
    
    Create a prompt that will generate a {modern_style} image with:
    
    VISUAL STYLE (2025 Modern Aesthetic):
    - Cinematic, movie poster quality composition
    - Vibrant, saturated colors with high contrast
    - Modern lighting: dramatic rim lighting, color grading, atmospheric haze
    - Contemporary visual trends: depth blur, light leaks, lens flares where appropriate
    - Professional studio quality with crisp 4K details
    - Dynamic angle and perspective for visual impact
    - Emotional and engaging visual storytelling
    {reference_context}
    
    TECHNICAL REQUIREMENTS:
    - 16:9 aspect ratio (1536x1024 for gpt-image-1)
    - NO text, words, letters, numbers, or typography in the image
    - Focus on visual elements only - text will be added separately
    - Clear subject with strong focal point
    - High visual clarity suitable for small thumbnail viewing
    
    MODERN STYLE ELEMENTS TO INCLUDE:
    - Contemporary color grading (teal/orange, moody blues, vibrant gradients)
    - Modern compositional techniques (rule of thirds, leading lines, depth layers)
    - Current visual trends (neon accents, glass morphism, 3D elements where relevant)
    - Professional post-processing look (HDR effect, color pop, selective focus)
    
    Generate a concise, effective prompt that will create a stunning, modern thumbnail image.
    
    Return JSON: {{"prompt": "modern style prompt for gpt-image-1", "style_notes": "key visual elements"}}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at creating DALL-E prompts for YouTube thumbnails."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    quality = data.get('quality', 'standard')  # Frontend sends standard/hd
    
    # Map DALL-E 3 quality values to gpt-image-1 values
    quality_mapping = {
        'standard': 'medium',
        'hd': 'high'
    }
    gpt_quality = quality_mapping.get(quality, 'medium')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        # Use GPT-4o native image generation (gpt-image-1) - latest model from 2025
        # Organization must be verified to use this model
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1536x1024",  # Landscape format (closest to 16:9 for YouTube thumbnails)
            quality=gpt_quality,   # low, medium, high, or auto
            n=1,
        )
        
        # GPT-4o image generation (gpt-image-1) returns base64 directly
        if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
            # Direct base64 response from gpt-image-1
            return jsonify({'image_url': f'data:image/png;base64,{response.data[0].b64_json}'})
        elif hasattr(response.data[0], 'url'):
            # Fallback to URL if provided (shouldn't happen with gpt-image-1)
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image_base64 = base64.b64encode(image_response.content).decode('utf-8')
                return jsonify({'image_url': f'data:image/png;base64,{image_base64}'})
            else:
                return jsonify({'image_url': image_url})
        else:
            return jsonify({'error': 'Unexpected response format from gpt-image-1'}), 500
            
    except Exception as e:
        # No fallback - only use gpt-image-1
        return jsonify({'error': f'Image generation failed with gpt-image-1: {str(e)}. Please ensure your OpenAI organization is verified.'}), 500

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

@app.route('/api/fonts', methods=['GET'])
def get_google_fonts():
    """Get Google Fonts list"""
    try:
        # Comprehensive list of popular Google Fonts - no API key needed
        popular_fonts = [
            # Sans-serif fonts
            {'family': 'Roboto'}, {'family': 'Open Sans'}, {'family': 'Lato'}, {'family': 'Montserrat'},
            {'family': 'Source Sans Pro'}, {'family': 'Raleway'}, {'family': 'PT Sans'}, {'family': 'Ubuntu'},
            {'family': 'Nunito'}, {'family': 'Work Sans'}, {'family': 'Poppins'}, {'family': 'Inter'},
            {'family': 'Fira Sans'}, {'family': 'Quicksand'}, {'family': 'Muli'}, {'family': 'Titillium Web'},
            {'family': 'Dosis'}, {'family': 'Varela Round'}, {'family': 'Karla'}, {'family': 'Barlow'},
            {'family': 'Catamaran'}, {'family': 'Exo'}, {'family': 'Cabin'}, {'family': 'Assistant'},
            {'family': 'Mukti'}, {'family': 'Oxygen'}, {'family': 'Arimo'}, {'family': 'Heebo'},
            
            # Display/Heading fonts
            {'family': 'Mohave'}, {'family': 'Bebas Neue'}, {'family': 'Anton'}, {'family': 'Oswald'},
            {'family': 'Fjalla One'}, {'family': 'Russo One'}, {'family': 'Righteous'}, {'family': 'Bangers'},
            {'family': 'Fredoka One'}, {'family': 'Archivo Black'}, {'family': 'Staatliches'}, {'family': 'Lobster'},
            {'family': 'Pacifico'}, {'family': 'Dancing Script'}, {'family': 'Permanent Marker'},
            {'family': 'Amatic SC'}, {'family': 'Comfortaa'}, {'family': 'Kalam'}, {'family': 'Alfa Slab One'},
            
            # Serif fonts
            {'family': 'Playfair Display'}, {'family': 'Merriweather'}, {'family': 'Libre Baskerville'},
            {'family': 'Crimson Text'}, {'family': 'Lora'}, {'family': 'Cormorant Garamond'},
            {'family': 'Source Serif Pro'}, {'family': 'Vollkorn'}, {'family': 'Bitter'}, {'family': 'Arvo'},
            {'family': 'PT Serif'}, {'family': 'Old Standard TT'}, {'family': 'Cardo'}, {'family': 'Neuton'},
            
            # Monospace fonts
            {'family': 'Roboto Mono'}, {'family': 'Source Code Pro'}, {'family': 'Space Mono'},
            {'family': 'Fira Code'}, {'family': 'JetBrains Mono'}, {'family': 'Inconsolata'},
            
            # Script/Handwriting fonts
            {'family': 'Great Vibes'}, {'family': 'Allura'}, {'family': 'Sacramento'}, {'family': 'Alex Brush'},
            {'family': 'Satisfy'}, {'family': 'Caveat'}, {'family': 'Indie Flower'}, {'family': 'Shadows Into Light'}
        ]
        
        google_fonts_api_key = os.getenv('GOOGLE_FONTS_API_KEY')
        if not google_fonts_api_key:
            # Return comprehensive list without needing API key
            return jsonify({'fonts': popular_fonts})
        
        url = f'https://www.googleapis.com/webfonts/v1/webfonts?key={google_fonts_api_key}&sort=popularity'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Return all fonts from API (no limit for full access)
            fonts = data.get('items', [])
            return jsonify({'fonts': fonts})
        else:
            # Fallback to comprehensive static list
            return jsonify({'fonts': popular_fonts})
            
    except Exception as e:
        print(f"Google Fonts API error: {e}")
        return jsonify({
            'fonts': [
                {'family': 'Mohave'}, {'family': 'Inter'}, {'family': 'Roboto'}, 
                {'family': 'Open Sans'}, {'family': 'Montserrat'}, {'family': 'Poppins'}
            ]
        })

@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    """Remove background from uploaded image using Remove.bg API"""
    data = request.json
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        remove_bg_api_key = os.getenv('REMOVE_BG_API_KEY')
        
        if not remove_bg_api_key:
            # Return original image if no API key
            return jsonify({
                'image': image_data, 
                'message': 'Remove.bg API key not configured. Background removal disabled.'
            })
        
        # Convert base64 to bytes
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Call Remove.bg API
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': image_bytes},
            data={'size': 'auto'},
            headers={'X-Api-Key': remove_bg_api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            # Convert result back to base64
            result_image = base64.b64encode(response.content).decode('utf-8')
            return jsonify({
                'image': f'data:image/png;base64,{result_image}',
                'message': 'Background removed successfully'
            })
        else:
            print(f"Remove.bg API error: {response.status_code} - {response.text}")
            return jsonify({
                'image': f'data:image/png;base64,{image_data}',
                'error': f'Background removal failed: {response.text}'
            }), response.status_code
            
    except Exception as e:
        print(f"Background removal error: {e}")
        return jsonify({
            'image': f'data:image/png;base64,{image_data}',
            'error': f'Background removal failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)