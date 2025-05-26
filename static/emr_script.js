function showNotification(title, message, type = 'info') {
    console.log(`[DEBUG] Creating notification: ${title} - ${message}`);
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="close-btn">&times;</span>
        <strong>${title}</strong>
        <p>${message}</p>
    `;
    
    const notificationArea = document.getElementById('notification-area');
    if (!notificationArea) {
        console.error("[CRITICAL] Notification area element not found!");
        return;
    }
    
    // Add click handler for close button
    notification.querySelector('.close-btn').addEventListener('click', () => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    });
    
    notificationArea.appendChild(notification);
    console.log("[DEBUG] Notification added to DOM");
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    }, 5000);
}
// ====================== EVENT HANDLERS ======================
function handleViewDetails(event) {
    if (event.target.classList.contains('event-details')) {
        console.log("[DEBUG] View Details button clicked");
        const eventCard = event.target.closest('.event-card');
        
        if (eventCard && eventCard.dataset.eventData) {
            try {
                const eventData = JSON.parse(eventCard.dataset.eventData);
                console.log("[DEBUG] Event data:", eventData);
                
                const queryParams = new URLSearchParams({
                    type: 'db',
                    id: eventData.id,
                    title: eventData.title,
                    date: new Date(eventData.start_time).toLocaleDateString(),
                    location: eventData.location,
                    description: eventData.description || 'No description'
                });
                
                window.location.href = `eventdetails?${queryParams.toString()}`;
            } catch (e) {
                console.error("[ERROR] Parsing event data:", e);
            }
        }
    }
}

// ====================== EVENT MANAGEMENT ======================
async function fetchEvents() {
    try {
        console.log("[DEBUG] Fetching events from /api/events");
        const response = await fetch('/api/events');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const events = await response.json();
        console.log("[DEBUG] Received events:", events.length);
        return events;
    } catch (error) {
        console.error("[ERROR] Fetching events:", error);
        showNotification("Error", "Could not load events", "error");
        return [];
    }
}

async function renderDatabaseEvents() {
    console.log("[DEBUG] Rendering events...");
    const events = await fetchEvents();
    const container = document.getElementById('eventsContainer');
    
    if (!container) {
        console.error("[CRITICAL] eventsContainer not found!");
        return;
    }
    
    container.innerHTML = '';
    
    events.forEach(event => {
        const eventCard = document.createElement('div');
        eventCard.className = 'event-card';
        
        const eventDate = new Date(event.start_time).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        eventCard.innerHTML = `
            <img src="/static/images/eventicon.png" alt="Event Image">
            <div class="event-info">
                <h3>${event.title}</h3>
                <p>Date: ${eventDate}</p>
                <p>Location: ${event.location}</p>
                <button class="event-details" data-event-id="${event.id}">View Details</button>
            </div>
        `;
        
        // Store full event data
        eventCard.dataset.eventData = JSON.stringify({
            id: event.id,
            title: event.title,
            start_time: event.start_time,
            location: event.location,
            description: event.description
        });
        
        container.appendChild(eventCard);
    });
    
    console.log("[DEBUG] Events rendered:", events.length);
}

// ====================== CANCELLED EVENTS CHECK ======================
async function checkCancelledEvents() {
    console.log("[DEBUG] Checking for cancelled events...");
    
    try {
        const response = await fetch('/api/events/cancelled-for-user', {
            credentials: 'include' // Ensure cookies are sent
        });
        
        console.log("[DEBUG] Response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const cancelledEvents = await response.json();
        console.log("[DEBUG] Cancelled events received:", cancelledEvents);
        
        if (cancelledEvents.length > 0) {
            console.log(`[DEBUG] Found ${cancelledEvents.length} cancelled events`);
            cancelledEvents.forEach(event => {
                const eventDate = new Date(event.start_time).toLocaleDateString();
                showNotification(
                    `Event Cancelled: ${event.title}`,
                    `Was scheduled for ${eventDate} at ${event.location}`
                );
            });
        } else {
            console.log("[DEBUG] No cancelled events found for this user");
        }
    } catch (error) {
        console.error("[ERROR] Checking cancelled events:", error);
    
    }
}

// ====================== INITIALIZATION ======================
document.addEventListener("DOMContentLoaded", function() {
    console.log("[DEBUG] DOM fully loaded - initializing...");
    setupSearch();
  
    // 3. Set up event listeners
    document.addEventListener('click', handleViewDetails);
    console.log("[DEBUG] Event listeners set up"); 
    
    // 4. Load and display events
    renderDatabaseEvents();
    
    // 5. Check for cancelled events immediately
    checkCancelledEvents();  
    
    // 6. Check for event reminders immediately
    checkEventReminders();
    
    // 7. Set up periodic checking (every 30 seconds)
    setInterval(checkCancelledEvents, 30000);
    setInterval(checkEventReminders, 30000);
    
    console.log("[DEBUG] Initialization complete");
});

// ====================== DEBUG HELPERS ======================
// Temporary function to test notifications manually
window.debugShowNotification = function() {
    showNotification(
        "Manual Test",
        "This is a manually triggered notification",
        "info"
    );
};

async function checkEventReminders() {
    console.log("[DEBUG] Checking for event reminders...");
    
    try {
        const response = await fetch('/api/events/reminders', {
            credentials: 'include'
        });
        
        console.log("[DEBUG] Reminders response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reminders = await response.json();
        console.log("[DEBUG] Reminders received:", reminders);
        
        if (reminders.length > 0) {
            console.log(`[DEBUG] Found ${reminders.length} event reminders`);
            
            reminders.forEach(reminder => {
                // Only show if not already shown for this event
                if (!localStorage.getItem(`reminder_shown_${reminder.id}`)) {
                    showNotification(
                        `Reminder: ${reminder.title}`,
                        `Happening tomorrow at ${reminder.time} in ${reminder.location}`,
                        "info"
                    );
                    // Mark as shown to prevent duplicates
                    localStorage.setItem(`reminder_shown_${reminder.id}`, 'true');
                }
            });
        } else {
            console.log("[DEBUG] No event reminders found for this user");
        }
    } catch (error) {
        console.error("[ERROR] Checking event reminders:", error);
        showNotification(
            "System Error",
            "Could not check for event reminders",
            "error"
        );
    }
}

// ====================== SEARCH FUNCTIONALITY ======================
function setupSearch() {
    const searchBar = document.getElementById('searchBar');
    
    searchBar.addEventListener('input', async function() {
        const searchTerm = this.value.toLowerCase();
        const events = await fetchEvents();
        
        if (!searchTerm) {
            renderDatabaseEvents(); // Show all events if search is empty
            return;
        }
        
        const filteredEvents = events.filter(event => {
            return (
                event.title.toLowerCase().startsWith(searchTerm) || 
                event.location.toLowerCase().startsWith(searchTerm) ||
                event.description?.toLowerCase().startsWith(searchTerm)
            );
        });
        
        renderFilteredEvents(filteredEvents);
    });
}

function renderFilteredEvents(events) {
    const container = document.getElementById('eventsContainer');
    
    if (!container) {
        console.error("[CRITICAL] eventsContainer not found!");
        return;
    }
    
    container.innerHTML = '';
    
    events.forEach(event => {
        const eventCard = document.createElement('div');
        eventCard.className = 'event-card';
        
        const eventDate = new Date(event.start_time).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        eventCard.innerHTML = `
            <img src="/static/images/eventicon.png" alt="Event Image">
            <div class="event-info">
                <h3>${event.title}</h3>
                <p>Date: ${eventDate}</p>
                <p>Location: ${event.location}</p>
                <button class="event-details" data-event-id="${event.id}">View Details</button>
            </div>
        `;
        
        eventCard.dataset.eventData = JSON.stringify({
            id: event.id,
            title: event.title,
            start_time: event.start_time,
            location: event.location,
            description: event.description
        });
        
        container.appendChild(eventCard);
    });
}