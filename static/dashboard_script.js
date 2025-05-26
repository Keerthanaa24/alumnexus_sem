document.addEventListener("DOMContentLoaded", function () {
    // =============================================
    // 1. SIDEBAR TOGGLE FOR MOBILE
    // =============================================
    const sidebar = document.querySelector(".sidebar");
    const toggleBtn = document.createElement("button");

    toggleBtn.innerText = "☰";
    toggleBtn.classList.add("sidebar-toggle");
    document.body.insertBefore(toggleBtn, sidebar);

    toggleBtn.addEventListener("click", function () {
        sidebar.style.left = (sidebar.style.left === "0px") ? "-250px" : "0px";
    });

    // =============================================
    // 2. ADMIN DASHBOARD MODAL
    // =============================================
    const adminLink = document.getElementById('adminDashboardLink');
    const modal = document.getElementById('adminModal');
    const closeBtn = document.querySelector('.close-modal');
    const submitBtn = document.getElementById('submitKey');
    const keyError = document.getElementById('keyError');
    
    if (adminLink && modal) {
        adminLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Admin button clicked - showing modal");
            modal.style.display = 'block';
        });
    } else {
        console.error("Admin modal elements not found - check your IDs");
    }
    
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
            if (keyError) keyError.style.display = 'none';
        });
    }
    
    if (submitBtn) {
        submitBtn.addEventListener('click', verifySecurityKey);
    }
    
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            if (keyError) keyError.style.display = 'none';
        }
    });

    async function verifySecurityKey() {
        const keyInput = document.getElementById('securityKey');
        if (!keyInput) return;
        
        try {
            const response = await fetch('/verify-admin-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    key: keyInput.value
                })
            });
            
            const data = await response.json();
            
            if (data.valid) {
                // Clear the modal state before redirecting
                modal.style.display = 'none';
                keyInput.value = '';
                if (keyError) keyError.style.display = 'none';
                
                // Use replace instead of href to prevent back button issues
                window.location.replace('/admin');
            } else if (keyError) {
                keyError.style.display = 'block';
            }
        } catch (error) {
            console.error('Error verifying key:', error);
            if (keyError) keyError.style.display = 'block';
        }
    }
    
    // Update the close button event handler:
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Add this line
            modal.style.display = 'none';
            if (keyError) keyError.style.display = 'none';
        });
    }
    

    // =============================================
    // 3. NOTIFICATION SYSTEM
    // =============================================
    document.getElementById("notifyBtn").addEventListener("click", async function () {
        try {
            const response = await fetch('/api/notifications');
            
            if (!response.ok) {
                alert("No new notifications");
                return;
            }
            
            const notifications = await response.json();
            
            if (!notifications || notifications.length === 0) {
                alert("No new notifications at the moment!");
                return;
            }
            
            // Check if popup already exists
            const existingPopup = document.querySelector('.notification-popup');
            if (existingPopup) {
                existingPopup.remove();
                return;
            }
            
            const popup = document.createElement('div');
            popup.className = 'notification-popup';
            
            popup.innerHTML = `
                <div class="notification-header">
                    <strong class="notification-title">Notifications</strong>
                    <button class="notification-close">×</button>
                </div>
                <div class="notification-body">
                    ${notifications.map(n => `
                        <div class="notification-item ${n.read ? 'read' : 'unread'}">
                            ${n.message}
                            <div class="notification-time">${formatTime(n.created_at)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            document.body.appendChild(popup);
            
            // Add click handler for the close button
            const closeBtn = popup.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => {
                fetch('/api/notifications/mark-read', { method: 'POST' });
                popup.remove();
            });
            
        } catch (error) {
            console.error('Notification error:', error);
            alert("Error loading notifications");
        }
    });
    
    // Helper function to format time
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // =============================================
    // 4. QUICK ACTIONS
    // =============================================
    document.getElementById("connectAlumni").addEventListener("click", function () {
        window.location.href = "/alunet";
    });

    document.getElementById("successStoriesBtn").addEventListener("click", function () {
        window.location.href = "/success_stories";
    });
    
    document.getElementById("createEvent").addEventListener("click", function () {
        window.location.href = "/events";
    });
});