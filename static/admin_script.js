document.addEventListener("DOMContentLoaded", function () {
    console.log("Admin script loaded"); // Debugging check
    // ✅ Highlight Active Link in Sidebar
    const currentPage = window.location.pathname.split("/").pop() || "admin.html";
    document.querySelectorAll(".sidebar a").forEach(link => {
        if (link.href.includes(currentPage)) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
    
    // ✅ Logout Functionality
    const logoutButton = document.getElementById("logout");
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            if (confirm("Are you sure you want to log out?")) {
                alert("Logged out successfully.");
                window.location.href = "login.html";
            }
        });
    }
    
    // ✅ Website Analytics (Chart.js)
    const ctx = document.getElementById("userChart")?.getContext("2d");
    if (ctx) {
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Users", "Active Sessions", "New Posts"],
                datasets: [{
                    label: "Website Analytics",
                    data: [120, 15, 8], // Replace with actual backend data
                    backgroundColor: ["#3498db", "#2ecc71", "#f1c40f"],
                    borderColor: "#333",
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true } }
            }
        });
    }
    
    // ✅ Load User Submissions (Sample Data)
    const submissions = [
        { id: 1, content: "User post about technology" },
        { id: 2, content: "User blog on AI advancements" },
        { id: 3, content: "Review on latest software update" }
    ];
    const userSubmissionsTable = document.getElementById("userSubmissions");
    if (userSubmissionsTable) {
        userSubmissionsTable.innerHTML = submissions.map(submission => `
            <tr>
                <td>${submission.content}</td>
                <td>
                    <button class="btn-approve" data-id="${submission.id}">Approve</button>
                    <button class="btn-remove" data-id="${submission.id}">Remove</button>
                </td>
            </tr>`).join("");
    }
    
    // ✅ Event Delegation for Content Actions
    document.body.addEventListener("click", function (e) {
        if (e.target.classList.contains("btn-approve")) {
            alert(`Content approved: ${e.target.dataset.id}`);
        } else if (e.target.classList.contains("btn-remove")) {
            alert(`Content removed: ${e.target.dataset.id}`);
            e.target.closest("tr").remove();
        }
    });
    
    // ✅ Job Applications (Sample Data)
    const applications = [
        { name: "John Doe", email: "john@example.com", job: "Software Engineer" },
        { name: "Jane Smith", email: "jane@example.com", job: "Product Manager" }
    ];
    const applicationList = document.getElementById("applicationList");
    if (applicationList) {
        applicationList.innerHTML = applications.map(app => `
            <tr>
                <td>${app.name}</td>
                <td>${app.email}</td>
                <td>${app.job}</td>
            </tr>`).join("");
    }
    
    // ✅ Job Listings Management (Sample Data)
    const jobListings = document.getElementById("jobListings");
    let jobs = JSON.parse(localStorage.getItem("jobs")) || [
        { title: "Software Engineer", company: "TechCorp", location: "New York", postedBy: "Recruiter A" },
        { title: "Data Analyst", company: "Data Inc.", location: "San Francisco", postedBy: "Recruiter B" },
        { title: "UX Designer", company: "DesignHub", location: "Los Angeles", postedBy: "Recruiter C" }
    ];
    function renderJobs() {
        if (jobListings) {
            jobListings.innerHTML = jobs.map((job, index) => `
                <tr>
                    <td>${job.title}</td>
                    <td>${job.company}</td>
                    <td>${job.location}</td>
                    <td>${job.postedBy}</td>
                    <td><button class="delete-job" data-index="${index}">Delete</button></td>
                </tr>`).join("");
            localStorage.setItem("jobs", JSON.stringify(jobs));
        }
    }
    renderJobs();
    
    // ✅ Delete Job Postings
    document.body.addEventListener("click", function (e) {
        if (e.target.classList.contains("delete-job")) {
            const index = e.target.dataset.index;
            if (confirm("Are you sure you want to delete this job posting?")) {
                jobs.splice(index, 1);
                renderJobs();
            }
        }
    });
    
    // ✅ Save Text Content
    const saveTextButton = document.getElementById("saveContent");
    const textEditor = document.getElementById("editor");
    if (saveTextButton && textEditor) {
        saveTextButton.addEventListener("click", function () {
            const textContent = textEditor.value.trim();
            if (textContent === "") {
                alert("Text content cannot be empty.");
                return;
            }
            localStorage.setItem("savedTextContent", textContent);
            alert("Text content saved successfully!");
        });
        // Load saved content
        const savedText = localStorage.getItem("savedTextContent");
        if (savedText) textEditor.value = savedText;
    }
    
    // ✅ Upload Image Preview
    const uploadInput = document.getElementById("uploadImage");
    const uploadBtn = document.getElementById("uploadBtn");
    const imagePreview = document.getElementById("imagePreview");
    if (uploadBtn) {
        uploadBtn.addEventListener("click", function () {
            const file = uploadInput.files[0];
            if (!file) {
                alert("Please select an image to upload.");
                return;
            }
            const reader = new FileReader();
            reader.onload = function (e) {
                imagePreview.innerHTML = `<img src="${e.target.result}" alt="Uploaded Image" style="max-width: 200px;">`;
            };
            reader.readAsDataURL(file);
        });
    }
    
    // ✅ Post Event/Job Button
    const postEventButton = document.getElementById("postEvent");
    const eventTitleInput = document.getElementById("eventTitle");
    const eventDescInput = document.getElementById("eventDesc");
    const eventList = document.getElementById("eventList");
    let events = JSON.parse(localStorage.getItem("events_admin")) || [];
    function renderEvents() {
        eventList.innerHTML = events.map((event, index) => `
            <li>
                <strong>${event.title}</strong> - ${event.desc} 
                <small>(${event.timestamp})</small> 
                <button class="delete-event" data-index="${index}">Delete</button>
            </li>
        `).join("");
    }
    if (postEventButton) {
        postEventButton.addEventListener("click", function () {
            const title = eventTitleInput.value.trim();
            const desc = eventDescInput.value.trim();

            if (title === "" || desc === "") {
                alert("Event/Job title and description cannot be empty.");
                return;
            }
            events.push({ title, desc, timestamp: new Date().toLocaleString() });
            localStorage.setItem("events_admin", JSON.stringify(events));
            renderEvents();
            eventTitleInput.value = "";
            eventDescInput.value = "";
        });
        // Delete Event
        document.body.addEventListener("click", function (e) {
            if (e.target.classList.contains("delete-event")) {
                const index = e.target.dataset.index;
                events.splice(index, 1);
                localStorage.setItem("events_admin", JSON.stringify(events));
                renderEvents();
            }
        });
        renderEvents();
    }
    
    // Load job data from backend
    fetch("/admin/job_data")
        .then(response => response.json())
        .then(data => {
            const jobListings = document.getElementById("jobListings");
            const applicationList = document.getElementById("applicationList");

            // Load job postings
            data.jobs.forEach(job => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${job.title}</td>
                    <td>${job.company}</td>
                    <td>${job.location}</td>
                    <td>${job.posted_by}</td>
                    <td><button onclick="deleteJob(${job.id})">Delete</button></td>
                `;
                jobListings.appendChild(row);
            });

            // Load job applications
            data.applications.forEach(app => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${app.applicant_name}</td>
                    <td>${app.applicant_email}</td>
                    <td>${app.job_title}</td>
                `;
                applicationList.appendChild(row);
            });
        })
        .catch(error => console.error("Error loading job data:", error));
});

// ✅ Event Management
const createEventBtn = document.getElementById("createEventBtn");
const modal = document.getElementById("eventModal");
const closeModal = document.querySelector(".close-btn");
const eventForm = document.getElementById("eventForm");
const eventTableBody = document.querySelector("#eventTable tbody");
const eventsList = document.getElementById("eventsList");

// Function to fetch events from backend
async function fetchEvents() {
    try {
        const response = await fetch('/api/events');
        if (!response.ok) throw new Error('Failed to fetch events');
        return await response.json();
    } catch (error) {
        console.error('Error fetching events:', error);
        return [];
    }
}

// Function to create a new event
async function createEvent(eventData) {
    try {
        const response = await fetch('/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData)
        });
        if (!response.ok) throw new Error('Failed to create event');
        return await response.json();
    } catch (error) {
        console.error('Error creating event:', error);
        return null;
    }
}

// Function to render events in the table
function renderEventTable(events) {
    // Add time formatting here
    events.forEach(event => {
        event.formatted_start_date = new Date(event.start_time).toLocaleDateString();
        event.formatted_start_time = new Date(event.start_time).toLocaleTimeString();
        event.formatted_end_time = new Date(event.end_time).toLocaleTimeString();
    });

    eventTableBody.innerHTML = events.map(event => `
        <tr>
            <td>${event.title}</td>
            <td>${event.formatted_start_date}</td>
            <td>${event.formatted_start_time}</td>
            <td>${event.location}</td>
            <td>${event.description}</td>
            <td>
                <button class="delete-event" data-event-id="${event.id}">Delete</button>
            </td>
        </tr>
    `).join("");
}

// Function to render events in the display section
function renderEventsDisplay(events) {
    // Add time formatting here
    events.forEach(event => {
        event.formatted_date = new Date(event.start_time).toLocaleDateString();
        event.formatted_start = new Date(event.start_time).toLocaleTimeString();
        event.formatted_end = new Date(event.end_time).toLocaleTimeString();
    });

    eventsList.innerHTML = events.map(event => `
        <div class="event-card">
            <h3>${event.title}</h3>
            <p><strong>Date:</strong> ${event.formatted_date}</p>
            <p><strong>Time:</strong> ${event.formatted_start} - ${event.formatted_end}</p>
            <p><strong>Location:</strong> ${event.location}</p>
            <p>${event.description}</p>
        </div>
    `).join("");
}

// Load and display events
async function loadEvents() {
    const events = await fetchEvents();
    renderEventTable(events);
    renderEventsDisplay(events);
}

// Initialize event management
if (createEventBtn && modal) {
    // Load existing events on page load
    document.addEventListener('DOMContentLoaded', loadEvents);

    createEventBtn.addEventListener("click", function () {
        modal.style.display = "flex";
    });
    closeModal.addEventListener("click", function () {
        modal.style.display = "none";
    });
    window.addEventListener("click", function (e) {
        if (e.target === modal) modal.style.display = "none";
    });
    eventForm.addEventListener("submit", async function (e) {
        e.preventDefault();      
        const startDateTime = new Date(`${document.getElementById("eventDate").value}T${document.getElementById("eventTime").value}`);        
        const newEvent = {
            title: document.getElementById("eventName").value,
            description: document.getElementById("eventDescription").value,
            location: document.getElementById("eventLocation").value,
            start_time: startDateTime.toISOString(),
            end_time: new Date(startDateTime.getTime() + 2 * 60 * 60 * 1000).toISOString() // Default 2 hour duration
        };
        const createdEvent = await createEvent(newEvent);
        if (createdEvent) {
            modal.style.display = "none";
            eventForm.reset();
            alert("Event added successfully!");
            loadEvents(); // Refresh the events list
        } else {
            alert("Failed to create event. Please try again.");
        }
    });
}

// Add this to your existing admin_script.js
document.addEventListener('click', async function(e) {
    if (e.target.classList.contains('delete-event')) {
        const eventId = e.target.dataset.eventId;
        if (confirm('Are you sure you want to cancel this event?')) {
            try {
                const response = await fetch(`/api/events/${eventId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    alert('Event cancelled successfully!');
                    loadEvents(); // Refresh the events list
                } else {
                    alert('Failed to cancel event');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error cancelling event');
            }
        }
    }
});

// Optional: Job deletion (requires backend route)
function deleteJob(jobId) {
    if (confirm("Are you sure you want to delete this job posting?")) {
        fetch(`/admin/delete_job/${jobId}`, { method: "DELETE" })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(err => {
                console.error("Error deleting job:", err);
                alert("Failed to delete job.");
            });
    }
}

function submitRoleRequest() {
    const requestedRole = document.getElementById('requested-role').value;
    
    // Validate the role before sending
    const allowedRoles = ['student', 'Alumni', 'faculty', 'recruiter'];
    if (!allowedRoles.includes(requestedRole)) {
        alert('Please select a valid role');
        return;
    }

    fetch('/request_role_change', {  // Make sure this matches your route
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: requestedRole })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message || "Request submitted successfully");
        } else {
            alert(data.message || "Error submitting request");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to submit request');
    });
}