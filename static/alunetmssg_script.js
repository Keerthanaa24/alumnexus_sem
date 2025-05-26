document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const alumniName = urlParams.get("name");
    const alumniId = urlParams.get("id");
    
    if (!alumniName || !alumniId) {
        console.error("Missing alumni name or ID in URL");
        return;
    }

    // Set the alumni name in the UI
    document.getElementById("alumni-name").textContent = alumniName;
    document.getElementById("alumni-profile-name").textContent = alumniName;

    // Initialize chat
    initChat(alumniId);

    // Function to initialize chat
    async function initChat(recipientId) {
        try {
            // Get current user info
            const response = await fetch('/api/current_user');
            if (!response.ok) throw new Error('Failed to get current user');
            const currentUser = await response.json();

            // Load existing messages
            loadMessages(currentUser.id, recipientId);
            
            // Set up polling for new messages
            setInterval(() => loadMessages(currentUser.id, recipientId), 2000);
            
        } catch (error) {
            console.error('Error initializing chat:', error);
        }
    }

    // Function to load messages
    async function loadMessages(userId, recipientId) {
        try {
            const response = await fetch(`/api/get_messages?other_user_id=${recipientId}`);
            if (!response.ok) throw new Error('Failed to load messages');
            const messages = await response.json();

            const chatMessages = document.getElementById("chatMessages");
            chatMessages.innerHTML = '';
            
            messages.forEach(msg => {
                const messageDiv = document.createElement("div");
                messageDiv.className = `message ${msg.sender_id === userId ? 'sent' : 'received'}`;
                messageDiv.innerHTML = `
                    <p>${msg.content}</p>
                    <span>${new Date(msg.timestamp).toLocaleTimeString()}</span>
                `;
                chatMessages.appendChild(messageDiv);
            });
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    // Function to send message
    async function sendMessage() {
        const input = document.getElementById("messageInput");
        const message = input.value.trim();
        const recipientId = urlParams.get("id");
        
        if (!message || !recipientId) return;
        
        try {
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    receiver_id: recipientId,
                    content: message
                })
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            input.value = '';
            // No need to reload messages here as polling will handle it
            
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    }

    // Event listeners
    document.querySelector(".chat-input button").addEventListener("click", sendMessage);
    document.getElementById("messageInput").addEventListener("keypress", (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

document.addEventListener("DOMContentLoaded", () => {
    fetch('/api/connections')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById("chatList");
            list.innerHTML = "";
            data.forEach(user => {
                const item = document.createElement("li");
                item.className = "chat-item";
                item.onclick = () => updateChat(user);
                item.innerHTML = `
                    <img src="/static/images/pro.png" alt="Alumni">
                    <div class="chat-info">
                        <h4>${user.name}</h4>
                        <p>Last message preview...</p>
                    </div>
                `;
                list.appendChild(item);
            });
        });
});

function updateChat(user) {
    document.getElementById("alumni-name").textContent = user.name;
    document.getElementById("alumni-profile-name").textContent = user.name;
    document.querySelector(".user-profile p:nth-of-type(1)").textContent = user.position || "Unknown Position";
    document.querySelector(".user-profile p:nth-of-type(2)").textContent = user.email;
    document.querySelector(".user-profile p:nth-of-type(3)").textContent = user.phone || "N/A";

    // Optionally: Load messages here if implemented
    // fetchMessages(user.id);
}
