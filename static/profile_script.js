document.addEventListener("DOMContentLoaded", function () {
    const saveBtn = document.querySelector(".save-btn");
    
    saveBtn.addEventListener("click", function () {
        const firstName = document.getElementById("first-name").value.trim();
        const lastName = document.getElementById("last-name").value.trim();
        const department = document.getElementById("department").value.trim();
        const email = document.getElementById("email").value.trim();

        // Validate required fields
        if (!firstName || !lastName || !department || !email) {
            alert("Please fill all required fields: First Name, Last Name, Department, and Email");
            return;
        }

        const formData = new FormData();
        formData.append("first_name", firstName);
        formData.append("last_name", lastName);
        formData.append("department", department);
        formData.append("email", email);
        
        // Get privacy value before appending
        const privacy = document.getElementById("privacy").value;
        formData.append("privacy", privacy);
        
        // Handle files
        const resumeFile = document.getElementById("resume-upload").files[0];
        const avatarFile = document.getElementById("avatar-upload").files[0];
        
        if (resumeFile) formData.append("resume", resumeFile);
        if (avatarFile) formData.append("avatar", avatarFile);

        // Handle skills
        const skillElements = document.querySelectorAll("#skills-list .skill");
        const skills = [];
        skillElements.forEach(skillEl => {
            const name = skillEl.querySelector(".skill-name").value.trim();
            const percentage = skillEl.querySelector(".skill-slider").value;
            if (name) {
                skills.push({ name, percentage: parseInt(percentage) });
            }
        });
        formData.append("skills", JSON.stringify(skills));

        // Disable button during submission
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";

        fetch("/profile", {
            method: "POST",
            body: formData
        })
        .then(res => {
            if (!res.ok) {
                throw new Error("Network response was not ok");
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                // Update displayed info
                document.getElementById("display-name").textContent = `${firstName} ${lastName}`;
                document.getElementById("display-location").textContent = department;
                document.getElementById("display-company").textContent = email;
                
                // Update avatar preview if new one was uploaded
                if (avatarFile) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById("preview").src = e.target.result;
                    }
                    reader.readAsDataURL(avatarFile);
                }
                alert("Profile updated successfully!");
            } else {
                throw new Error(data.message || "Failed to save profile");
            }
        })
        .catch(err => {
            console.error("Error:", err);
            alert(err.message || "Failed to save profile. Please try again.");
        })
        .finally(() => {
            saveBtn.disabled = false;
            saveBtn.textContent = "Save";
        });
    });
    document.getElementById("add-skill").addEventListener("click", function () {
        const skillDivs = document.querySelectorAll(".skill-name");
        for (let input of skillDivs) {
            if (!input.value.trim()) {
                alert("Please fill in all existing skill names before adding a new one.");
                return;
            }
        }
        const skillList = document.getElementById("skills-list");
        const skillDiv = document.createElement("div");
        skillDiv.className = "skill";
        skillDiv.innerHTML = `
            <input type="text" class="skill-name" placeholder="Skill Name">
            <input type="range" class="skill-slider" min="0" max="100" value="50">
            <span class="percentage">50%</span>
            <button class="delete-skill">❌</button>
        `;
        skillList.appendChild(skillDiv);
    });
    document.getElementById("skills-list").addEventListener("input", function (e) {
        if (e.target.classList.contains("skill-slider")) {
            const percentageSpan = e.target.nextElementSibling;
            percentageSpan.textContent = `${e.target.value}%`;
        }
    });
    document.addEventListener("click", function(e) {
        if (e.target.classList.contains("delete-skill")) {
            const skillDiv = e.target.closest(".skill");
            if (skillDiv) {
                skillDiv.remove();
            }
        }
    });
    document.getElementById("notification-bell").addEventListener("click", (e) => {
        e.stopPropagation();
        const notificationBox = document.getElementById("notification-box");
        notificationBox.classList.toggle("hidden");
        fetch('/get_notifications')
            .then(response => response.json())
            .then(notifications => {
                const box = document.getElementById("notification-box");
                if (notifications.length === 0) {
                    box.innerHTML = "<p>No new notifications</p>";
                    return;
                }
                box.innerHTML = notifications.map(n => 
                    `<div class="notification-item">
                        <p>${n.message}</p>
                        <small>${new Date(n.created_at).toLocaleString()}</small>
                    </div>`
                ).join('');
            });
    });
    document.addEventListener("click", () => {
        const box = document.getElementById("notification-box");
        if (box && !box.classList.contains("hidden")) {
            box.classList.add("hidden");
        }
    });
    document.getElementById("my-sessions").addEventListener("click", () => {
        alert("📅 Displaying your active sessions...");
        fetch("/log_sidebar_action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ section: "sessions", timestamp: new Date().toISOString() })
        });
    });
    const roleElement = document.querySelector(".setting-select[readonly]");
    if (roleElement && roleElement.value === "Alumni") {
        loadConnectionRequests();
    }
});
function loadConnectionRequests() {
    fetch('/get_connection_requests')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(requests => {
            const container = document.getElementById('requests-container');
            
            if (!container) return;
            
            if (requests.length === 0) {
                container.innerHTML = '<p>No pending connection requests</p>';
                return;
            }
            
            container.innerHTML = '';
            
            requests.forEach(request => {
                const card = document.createElement('div');
                card.className = 'request-card';
                card.innerHTML = `
                    <div>
                        <h4>${request.fullname}</h4>
                        <p>Sent on ${new Date(request.created_at).toLocaleDateString()}</p>
                    </div>
                    <div class="request-actions">
                        <button class="accept-btn" onclick="handleRequest(${request.id}, 'accept')">Accept</button>
                        <button class="reject-btn" onclick="handleRequest(${request.id}, 'reject')">Reject</button>
                    </div>
                `;
                container.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Error loading connection requests:', error);
            const container = document.getElementById('requests-container');
            if (container) {
                container.innerHTML = '<p>Error loading connection requests</p>';
            }
        });
}

function handleRequest(senderId, action) {
    fetch('/handle_connection_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            sender_id: senderId,
            action: action
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`Request ${action}ed successfully!`);
            loadConnectionRequests();
            // Reload connections if accepted
            if (action === 'accept') {
                // You might want to refresh the connections list here
                // or just reload the page
                location.reload();
            }
        } else {
            alert(data.message || 'Failed to process request');
        }
    })
    .catch(error => {
        console.error('Error handling request:', error);
        alert('Error processing request. Please try again.');
    });
}
document.addEventListener("input", function (e) {
    if (e.target.classList.contains("skill-slider")) {
        e.target.nextElementSibling.textContent = e.target.value + "%";
    }
});
document.getElementById("my-connections").addEventListener("click", () => {
    // Scroll to connections section instead of showing alert
    document.querySelector(".connections-section").scrollIntoView({ behavior: 'smooth' });
    
    fetch("/log_sidebar_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "connections", timestamp: new Date().toISOString() })
    });
});

function isValidDateTime(dtString) {
    return !isNaN(Date.parse(dtString));
}
