function sendConnectionRequest(receiverId, receiverName) {
    fetch('/send_connection_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            receiver_id: receiverId,
            receiver_name: receiverName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showConnectionModal();
        } else {
            alert(data.message || 'Failed to send connection request');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while sending the request');
    });
}