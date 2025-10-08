/**
 * Admin Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminHandlers();
});

function initializeAdminHandlers() {
    // Refresh dashboard
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="refresh-dashboard"]')) {
            refreshDashboard();
        }
    });
    
    // Edit user
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="edit-user"]')) {
            const userId = e.target.closest('[data-action="edit-user"]').dataset.userId;
            editUser(userId);
        }
    });
    
    // Delete user
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="delete-user"]')) {
            const userId = e.target.closest('[data-action="delete-user"]').dataset.userId;
            deleteUser(userId);
        }
    });
    
    // Revoke expired tokens
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="revoke-expired-tokens"]')) {
            revokeExpiredTokens();
        }
    });
    
    // Revoke token
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="revoke-token"]')) {
            const tokenId = e.target.closest('[data-action="revoke-token"]').dataset.tokenId;
            revokeToken(tokenId);
        }
    });
}

function refreshDashboard() {
    location.reload();
}

function editUser(userId) {
    console.log('Edit user:', userId);
    // Add modal or redirect logic here
}

function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        console.log('Delete user:', userId);
        // Add deletion logic here
    }
}

function revokeExpiredTokens() {
    if (confirm('Are you sure you want to revoke all expired tokens?')) {
        console.log('Revoking expired tokens');
        // Add revocation logic here
    }
}

function revokeToken(tokenId) {
    if (confirm('Are you sure you want to revoke this token?')) {
        console.log('Revoke token:', tokenId);
        // Add revocation logic here
    }
}
