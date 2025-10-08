/**
 * History Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeHistoryHandlers();
});

function initializeHistoryHandlers() {
    // Refresh page
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="refresh"]')) {
            location.reload();
        }
    });
    
    // View details
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="view-details"]')) {
            const recordId = e.target.closest('[data-action="view-details"]').dataset.recordId;
            viewDetails(recordId);
        }
    });
    
    // Download result
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="download-result"]')) {
            const recordId = e.target.closest('[data-action="download-result"]').dataset.recordId;
            downloadResult(recordId);
        }
    });
}

function viewDetails(recordId) {
    console.log('View details for record:', recordId);
    // Add modal logic here
}

function downloadResult(recordId) {
    console.log('Download result for record:', recordId);
    // Add download logic here
}
