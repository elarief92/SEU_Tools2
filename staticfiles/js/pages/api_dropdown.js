/**
 * API Dropdown functionality
 * Handles API endpoint interactions and testing capabilities
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeDropdowns();
});

function initializeDropdowns() {
    // Initialize APIs dropdown
    initializeApiDropdown();

    // Initialize Services dropdown
    initializeServicesDropdown();
}

function initializeApiDropdown() {
    // Add click handlers for API endpoints
    const apiLinks = document.querySelectorAll('#apisDropdown a[href*="/api/"]');

    apiLinks.forEach(link => {
        // Add tooltip to show full endpoint URL
        link.setAttribute('title', link.href);

        // Add context menu for copying URL
        link.addEventListener('contextmenu', function (e) {
            e.preventDefault();
            copyToClipboard(this.href);
            showToast('API endpoint URL copied to clipboard!', 'success');
        });

        // Add double-click to copy URL
        link.addEventListener('dblclick', function (e) {
            e.preventDefault();
            copyToClipboard(this.href);
            showToast('API endpoint URL copied to clipboard!', 'success');
        });
    });

    // Add search functionality for API endpoints
    addSearchFilter('apisDropdown', 'Search APIs...');
}

function initializeServicesDropdown() {
    // Add search functionality for Services dropdown
    addSearchFilter('servicesDropdown', 'Search Services...');
}

function addSearchFilter(dropdownId, placeholder) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    // Create search input
    const searchContainer = document.createElement('div');
    searchContainer.className = 'p-2 mb-1 border-bottom';
    searchContainer.innerHTML = `
        <div class="input-group input-group-sm">
            <span class="input-group-text">
                <i class="fas fa-search"></i>
            </span>
            <input type="text" class="form-control" placeholder="${placeholder}" id="${dropdownId}Search">
        </div>
    `;

    // Insert search at the beginning of dropdown
    dropdown.insertBefore(searchContainer, dropdown.firstChild);

    // Add search functionality
    const searchInput = document.getElementById(`${dropdownId}Search`);
    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const items = dropdown.querySelectorAll('.dropdown-item');
        const headers = dropdown.querySelectorAll('.dropdown-header');
        const dividers = dropdown.querySelectorAll('.dropdown-divider');

        // Filter items
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            const shouldShow = text.includes(searchTerm);
            item.style.display = shouldShow ? 'flex' : 'none';
        });

        // Show/hide headers based on visible items in their sections
        headers.forEach(header => {
            const section = [];
            let nextSibling = header.nextElementSibling;

            while (nextSibling && !nextSibling.classList.contains('dropdown-header')) {
                if (nextSibling.classList.contains('dropdown-item')) {
                    section.push(nextSibling);
                }
                nextSibling = nextSibling.nextElementSibling;
            }

            const hasVisibleItems = section.some(item => item.style.display !== 'none');
            header.style.display = hasVisibleItems ? 'block' : 'none';

            // Hide the divider after the header if no items are visible
            const nextDivider = header.nextElementSibling;
            while (nextDivider && !nextDivider.classList.contains('dropdown-divider') && !nextDivider.classList.contains('dropdown-header')) {
                nextDivider = nextDivider.nextElementSibling;
            }
            if (nextDivider && nextDivider.classList.contains('dropdown-divider')) {
                nextDivider.style.display = hasVisibleItems ? 'block' : 'none';
            }
        });

        // Handle dividers between sections
        dividers.forEach(divider => {
            const prevItems = [];
            const nextItems = [];

            // Get items before divider
            let prevSibling = divider.previousElementSibling;
            while (prevSibling && !prevSibling.classList.contains('dropdown-divider')) {
                if (prevSibling.classList.contains('dropdown-item')) {
                    prevItems.push(prevSibling);
                }
                prevSibling = prevSibling.previousElementSibling;
            }

            // Get items after divider
            let nextSibling = divider.nextElementSibling;
            while (nextSibling && !nextSibling.classList.contains('dropdown-divider')) {
                if (nextSibling.classList.contains('dropdown-item')) {
                    nextItems.push(nextSibling);
                }
                nextSibling = nextSibling.nextElementSibling;
            }

            const hasPrevVisible = prevItems.some(item => item.style.display !== 'none');
            const hasNextVisible = nextItems.some(item => item.style.display !== 'none');

            divider.style.display = (hasPrevVisible && hasNextVisible) ? 'block' : 'none';
        });
    });

    // Clear search when dropdown closes
    dropdown.addEventListener('hidden.bs.dropdown', function () {
        searchInput.value = '';
        const items = dropdown.querySelectorAll('.dropdown-item, .dropdown-header, .dropdown-divider');
        items.forEach(item => item.style.display = '');
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Initialize and show toast
    const bootstrapToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bootstrapToast.show();

    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

// Add keyboard shortcuts for dropdown navigation
document.addEventListener('keydown', function (e) {
    // Ctrl+Shift+A to open API dropdown
    if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        const apiDropdownToggle = document.querySelector('a[data-bs-toggle="dropdown"] i.fa-code').parentElement;
        if (apiDropdownToggle) {
            apiDropdownToggle.click();
        }
    }

    // Ctrl+Shift+S to open Services dropdown
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        const servicesDropdownToggle = document.querySelector('a[data-bs-toggle="dropdown"] i.fa-cogs').parentElement;
        if (servicesDropdownToggle) {
            servicesDropdownToggle.click();
        }
    }
});

// Export functions for external use
window.SEUTools = window.SEUTools || {};
window.SEUTools.Dropdowns = {
    copyEndpointUrl: copyToClipboard,
    showToast: showToast,
    addSearchFilter: addSearchFilter
}; 