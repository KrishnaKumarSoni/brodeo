# Brodeo Project Constitution & Guidance for Claude Code CLI

## IMPORTANT INSTRUCTIONS
YOU MUST keep the scope to ONLY the features and requirements described in this file. Do not add any extra functionality, such as user authentication, multi-user support, or unrelated features. This is a personal, single-user tool with no login required.

YOU MUST use only the specified tech stack: HTML, CSS, JS for frontend; Python Flask for backend. Deploy on Vercel using GitHub CLI and Vercel CLI (assume user is logged in). Use venv for all Python work. Firebase JSON is in the project root; assume user is logged in on Firebase CLI for any database needs.

YOU MUST use ONLY off-the-shelf Tailwind CSS components. NEVER use manually coded or customized CSS components. Theme: Black and red color scheme, Mohave font for headings, Inter for body text, small font sizes, modern trendy UI, dark mode interface throughout. Use real icons (not emojis), TailwindCSS-based dropdowns and icons in our design style (not system defaults). Avoid jumbo components; keep everything compact.

When generating code:
- Always activate venv before running Python commands.
- Import necessary packages in code; no internet installs.
- Ensure AI integrations use gpt-4o-mini for title/description generation.
- For thumbnails: Integrate background removal, Google Fonts, customizable options as specified.
- Preview thumbnails in light/dark YouTube dummy mockups.
- Use Firebase for data storage (e.g., video ideas, schedules) since config is present.

## 1. Project Overview
Brodeo is a personal web app to help plan, prepare, and stay consistent with YouTube uploads. It combines a simple planning interface with AI-assisted title, description, and thumbnail creation, plus a lightweight scheduling & streak system.

Core Focus:
- Plan videos in a calendar with drag-and-drop.
- Maintain a Kanban backlog of video ideas.
- Create titles, descriptions, and thumbnails with AI help.
- Design thumbnails with templates, fonts, background removal, and previews.
- Attach AI-generated assets to ideas.
- Set posting cadence and deadline.
- Receive two reminders per day.
- Track streaks and auto-carry missed items.
- Manage settings for personalization.

No login — personal, single-user tool.

## 2. Technology Stack
- **Frontend**: HTML, CSS (Tailwind CSS only), JavaScript (vanilla or minimal libraries if needed).
- **Backend**: Python with Flask.
- **Deployment**: Vercel (use Vercel CLI for deploy).
- **AI**: gpt-4o-mini for title, description, thumbnail text suggestions.
- **Database**: Firebase (config in root firebase.json).
- **Fonts**: Mohave for headings, Inter for body.
- **Theme**: Dark mode only, black/red palette, small fonts, modern UI.
- **Tools**: GitHub CLI for repo management, venv for Python env.
- **Other**: Drag-and-drop via JS libraries if off-the-shelf, background removal via Canvas or simple JS.

## 3. Architecture & Key Files
- **Folder Structure**:
  - / (root): app.py (Flask app), firebase.json, requirements.txt, CLAUDE.md.
  - /static: CSS/JS files (Tailwind compiled).
  - /templates: HTML files for screens.
  - /assets: User-uploaded images/thumbnails.
- **Cornerstone Files**:
  - app.py: Main Flask entrypoint.
  - index.html: Main layout with top bar (Next Due + Streak).
  - calendar.html, backlog.html, editor.html, schedule.html, settings.html: Screen templates.
- **Data Models**:
  - Video Idea: {id, title, description, tags, priority, status (Idea/Drafting/Editing/Ready/Scheduled/Published), assets (thumbnails, etc.), schedule_date}.
  - Schedule: {cadence (daily/custom days), post_by_time, reminders (60min/10min)}.
  - Settings: {channel_details, default_fonts, thumbnail_template, colors}.
- Use Firebase Realtime Database or Firestore for storing ideas, schedules, settings.

## 4. Key Screens & Functions
Implement exactly as described:

A. **Calendar**:
- Views: Month, week, day.
- Drag video ideas onto dates.
- Color-coded status chips.
- Show “Next Due” time and countdown.
- Preview title/thumbnail in light/dark YouTube mockups.

B. **Backlog (Kanban)**:
- Columns: Idea → Drafting → Editing → Ready → Scheduled → Published.
- Cards: Title, short desc, tags, priority, jump to Editor.

C. **Editor**:
- Input: Topic, audience, key points.
- AI: Generate titles/descriptions (multiple options, editable via gpt-4o-mini).
- Thumbnail Studio: Sizes (16:9,4:3,1:1,9:16); Templates (Text only, Text over image, Text behind subject, Image only); Background removal; Google Fonts; Customizable font/size/color/border, background (solid/gradient/AI-image); AI text suggestions; Light/dark previews; Save/download.

D. **Schedule**:
- Cadence: Daily or custom days.
- Single post-by time per day.
- Reminders: 60min and 10min before (browser notifications).
- Streak: Increment if published before deadline; reset if missed.
- Auto-Carry: Move missed to next day.

E. **Settings**:
- Channel details, default fonts/templates/colors.

## 5. User Experience Principles
- Minimal clicks: Idea → draft → final asset.
- Visual clarity: Status colors, simple layouts.
- Deadlines always visible: Next Due + Streak in top bar.
- AI aids, editable outputs.
- Two gentle nudges/day to avoid fatigue.
- Light/dark previews for accuracy.

## 6. Critical Coding Workflow
YOU MUST follow this sequence:
1. Activate venv: `source venv/bin/activate`.
2. Develop features in small increments.
3. Test locally: `flask run`.
4. Commit changes: Use GitHub CLI (e.g., `gh repo sync`).
5. Deploy: `vercel deploy`.
6. Format code: Use Black for Python, Prettier for JS/HTML if integrated.
7. No custom CSS: Compile Tailwind only.

## 7. Key Development Commands
- Setup venv: `python -m venv venv`.
- Install deps: `pip install flask openai firebase-admin` (assume pre-installed if needed).
- Run app: `flask run`.
- Build Tailwind: `npx tailwindcss -i input.css -o output.css --watch`.
- Deploy: `vercel`.
- Firebase: `firebase deploy` if needed.

## 8. Coding Standards
- Python: PEP8, use type hints.
- JS: ES6+, minimal.
- HTML: Semantic, accessible.
- Naming: camelCase for JS, snake_case for Python.
- Comments: Concise, only where needed.
- Errors: Handle gracefully, log to console.
- AI Calls: Use gpt-4o-mini via OpenAI API.

## 9. Version Control Etiquette
- Branch: feature/name.
- Commit: "feat: add calendar view".
- PR: Use GitHub CLI.

## 10. Debugging Instructions
- Log errors to console.
- Test AI outputs manually.
- For drag-drop issues: Check JS console.
- Thumbnail previews: Ensure Canvas API usage.

## 11. Do Not Touch List
- firebase.json: Do not modify.
- External APIs: Only gpt-4o-mini.
- Scope: No expansions beyond described.

use wsgi based deployment on vercel. 

custom dropdowns in our design system and no system default dropdowns

Full google font suite real one no hardcoded

Real black dark mode

Realistic YouTube dummy to test thumbnails

NEVER commit firebase josn or firebaseConfig.md please. 