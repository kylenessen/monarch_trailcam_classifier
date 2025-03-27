// --- Module State ---
let isZooming = false;
const zoomLevel = 3; // 300% zoom

// --- DOM Element References ---
// We need references to the elements involved in zooming.
// These could be passed during initialization or queried directly.
let imageContainer = null; 
let imageWrapper = null; 

// --- Initialization ---

/**
 * Initializes the zoom functionality by setting up event listeners.
 */
export function initializeZoom() {
    // Cache elements
    imageContainer = document.getElementById('image-container');
    // imageWrapper is dynamically created, so we'll get it inside the event handlers

    // Add event listeners to the document
    document.addEventListener('keydown', handleZoomKeyDown);
    document.addEventListener('keyup', handleZoomKeyUp);
    // Attach mousemove to the container where zooming happens
    if (imageContainer) {
        imageContainer.addEventListener('mousemove', updateZoomPosition);
    } else {
        console.error("Zoom initialization failed: image-container not found.");
    }
    console.log('Zoom functionality initialized.');
}

// --- Event Handlers ---

function handleZoomKeyDown(event) {
    // Ignore if typing in input/textarea or if not spacebar
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.key !== ' ' || isZooming) {
        return;
    }
    
    // Check if there's an image loaded
    imageWrapper = imageContainer?.querySelector('.image-wrapper'); // Get current wrapper
    if (!imageWrapper || !imageContainer) return; 

    event.preventDefault(); // Prevent spacebar default action (scrolling)
    isZooming = true;
    imageWrapper.classList.add('zoomed'); // Add class for potential styling
    // Initial position update based on current mouse position relative to container
    updateZoomPosition(event); 
}

function handleZoomKeyUp(event) {
    // Ignore if not spacebar or not currently zooming
    if (event.key !== ' ' || !isZooming) {
        return;
    }
    
    event.preventDefault();
    isZooming = false;
    
    // imageWrapper should still hold the reference from keydown
    if (imageWrapper) {
        imageWrapper.classList.remove('zoomed');
        // Reset transform
        imageWrapper.style.transformOrigin = 'center center'; // Reset origin
        imageWrapper.style.transform = 'none'; // Remove scale
    }
}

function updateZoomPosition(event) {
    if (!isZooming || !imageWrapper || !imageContainer) return;

    const rect = imageContainer.getBoundingClientRect();
    
    // Calculate mouse position relative to the container
    // Use clientX/clientY as they are relative to the viewport
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    // Ensure mouse coordinates are within the bounds of the container
    const boundedX = Math.max(0, Math.min(mouseX, rect.width));
    const boundedY = Math.max(0, Math.min(mouseY, rect.height));

    // Calculate position as percentage of container dimensions
    const xPercent = (boundedX / rect.width) * 100;
    const yPercent = (boundedY / rect.height) * 100;

    // Set the transform origin and apply the scale
    imageWrapper.style.transformOrigin = `${xPercent}% ${yPercent}%`;
    imageWrapper.style.transform = `scale(${zoomLevel})`;
}

// Optional: Function to reset zoom state if the image changes while zooming
export function resetZoomState() {
     if (isZooming && imageWrapper) {
         imageWrapper.classList.remove('zoomed');
         imageWrapper.style.transformOrigin = 'center center';
         imageWrapper.style.transform = 'none';
     }
    isZooming = false;
    imageWrapper = null; // Clear reference
}
