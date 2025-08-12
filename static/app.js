// Global utility functions for Brodeo

// API helper functions
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Notification helper
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all ${
        type === 'success' ? 'bg-green-600' : 
        type === 'error' ? 'bg-red-600' : 
        'bg-blue-600'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Date formatting
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Debounce function for input fields
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Local storage helpers
const storage = {
    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Storage get error:', error);
            return null;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage set error:', error);
        }
    },
    
    remove(key) {
        localStorage.removeItem(key);
    }
};

// Initialize app-wide features
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permission if needed
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Set up global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + S to save
        if ((e.metaKey || e.ctrlKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('[onclick*="save"]');
            if (saveBtn) saveBtn.click();
        }
        
        // Cmd/Ctrl + N for new idea
        if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/editor';
        }
    });
    
    // Auto-save draft every 30 seconds if on editor page
    if (window.location.pathname === '/editor') {
        setInterval(() => {
            const draft = {
                topic: document.getElementById('topic')?.value,
                audience: document.getElementById('audience')?.value,
                keyPoints: document.getElementById('keyPoints')?.value,
                title: document.getElementById('selectedTitle')?.value,
                description: document.getElementById('selectedDescription')?.value,
                timestamp: new Date().toISOString()
            };
            
            if (draft.topic || draft.title) {
                storage.set('draft', draft);
                console.log('Draft auto-saved');
            }
        }, 30000);
    }
});

// Export utilities for use in templates
window.brodeoUtils = {
    apiCall,
    showNotification,
    formatDate,
    formatTime,
    debounce,
    storage
};