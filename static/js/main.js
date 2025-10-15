// Main JavaScript for PakJobs Aggregator

// Utility functions
const showNotification = (message, type = 'info') => {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
};

// Loading indicator
const showLoading = () => {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loader.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(loader);
};

const hideLoading = () => {
    const loader = document.getElementById('global-loader');
    if (loader) loader.remove();
};

// Format numbers with commas
const formatNumber = (num) => {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

// Format date
const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
};

// Debounce function for search
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Auto-refresh scraper status (if on scrapers page)
if (window.location.pathname === '/scrapers') {
    setInterval(() => {
        // Optionally refresh scraper status every 30 seconds
        // location.reload();
    }, 30000);
}

// Handle form submissions with loading indicator
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            // Don't show loader for GET forms (search forms)
            if (form.method.toLowerCase() !== 'get') {
                showLoading();
            }
        });
    });
});

// Confirm before running scrapers
const confirmScraperRun = (siteName, mode) => {
    const message = `Run ${siteName} scraper in ${mode} mode?`;
    return confirm(message);
};

// Copy to clipboard functionality
const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy', 'error');
    });
};

// Export event tracking
document.querySelectorAll('a[href*="/export"]').forEach(link => {
    link.addEventListener('click', () => {
        showNotification('Export started...', 'info');
    });
});

console.log('PakJobs Aggregator initialized');
