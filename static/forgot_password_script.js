document.addEventListener("DOMContentLoaded", function () {
    let resetPasswordForm = document.getElementById("resetPasswordForm");

    if (!resetPasswordForm) {
        console.error("Error: Reset Password form not found!");
        return;
    }

    resetPasswordForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Stop page reload

        let newPassword = document.getElementById("newPassword").value;
        let confirmPassword = document.getElementById("confirmPassword").value;

        if (!newPassword || !confirmPassword) {
            alert("Please fill in all fields.");
            return;
        }

        if (newPassword !== confirmPassword) {
            alert("Passwords do not match. Try again.");
            return;
        }

        fetch("/reset_password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ new_password: newPassword, confirm_password: confirmPassword })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Your password has been reset successfully!");
                window.location.href = data.redirect; // Redirect to login page
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error("Fetch error:", error);
            alert("Something went wrong! Please try again.");
        });
    });
});
