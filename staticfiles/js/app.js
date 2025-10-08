// SEU Tools Frontend JavaScript

// Global variables
let currentUser = null;
let charts = {};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();

    // Initialize file upload if present
    initializeFileUpload();

    // Initialize forms
    initializeForms();

    // Add fade-in animation to content
    document.querySelectorAll('.fade-in').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';

        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100);
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize file upload functionality
function initializeFileUpload() {
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.querySelector('#fileInput');

    if (fileUploadArea && fileInput) {
        // Click to select file
        fileUploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag and drop functionality
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });

        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelection(files[0]);
            }
        });

        // File selection handling
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0]);
            }
        });
    }
}

// Handle file selection
function handleFileSelection(file) {
    const fileName = document.querySelector('#fileName');
    const fileSize = document.querySelector('#fileSize');
    const processBtn = document.querySelector('#processBtn');

    if (fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);

        // Validate file type
        if (file.type === 'application/pdf') {
            if (processBtn) {
                processBtn.disabled = false;
                processBtn.classList.remove('btn-outline-primary');
                processBtn.classList.add('btn-primary');
            }
        } else {
            showAlert('Please select a PDF file', 'danger');
            if (processBtn) {
                processBtn.disabled = true;
            }
        }
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize forms
function initializeForms() {
    // Login form - let it submit normally to Django view
    const loginForm = document.querySelector('#loginForm');
    if (loginForm) {
        // Remove any existing event listeners and let form submit normally
        loginForm.removeEventListener('submit', handleLoginForm);
    }

    // All other forms should submit normally to Django views
    // Remove any API-related form handling
}

// Copy token to clipboard
function copyToken(token) {
    navigator.clipboard.writeText(token).then(() => {
        showAlert('Token copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy token', 'danger');
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.appendChild(alert);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Logout function - use Django session logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Use Django logout
        window.location.href = '/logout/';
    }
}

// Delete user (admin function) - placeholder for future implementation
function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        // This would be implemented as Django form submission
        showAlert('User deletion functionality will be implemented via Django forms', 'info');
    }
}

// Revoke token - placeholder for future implementation
function revokeToken(tokenId) {
    if (confirm('Are you sure you want to revoke this token?')) {
        // This would be implemented as Django form submission
        showAlert('Token revocation functionality will be implemented via Django forms', 'info');
    }
}

// Filter services dropdown
function filterServices() {
    const searchInput = document.getElementById('servicesSearch');
    const dropdown = document.getElementById('servicesDropdown');
    const items = dropdown.querySelectorAll('.dropdown-item');
    const dividers = dropdown.querySelectorAll('.dropdown-divider');

    if (!searchInput) return;

    const searchTerm = searchInput.value.toLowerCase();

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const listItem = item.closest('li');

        if (text.includes(searchTerm)) {
            listItem.style.display = 'block';
        } else {
            listItem.style.display = 'none';
        }
    });

    // Show/hide dividers based on visible items
    dividers.forEach(divider => {
        const listItem = divider.closest('li');
        const nextItem = listItem.nextElementSibling;
        const prevItem = listItem.previousElementSibling;

        // Hide divider if next or previous item is hidden
        if (nextItem && nextItem.style.display === 'none' ||
            prevItem && prevItem.style.display === 'none') {
            listItem.style.display = 'none';
        } else {
            listItem.style.display = 'block';
        }
    });
} 