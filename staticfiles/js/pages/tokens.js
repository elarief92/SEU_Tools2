/**
 * Tokens Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTokenHandlers();
});

function initializeTokenHandlers() {
    // Copy token functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="copy-token"]')) {
            const button = e.target.closest('[data-action="copy-token"]');
            const token = button.dataset.token;
            copyToken(token, button);
        }
    });
    
    // Refresh page
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="refresh"]')) {
            location.reload();
        }
    });
}

function copyToken(token, button) {
    if (!token) return;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(token).then(function() {
            console.log('Token copied');
        });
    } else {
        const textArea = document.createElement('textarea');
        textArea.value = token;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}
