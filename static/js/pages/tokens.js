/**
 * Tokens Page JavaScript
 * Handles copy functionality for API tokens with DataTables compatibility
 */

// Wait for DOM and all scripts to load
$(document).ready(function () {
    // Initialize token handlers after a short delay to ensure DataTables is ready
    setTimeout(function () {
        initializeTokenHandlers();
    }, 100);
});

function initializeTokenHandlers() {
    console.log('Initializing token handlers...');

    // Use event delegation to handle clicks on copy buttons
    // This works even after DataTables processes the table
    $(document).on('click', '[data-action="copy-token"]', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const button = $(this);
        const token = button.data('token');

        console.log('Table copy button clicked, token:', token ? 'present' : 'missing');

        if (token) {
            copyTokenWithFeedback(token, button[0]);
        } else {
            console.error('No token found in button data');
        }
    });

    // Handle new token modal copy button
    $(document).on('click', '[data-action="copy-new-token"]', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const button = $(this);
        const tokenInput = $('#newTokenDisplay');
        const token = tokenInput.val();

        console.log('Modal copy button clicked, token:', token ? 'present' : 'missing');

        if (token) {
            copyTokenWithFeedback(token, button[0]);
        } else {
            console.error('No token found in input field');
        }
    });

    // Handle refresh button
    $(document).on('click', '[data-action="refresh"]', function (e) {
        e.preventDefault();
        window.location.reload();
    });

    console.log('Token handlers initialized successfully');
}

function copyTokenWithFeedback(token, buttonElement) {
    console.log('Starting copy operation...');

    if (!token) {
        console.error('No token provided for copy operation');
        return;
    }

    const $button = $(buttonElement);
    const originalHtml = $button.html();
    const originalClass = $button.attr('class');

    // Function to update button appearance
    function updateButton(success) {
        if (success) {
            $button.html('<i class="fas fa-check"></i>')
                .removeClass('btn-outline-secondary btn-outline-primary')
                .addClass('btn-success');
            showAlert('Token copied to clipboard!', 'success');
            console.log('Copy successful');
        } else {
            $button.html('<i class="fas fa-times"></i>')
                .removeClass('btn-outline-secondary btn-outline-primary')
                .addClass('btn-danger');
            console.log('Copy failed');
        }

        // Restore original button after 2 seconds
        setTimeout(function () {
            $button.html(originalHtml).attr('class', originalClass);
        }, 2000);
    }

    // Try modern Clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
        console.log('Using modern Clipboard API...');
        navigator.clipboard.writeText(token)
            .then(function () {
                updateButton(true);
            })
            .catch(function (err) {
                console.warn('Clipboard API failed:', err);
                copyTokenFallback(token, updateButton);
            });
    } else {
        console.log('Using fallback copy method...');
        copyTokenFallback(token, updateButton);
    }
}

function copyTokenFallback(token, callback) {
    try {
        // Create temporary textarea
        const $textarea = $('<textarea>')
            .val(token)
            .css({
                position: 'fixed',
                left: '-9999px',
                top: '-9999px',
                opacity: 0
            })
            .appendTo('body');

        // Select and copy
        $textarea[0].focus();
        $textarea[0].select();
        $textarea[0].setSelectionRange(0, token.length);

        const successful = document.execCommand('copy');
        $textarea.remove();

        if (successful) {
            callback(true);
        } else {
            throw new Error('execCommand copy failed');
        }

    } catch (err) {
        console.error('All copy methods failed:', err);
        callback(false);

        // Show manual copy modal as last resort
        showTokenForManualCopy(token);
    }
}

function showTokenForManualCopy(token) {
    const modalHtml = `
        <div class="modal fade" id="manualCopyModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-copy me-2"></i>Manual Copy Required
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Automatic copy failed. Please manually copy the token below:
                        </div>
                        <div class="mb-3">
                            <label for="manualCopyInput" class="form-label">Token:</label>
                            <div class="input-group">
                                <input type="text" class="form-control" id="manualCopyInput" value="${token}" readonly>
                                <button class="btn btn-outline-primary" type="button" onclick="selectTokenText()">
                                    <i class="fas fa-mouse-pointer"></i> Select All
                                </button>
                            </div>
                        </div>
                        <p class="text-muted">
                            <small>
                                <i class="fas fa-info-circle me-1"></i>
                                Select the text above and press <kbd>Ctrl+C</kbd> (or <kbd>Cmd+C</kbd> on Mac) to copy.
                            </small>
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            I've copied the token
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    $('#manualCopyModal').remove();

    // Add modal to page
    $('body').append(modalHtml);

    // Show modal and setup events
    const $modal = $('#manualCopyModal');
    $modal.modal('show');

    // Auto-select token text when modal is shown
    $modal.on('shown.bs.modal', function () {
        const input = document.getElementById('manualCopyInput');
        if (input) {
            input.focus();
            input.select();
            input.setSelectionRange(0, input.value.length);
        }
    });

    // Clean up modal when hidden
    $modal.on('hidden.bs.modal', function () {
        $(this).remove();
    });
}

// Helper function for manual copy modal
function selectTokenText() {
    const input = document.getElementById('manualCopyInput');
    if (input) {
        input.focus();
        input.select();
        input.setSelectionRange(0, input.value.length);
    }
}

function showAlert(message, type) {
    // Convert error to danger for Bootstrap
    if (type === 'error') type = 'danger';

    const iconMap = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };

    const icon = iconMap[type] || 'info-circle';

    const alertHtml = `
        <div class="position-fixed top-0 end-0 p-3" style="z-index: 1060;">
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        </div>
    `;

    const $alert = $(alertHtml).appendTo('body');

    // Auto-dismiss after 4 seconds
    setTimeout(function () {
        $alert.fadeOut(function () {
            $(this).remove();
        });
    }, 4000);
}

// Global function for new token display (called from template)
window.displayNewToken = function (token, tokenName) {
    $('#newTokenDisplay').val(token);

    const newTokenModal = new bootstrap.Modal(document.getElementById('newTokenModal'));
    newTokenModal.show();

    const createTokenModal = bootstrap.Modal.getInstance(document.getElementById('createTokenModal'));
    if (createTokenModal) {
        createTokenModal.hide();
    }

    showAlert(`Token "${tokenName}" created successfully!`, 'success');
};

// Debug function to test copy functionality
window.testCopy = function () {
    console.log('Testing copy functionality...');
    copyTokenWithFeedback('test-token-12345', document.querySelector('[data-action="copy-token"]'));
};
