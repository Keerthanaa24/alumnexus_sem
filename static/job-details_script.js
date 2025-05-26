document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('job-application-form');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const jobId = document.getElementById('job-id').value;
        
        try {
            const response = await fetch(`/api/job/${jobId}/apply`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Application failed');
            }
            
            showPopup(result.message);
            form.reset(); // Clear the form after successful submission
            
        } catch (error) {
            showPopup(error.message);
            console.error('Application error:', error);
        }
    });
});

function goBack() {
    window.history.back();
}