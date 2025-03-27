/**
 * Displays a temporary notification message on the screen.
 * @param {string} message - The message to display.
 * @param {'info' | 'success' | 'warning' | 'error'} type - The type of notification.
 */
export function showNotification(message, type = 'info') {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Remove after delay
    setTimeout(() => {
        notification.classList.add('fade-out');
        // Wait for fade-out animation to complete before removing
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300); // Matches the CSS transition duration
    }, 3000); // Display duration
}

/**
 * Generates a unique ID for a grid cell based on its row and column.
 * @param {number} row - The row index of the cell.
 * @param {number} col - The column index of the cell.
 * @returns {string} The generated cell ID.
 */
export function generateCellId(row, col) {
    return `cell_${row}_${col}`;
}

/**
 * Validates the username input.
 * @returns {boolean} True if the username is valid, false otherwise.
 */
export function validateUsername() {
    const usernameInput = document.getElementById('username-input');
    if (!usernameInput) return false; // Should not happen, but good practice

    const username = usernameInput.value.trim();
    if (!username) {
        showNotification('Please enter your initials before confirming images', 'error');
        return false;
    }
    // Allow letters, numbers, and hyphens, up to 30 characters
    if (!/^[a-zA-Z0-9-]{1,30}$/.test(username)) {
        showNotification('Initials must be 1-30 characters and contain only letters, numbers, or hyphens.', 'error');
        return false;
    }
    return true;
}
