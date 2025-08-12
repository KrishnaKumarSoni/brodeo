# Brodeo - YouTube Planning Web App

A personal YouTube content planning and management system built with Flask and modern web technologies.

## 🎯 Features

### 📅 Content Calendar
- Month, week, and day views
- Drag-and-drop video scheduling
- Status tracking (Idea → Drafting → Editing → Ready → Scheduled → Published)
- Next deadline countdown timer

### 📋 Kanban Backlog
- Visual content pipeline management
- Drag-and-drop between status columns
- Quick video editing access
- Tags and priority management

### ✍️ AI-Powered Editor
- Topic, audience, and key points input
- AI-generated title suggestions (multiple options)
- AI-generated descriptions
- Editable AI outputs

### 🎨 Thumbnail Studio
- Multiple aspect ratios (16:9, 4:3, 1:1, 9:16)
- Templates: Text only, Text over image, Text behind subject, Image only
- AI thumbnail generation with DALL-E 3
- **Reference face photos** - Upload photos of people to include in AI-generated thumbnails
- Custom fonts (Mohave, Inter), colors, and styling
- Light/dark preview modes
- Save and download options

### 📊 Schedule & Streak Tracking
- Daily or custom day scheduling
- Deadline reminders (60min & 10min before)
- Streak counter (increments on on-time publishing)
- Auto-carry missed items to next day

### ⚙️ Settings
- Channel configuration
- Default fonts, templates, and colors
- Reference face photo management

## 🚀 Deployment

### Live Demo
**Deployed on Vercel:** [https://brodeo-oz4mova7b-krishnas-projects-cc548bc4.vercel.app](https://brodeo-oz4mova7b-krishnas-projects-cc548bc4.vercel.app)

### GitHub Repository
**Source Code:** [https://github.com/KrishnaKumarSoni/brodeo](https://github.com/KrishnaKumarSoni/brodeo)

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Node.js and npm
- OpenAI API Key

### Local Development

1. **Clone and setup:**
```bash
git clone https://github.com/KrishnaKumarSoni/brodeo.git
cd brodeo
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
npm install
```

2. **Environment Configuration:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_openai_api_key_here
# SECRET_KEY=your_secret_key_here
```

3. **Build CSS and run:**
```bash
npx tailwindcss -i ./src/input.css -o ./static/output.css
python app.py
```

4. **Access the app:**
Open [http://localhost:5000](http://localhost:5000)

### Vercel Deployment

1. **Deploy to Vercel:**
```bash
npx vercel
```

2. **Set environment variables:**
```bash
npx vercel env add OPENAI_API_KEY production
npx vercel env add SECRET_KEY production
```

## 🎨 Design

- **Theme:** Black + Red aesthetic
- **Fonts:** Mohave (headings), Inter (body)
- **UI:** Dark mode, modern, compact design
- **Icons:** Heroicons/TailwindCSS components

## 🤖 AI Features

- **Title Generation:** Multiple catchy options using GPT-4o-mini
- **Description Generation:** SEO-friendly descriptions
- **Thumbnail Generation:** DALL-E 3 integration with reference faces
- **Smart Prompting:** Context-aware AI suggestions

## 📁 Project Structure

```
brodeo/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Main frontend
├── static/
│   ├── app.js         # Frontend JavaScript
│   ├── output.css     # Compiled Tailwind CSS
│   └── uploads/       # Reference face photos
├── src/
│   └── input.css      # Tailwind source
├── requirements.txt    # Python dependencies
├── package.json       # Node.js dependencies
├── tailwind.config.js # Tailwind configuration
├── vercel.json        # Vercel deployment config
└── README.md          # This file
```

## 🔑 Key Technologies

- **Backend:** Flask, OpenAI API, Python
- **Frontend:** HTML, TailwindCSS, Vanilla JavaScript
- **AI:** GPT-4o-mini (text), DALL-E 3 (images)
- **Deployment:** Vercel
- **Storage:** Local file system (reference photos)

## 🎯 Target Users

Content creators who want:
- Consistent YouTube upload scheduling
- AI-assisted content planning
- Professional thumbnail creation
- Progress tracking and streak motivation

---

**Built with ❤️ using Claude Code**