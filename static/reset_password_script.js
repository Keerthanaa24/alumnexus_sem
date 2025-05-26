document.addEventListener("DOMContentLoaded", function () {
    let resetPasswordForm = document.getElementById("resetPasswordForm");

    if (!resetPasswordForm) {
        console.error("Error: Reset Password form not found!");
        return;
    }

    resetPasswordForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Stop page reload

        let formData = new FormData(resetPasswordForm);

        fetch("/reset_password", {
            method: "POST",
            body: formData,
            headers: { "X-Requested-With": "XMLHttpRequest" }  // Tells Flask this is AJAX
        })
        .then(response => response.json())  // Convert response to JSON
        .then(data => {
            if (data.success) {
                // ✅ Show popup before redirecting
                alert("Password reset successfully! Redirecting to login...");

                // 🔄 Redirect to login page after 2 seconds
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 2000);
            } else {
                alert(data.message); // Show error message
            }
        })
        .catch(error => {
            console.error("Fetch error:", error);
            alert("Something went wrong! Please try again.");
        });
    });
});
