// State management
let currentView = 'calendar';
let videos = [];
let settings = {};
let currentEditingVideo = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadVideos();
    loadSettings();
    loadReferenceFaces();
    initializeKanban();
    initializeCalendar();
    startCountdown();
    
    // Set default view
    showView('calendar');
});

// View management
function showView(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`${view}-view`).classList.remove('hidden');
    currentView = view;
    
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('text-brodeo-red');
        if (btn.textContent.toLowerCase() === view) {
            btn.classList.add('text-brodeo-red');
        }
    });
}

// API calls
async function loadVideos() {
    try {
        const response = await fetch('/api/videos');
        videos = await response.json();
        updateKanban();
        updateCalendar();
    } catch (error) {
        console.error('Error loading videos:', error);
    }
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        settings = await response.json();
        updateSettingsUI();
        updateStreakUI();
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveVideo(video) {
    try {
        const method = video.id ? 'PUT' : 'POST';
        const url = video.id ? `/api/videos/${video.id}` : '/api/videos';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(video)
        });
        
        const savedVideo = await response.json();
        if (!video.id) {
            videos.push(savedVideo);
        } else {
            const index = videos.findIndex(v => v.id === video.id);
            videos[index] = savedVideo;
        }
        
        updateKanban();
        updateCalendar();
        return savedVideo;
    } catch (error) {
        console.error('Error saving video:', error);
    }
}

// Kanban functionality
function initializeKanban() {
    const columns = ['idea', 'drafting', 'editing', 'ready', 'scheduled', 'published'];
    
    columns.forEach(status => {
        const element = document.getElementById(`col-${status}`);
        if (element) {
            new Sortable(element, {
                group: 'kanban',
                animation: 150,
                onEnd: async (evt) => {
                    const videoId = parseInt(evt.item.dataset.videoId);
                    const newStatus = evt.to.id.replace('col-', '');
                    
                    const video = videos.find(v => v.id === videoId);
                    if (video) {
                        video.status = newStatus;
                        await saveVideo(video);
                        
                        if (newStatus === 'published') {
                            incrementStreak();
                        }
                    }
                }
            });
        }
    });
}

function updateKanban() {
    const columns = ['idea', 'drafting', 'editing', 'ready', 'scheduled', 'published'];
    
    columns.forEach(status => {
        const container = document.getElementById(`col-${status}`);
        if (container) {
            container.innerHTML = '';
            
            const statusVideos = videos.filter(v => v.status === status);
            statusVideos.forEach(video => {
                const card = createKanbanCard(video);
                container.appendChild(card);
            });
        }
    });
}

function createKanbanCard(video) {
    const card = document.createElement('div');
    card.className = 'bg-gray-800 rounded p-3 cursor-move hover:bg-gray-700 transition-colors';
    card.dataset.videoId = video.id;
    
    const statusColors = {
        'idea': 'bg-gray-500',
        'drafting': 'bg-yellow-500',
        'editing': 'bg-blue-500',
        'ready': 'bg-green-500',
        'scheduled': 'bg-purple-500',
        'published': 'bg-brodeo-red'
    };
    
    card.innerHTML = `
        <div class="mb-2">
            <span class="inline-block px-2 py-1 text-xs rounded ${statusColors[video.status]} text-white">
                ${video.status.toUpperCase()}
            </span>
        </div>
        <h4 class="text-sm font-semibold mb-1">${video.title || 'Untitled'}</h4>
        <p class="text-xs text-gray-400 mb-2">${video.description || 'No description'}</p>
        <div class="flex justify-between items-center">
            <div class="flex space-x-1">
                ${(video.tags || []).map(tag => `
                    <span class="text-xs bg-gray-700 px-2 py-1 rounded">${tag}</span>
                `).join('')}
            </div>
            <button onclick="editVideo(${video.id})" class="text-xs text-brodeo-red hover:text-red-400">
                Edit →
            </button>
        </div>
    `;
    
    return card;
}

function addNewIdea() {
    const title = prompt('Enter video title:');
    if (title) {
        saveVideo({
            title: title,
            status: 'idea',
            description: '',
            tags: []
        });
    }
}

function editVideo(id) {
    currentEditingVideo = videos.find(v => v.id === id);
    if (currentEditingVideo) {
        showView('editor');
        document.getElementById('topic-input').value = currentEditingVideo.topic || '';
        document.getElementById('audience-input').value = currentEditingVideo.audience || '';
        document.getElementById('keypoints-input').value = (currentEditingVideo.key_points || []).join('\n');
    }
}

// Calendar functionality
function initializeCalendar() {
    renderCalendar('month');
}

function calendarView(view) {
    renderCalendar(view);
}

function renderCalendar(view) {
    const container = document.getElementById('calendar-container');
    const today = new Date();
    
    if (view === 'month') {
        container.innerHTML = renderMonthView(today);
    } else if (view === 'week') {
        container.innerHTML = renderWeekView(today);
    } else if (view === 'day') {
        container.innerHTML = renderDayView(today);
    }
}

function renderMonthView(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    let html = '<div class="grid grid-cols-7 gap-2">';
    
    // Day headers
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        html += `<div class="text-xs font-semibold text-gray-400 text-center py-2">${day}</div>`;
    });
    
    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        html += '<div class="h-24 bg-gray-800 rounded"></div>';
    }
    
    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayVideos = videos.filter(v => {
            if (v.scheduled_date) {
                const vDate = new Date(v.scheduled_date);
                return vDate.getDate() === day && vDate.getMonth() === month && vDate.getFullYear() === year;
            }
            return false;
        });
        
        html += `
            <div class="h-24 bg-gray-800 rounded p-2 hover:bg-gray-700 transition-colors" ondrop="dropVideo(event, '${year}-${month+1}-${day}')" ondragover="allowDrop(event)">
                <div class="text-xs font-semibold mb-1">${day}</div>
                <div class="space-y-1">
                    ${dayVideos.slice(0, 2).map(v => `
                        <div class="text-xs bg-${getStatusColor(v.status)}-500 px-1 py-0.5 rounded truncate">
                            ${v.title}
                        </div>
                    `).join('')}
                    ${dayVideos.length > 2 ? `<div class="text-xs text-gray-400">+${dayVideos.length - 2} more</div>` : ''}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

function renderWeekView(date) {
    // Simplified week view
    return '<div class="text-center py-20 text-gray-400">Week view coming soon</div>';
}

function renderDayView(date) {
    // Simplified day view
    return '<div class="text-center py-20 text-gray-400">Day view coming soon</div>';
}

function getStatusColor(status) {
    const colors = {
        'idea': 'gray',
        'drafting': 'yellow',
        'editing': 'blue',
        'ready': 'green',
        'scheduled': 'purple',
        'published': 'red'
    };
    return colors[status] || 'gray';
}

function allowDrop(ev) {
    ev.preventDefault();
}

function dropVideo(ev, date) {
    ev.preventDefault();
    // Implementation for drag and drop
}

function updateCalendar() {
    if (currentView === 'calendar') {
        renderCalendar('month');
    }
}

// Editor functionality
async function generateTitles() {
    const topic = document.getElementById('topic-input').value;
    const audience = document.getElementById('audience-input').value;
    const keyPoints = document.getElementById('keypoints-input').value.split('\n').filter(p => p.trim());
    
    try {
        const response = await fetch('/api/ai/generate-titles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, audience, key_points: keyPoints })
        });
        
        const data = await response.json();
        const container = document.getElementById('title-suggestions');
        container.innerHTML = '';
        
        data.titles.forEach(title => {
            const div = document.createElement('div');
            div.className = 'p-2 bg-gray-800 rounded hover:bg-gray-700 cursor-pointer text-sm';
            div.textContent = title;
            div.onclick = () => {
                if (currentEditingVideo) {
                    currentEditingVideo.title = title;
                    saveVideo(currentEditingVideo);
                }
            };
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Error generating titles:', error);
    }
}

async function generateDescription() {
    const title = currentEditingVideo?.title || '';
    const topic = document.getElementById('topic-input').value;
    const keyPoints = document.getElementById('keypoints-input').value.split('\n').filter(p => p.trim());
    
    try {
        const response = await fetch('/api/ai/generate-description', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, topic, key_points: keyPoints })
        });
        
        const data = await response.json();
        document.getElementById('description-output').value = data.description;
        
        if (currentEditingVideo) {
            currentEditingVideo.description = data.description;
            saveVideo(currentEditingVideo);
        }
    } catch (error) {
        console.error('Error generating description:', error);
    }
}

async function generateThumbnailText() {
    const title = currentEditingVideo?.title || document.getElementById('topic-input').value;
    
    try {
        const response = await fetch('/api/ai/generate-thumbnail-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        
        const data = await response.json();
        // Show suggestions (simplified for now)
        if (data.suggestions && data.suggestions.length > 0) {
            document.getElementById('thumbnail-text').value = data.suggestions[0];
            updateThumbnailPreview();
        }
    } catch (error) {
        console.error('Error generating thumbnail text:', error);
    }
}

// Thumbnail Studio
function setAspectRatio(ratio) {
    const preview = document.getElementById('thumbnail-preview');
    preview.className = preview.className.replace(/aspect-\w+/, '');
    
    const aspectClasses = {
        '16:9': 'aspect-video',
        '4:3': 'aspect-4/3',
        '1:1': 'aspect-square',
        '9:16': 'aspect-9/16'
    };
    
    preview.classList.add(aspectClasses[ratio] || 'aspect-video');
    
    // Update button states
    document.querySelectorAll('.aspect-btn').forEach(btn => {
        btn.classList.remove('bg-brodeo-red');
        if (btn.textContent === ratio) {
            btn.classList.add('bg-brodeo-red');
        }
    });
}

function updateThumbnailPreview() {
    const text = document.getElementById('thumbnail-text').value;
    const font = document.getElementById('font-select').value;
    const fontSize = document.getElementById('font-size').value;
    const textColor = document.getElementById('text-color').value;
    const bgColor = document.getElementById('bg-color').value;
    
    const preview = document.getElementById('thumbnail-preview');
    preview.style.background = bgColor;
    preview.innerHTML = `
        <span style="font-family: ${font}; font-size: ${fontSize}px; color: ${textColor}; font-weight: bold;">
            ${text || 'THUMBNAIL'}
        </span>
    `;
}

function previewMode(mode) {
    const preview = document.getElementById('thumbnail-preview');
    if (mode === 'light') {
        preview.parentElement.classList.add('bg-white');
        preview.parentElement.classList.remove('bg-gray-800');
    } else {
        preview.parentElement.classList.remove('bg-white');
        preview.parentElement.classList.add('bg-gray-800');
    }
}

function saveThumbnail() {
    if (currentEditingVideo) {
        currentEditingVideo.thumbnail = {
            text: document.getElementById('thumbnail-text').value,
            font: document.getElementById('font-select').value,
            fontSize: document.getElementById('font-size').value,
            textColor: document.getElementById('text-color').value,
            bgColor: document.getElementById('bg-color').value,
            template: document.getElementById('template-select').value
        };
        saveVideo(currentEditingVideo);
        alert('Thumbnail saved!');
    }
}

function downloadThumbnail() {
    // Implementation for downloading thumbnail as image
    alert('Download functionality will be implemented with canvas rendering');
}

// Schedule & Streak
document.getElementById('cadence-select')?.addEventListener('change', (e) => {
    const customDays = document.getElementById('custom-days');
    if (e.target.value === 'custom') {
        customDays.classList.remove('hidden');
    } else {
        customDays.classList.add('hidden');
    }
});

async function saveSchedule() {
    const schedule = {
        cadence: document.getElementById('cadence-select').value,
        custom_days: Array.from(document.querySelectorAll('.day-checkbox:checked')).map(cb => cb.value),
        deadline_time: document.getElementById('deadline-time').value,
        reminder_60: document.getElementById('reminder-60').checked,
        reminder_10: document.getElementById('reminder-10').checked
    };
    
    settings.schedule = schedule;
    
    try {
        await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        alert('Schedule saved!');
    } catch (error) {
        console.error('Error saving schedule:', error);
    }
}

async function incrementStreak() {
    try {
        const response = await fetch('/api/streak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'increment' })
        });
        
        const streak = await response.json();
        settings.streak = streak;
        updateStreakUI();
    } catch (error) {
        console.error('Error updating streak:', error);
    }
}

function updateStreakUI() {
    if (settings.streak) {
        document.getElementById('streak-counter').textContent = settings.streak.current;
        document.getElementById('current-streak').textContent = settings.streak.current;
        document.getElementById('best-streak').textContent = settings.streak.best;
        
        if (settings.streak.last_publish) {
            const date = new Date(settings.streak.last_publish);
            document.getElementById('last-publish').textContent = date.toLocaleDateString();
        }
    }
}

// Settings
async function saveSettings() {
    const newSettings = {
        ...settings,
        channel_name: document.getElementById('channel-name').value,
        channel_description: document.getElementById('channel-description').value,
        default_font: document.getElementById('default-font').value,
        default_template: document.getElementById('default-template').value,
        default_colors: {
            primary: document.getElementById('primary-color').value,
            secondary: document.getElementById('secondary-color').value
        }
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSettings)
        });
        
        settings = await response.json();
        alert('Settings saved!');
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

function updateSettingsUI() {
    if (settings.channel_name) {
        document.getElementById('channel-name').value = settings.channel_name;
    }
    if (settings.channel_description) {
        document.getElementById('channel-description').value = settings.channel_description;
    }
    if (settings.default_font) {
        document.getElementById('default-font').value = settings.default_font;
    }
    if (settings.default_template) {
        document.getElementById('default-template').value = settings.default_template;
    }
    if (settings.default_colors) {
        document.getElementById('primary-color').value = settings.default_colors.primary;
        document.getElementById('secondary-color').value = settings.default_colors.secondary;
    }
    if (settings.schedule) {
        document.getElementById('cadence-select').value = settings.schedule.cadence;
        document.getElementById('deadline-time').value = settings.schedule.deadline_time;
        document.getElementById('reminder-60').checked = settings.schedule.reminder_60;
        document.getElementById('reminder-10').checked = settings.schedule.reminder_10;
    }
}

// Countdown timer
function startCountdown() {
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

function updateCountdown() {
    const now = new Date();
    const deadline = getNextDeadline();
    
    if (deadline) {
        const diff = deadline - now;
        if (diff > 0) {
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            
            document.getElementById('next-due').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            document.getElementById('next-due').textContent = 'OVERDUE';
            document.getElementById('next-due').classList.add('animate-pulse');
        }
    }
}

function getNextDeadline() {
    if (!settings.schedule) return null;
    
    const now = new Date();
    const [hours, minutes] = (settings.schedule.deadline_time || '18:00').split(':');
    const deadline = new Date();
    deadline.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    
    if (deadline <= now) {
        deadline.setDate(deadline.getDate() + 1);
    }
    
    return deadline;
}

// Reference Faces Management
async function loadReferenceFaces() {
    try {
        const response = await fetch('/api/reference-faces');
        const faces = await response.json();
        updateReferenceFacesList(faces);
        updateFaceSelector(faces);
    } catch (error) {
        console.error('Error loading reference faces:', error);
    }
}

function updateReferenceFacesList(faces) {
    const container = document.getElementById('reference-faces-list');
    if (!container) return;
    
    container.innerHTML = '';
    faces.forEach(face => {
        const div = document.createElement('div');
        div.className = 'relative group';
        div.innerHTML = `
            <div class="aspect-square bg-gray-800 rounded-lg overflow-hidden">
                <img src="${face.url}" alt="${face.name}" class="w-full h-full object-cover">
            </div>
            <div class="absolute inset-0 bg-black bg-opacity-75 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex flex-col items-center justify-center">
                <p class="text-sm font-semibold mb-2">${face.name}</p>
                <button onclick="deleteReferenceFace('${face.filename}')" class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs">Delete</button>
            </div>
        `;
        container.appendChild(div);
    });
}

function updateFaceSelector(faces) {
    const container = document.getElementById('face-selector');
    if (!container) return;
    
    container.innerHTML = '';
    faces.forEach(face => {
        const label = document.createElement('label');
        label.className = 'flex items-center space-x-2 cursor-pointer hover:bg-gray-800 p-2 rounded';
        label.innerHTML = `
            <input type="checkbox" value="${face.filename}" class="face-checkbox">
            <span class="text-xs">${face.name}</span>
        `;
        container.appendChild(label);
    });
}

async function uploadReferenceFace(input) {
    const file = input.files[0];
    if (!file) return;
    
    const name = prompt('Enter a name for this face:');
    if (!name) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    
    try {
        const response = await fetch('/api/reference-faces', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('Face uploaded successfully!');
            loadReferenceFaces();
        } else {
            const error = await response.json();
            alert('Error uploading face: ' + error.error);
        }
    } catch (error) {
        console.error('Error uploading face:', error);
        alert('Error uploading face');
    }
    
    // Reset input
    input.value = '';
}

async function deleteReferenceFace(filename) {
    if (!confirm('Delete this reference face?')) return;
    
    try {
        const response = await fetch('/api/reference-faces', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        
        if (response.ok) {
            loadReferenceFaces();
        }
    } catch (error) {
        console.error('Error deleting face:', error);
    }
}

// AI Thumbnail Generation
async function generateAIThumbnail() {
    const text = document.getElementById('thumbnail-text').value;
    const template = document.getElementById('template-select').value;
    const selectedFaces = Array.from(document.querySelectorAll('.face-checkbox:checked')).map(cb => cb.value);
    
    if (!text) {
        alert('Please enter thumbnail text first');
        return;
    }
    
    try {
        const response = await fetch('/api/ai/generate-thumbnail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                template: template,
                include_faces: selectedFaces
            })
        });
        
        const data = await response.json();
        
        if (data.image_url) {
            // Update preview with generated image
            const preview = document.getElementById('thumbnail-preview');
            preview.innerHTML = `<img src="${data.image_url}" alt="Generated thumbnail" class="w-full h-full object-cover rounded">`;
            
            if (currentEditingVideo) {
                currentEditingVideo.ai_thumbnail_url = data.image_url;
                saveVideo(currentEditingVideo);
            }
        } else if (data.error) {
            alert('Error generating thumbnail: ' + data.error);
        }
    } catch (error) {
        console.error('Error generating AI thumbnail:', error);
        alert('Error generating thumbnail');
    }
}

// Event listeners for live updates
document.getElementById('thumbnail-text')?.addEventListener('input', updateThumbnailPreview);
document.getElementById('font-select')?.addEventListener('change', updateThumbnailPreview);
document.getElementById('font-size')?.addEventListener('input', updateThumbnailPreview);
document.getElementById('text-color')?.addEventListener('input', updateThumbnailPreview);
document.getElementById('bg-color')?.addEventListener('input', updateThumbnailPreview);