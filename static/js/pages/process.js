/**
 * Process Page JavaScript
 * Handles file upload, processing, and result display
 */

// Global variable to store the selected file
let selectedFile = null;

// Document ready
document.addEventListener('DOMContentLoaded', function () {
    initializeFileUpload();
    initializeEventListeners();
    initializeTooltips();
    initializeFormHandling();
});

/**
 * Initialize file upload functionality
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInfo = document.getElementById('fileInfo');

    if (!fileInput || !fileUploadArea || !fileInfo) {
        console.error('Required elements not found!');
        return;
    }

    // File input change handler
    fileInput.addEventListener('change', function (e) {
        if (e.target.files[0]) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag and drop handlers for the upload area
    fileUploadArea.addEventListener('dragover', function (e) {
        e.preventDefault();
        fileUploadArea.classList.add('dragover');
    });

    fileUploadArea.addEventListener('dragleave', function (e) {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');
    });

    fileUploadArea.addEventListener('drop', function (e) {
        e.preventDefault();
        fileUploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const droppedFile = files[0];

            // Create a new DataTransfer object and assign the dropped file to the file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(droppedFile);
            fileInput.files = dataTransfer.files;

            // Handle the file selection
            handleFileSelection(droppedFile);
        }
    });
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    // Clear file button
    const clearFileBtn = document.querySelector('[data-action="clear-file"]');
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', clearFile);
    }

    // Clear results button
    const clearResultsBtn = document.querySelector('[data-action="clear-results"]');
    if (clearResultsBtn) {
        clearResultsBtn.addEventListener('click', clearResults);
    }
}

/**
 * Initialize form handling
 */
function initializeFormHandling() {
    const form = document.getElementById('processForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

/**
 * Handle file selection
 */
function handleFileSelection(file) {
    if (!file) return;

    // Get file extension
    const fileExtension = file.name.toLowerCase().split('.').pop();
    const supportedExtensions = ['pdf', 'png', 'jpg', 'jpeg'];

    // Validate file type
    if (!supportedExtensions.includes(fileExtension)) {
        showAlert('Please select a PDF or image file (PNG, JPG, JPEG).', 'error');
        clearFile();
        return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        showAlert('File size must be less than 10MB.', 'error');
        clearFile();
        return;
    }

    // Store the selected file
    selectedFile = file;

    // Display file info
    displayFileInfo(file);

    // Show file info section
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.classList.remove('file-info-hidden');
    }

    // Handle processing options based on file type
    handleProcessingOptions(fileExtension);

    // Enable submit button
    enableSubmitButton();
}

/**
 * Handle processing options based on file type
 */
function handleProcessingOptions(fileExtension) {
    const processingOptions = document.getElementById('processingOptions');
    const standardOption = document.getElementById('standard');
    const aiOption = document.getElementById('ai');

    if (!processingOptions || !standardOption || !aiOption) {
        return;
    }

    if (fileExtension === 'pdf') {
        // For PDF files, show both options and default to standard
        processingOptions.classList.remove('d-none');
        standardOption.checked = true;
        aiOption.checked = false;

        // Update the helper text
        updateProcessingHelperText('PDF files support both Standard and AI processing methods.');
    } else {
        // For image files, hide options and force AI processing
        processingOptions.classList.add('d-none');
        standardOption.checked = false;
        aiOption.checked = true;

        // Update the helper text
        updateProcessingHelperText('Image files require AI processing for text extraction.');
    }
}

/**
 * Update processing helper text
 */
function updateProcessingHelperText(message) {
    const helperText = document.getElementById('processingHelperText');
    if (helperText) {
        const textSpan = helperText.querySelector('span');
        if (textSpan) {
            textSpan.textContent = message;
        }
        helperText.classList.remove('d-none');
    }
}

/**
 * Display file information
 */
function displayFileInfo(file) {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileType = document.getElementById('fileType');
    const fileIcon = document.getElementById('fileIcon');

    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (fileType) fileType.textContent = file.type || 'application/pdf';

    // Update file icon based on file type
    if (fileIcon) {
        const fileExtension = file.name.toLowerCase().split('.').pop();
        if (fileExtension === 'pdf') {
            fileIcon.className = 'fas fa-file-pdf fa-2x text-danger';
        } else if (['png', 'jpg', 'jpeg'].includes(fileExtension)) {
            fileIcon.className = 'fas fa-file-image fa-2x text-success';
        } else {
            fileIcon.className = 'fas fa-file fa-2x text-secondary';
        }
    }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Enable submit button
 */
function enableSubmitButton() {
    const submitBtn = document.getElementById('processBtn');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-primary');
    }
}

/**
 * Disable submit button
 */
function disableSubmitButton() {
    const submitBtn = document.getElementById('processBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-secondary');
    }
}

/**
 * Clear selected file
 */
function clearFile() {
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const processingOptions = document.getElementById('processingOptions');
    const helperText = document.getElementById('processingHelperText');

    if (fileInput) {
        fileInput.value = '';
    }

    if (fileInfo) {
        fileInfo.classList.add('file-info-hidden');
    }

    if (processingOptions) {
        processingOptions.classList.remove('d-none');
    }

    if (helperText) {
        helperText.classList.add('d-none');
    }

    // Clear the stored file
    selectedFile = null;

    // Reset processing options to default
    const standardOption = document.getElementById('standard');
    const aiOption = document.getElementById('ai');
    if (standardOption) standardOption.checked = true;
    if (aiOption) aiOption.checked = false;

    // Disable submit button
    disableSubmitButton();

    showAlert('File cleared successfully.', 'success');
}

/**
 * Clear processing results
 */
function clearResults() {
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }

    showAlert('Results cleared successfully.', 'success');
}

/**
 * Handle form submission
 */
function handleFormSubmission(e) {
    const fileInput = document.getElementById('fileInput');
    const submitBtn = document.getElementById('processBtn');

    // Validate file is selected (check both file input and stored file)
    if (!selectedFile && (!fileInput || !fileInput.files || fileInput.files.length === 0)) {
        e.preventDefault();
        showAlert('Please select a file to process.', 'error');
        return false;
    }

    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    }

    // Show processing status
    showProcessingStatus();

    return true;
}

/**
 * Show processing status
 */
function showProcessingStatus() {
    const processingStatus = document.getElementById('processingStatus');
    if (processingStatus) {
        processingStatus.innerHTML = `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">
                        <i class="fas fa-spinner fa-spin me-2"></i>
                        Processing Certificate...
                    </h5>
                </div>
                <div class="card-body">
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 100%">
                            Please wait while we process your certificate...
                        </div>
                    </div>
                    <div class="text-center mt-3">
                        <small class="text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            This may take a few moments depending on the processing method selected.
                        </small>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Find container and insert alert
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
} 