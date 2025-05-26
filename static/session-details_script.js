// Function to get URL query parameters
function getQueryParameter(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

document.addEventListener("DOMContentLoaded", function () {
    const mentorName = getQueryParameter("mentor") || "Unknown Mentor"; // Default if missing

    // Display mentor details
    document.getElementById("mentor-details").innerHTML = `<h2>Session with ${mentorName}</h2>`;

    // Ensure chat box scrolls automatically
    const chatBox = document.getElementById("chatMessages");
    chatBox.scrollTop = chatBox.scrollHeight;
});

// Function to send messages in chat
function sendMessage() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();

    if (message) {
        const chatBox = document.getElementById("chatMessages");
        const messageElement = document.createElement("p");

        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        messageElement.innerHTML = `<strong>You:</strong> ${message} <span style="font-size: 0.8em; color: gray;">(${timestamp})</span>`;

        chatBox.appendChild(messageElement);
        input.value = "";
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to latest message
    }
}

// Placeholder function for video calls
function startVideoCall() {
    alert("Video call feature will be implemented later!");
}