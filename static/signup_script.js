document.addEventListener("DOMContentLoaded", function () {
    let signupForm = document.getElementById("signup-form");

    if (signupForm) {
        signupForm.addEventListener("submit", async function (event) {
            event.preventDefault(); // Prevent default form submission

            let email = document.getElementById("email").value;
            let password = document.getElementById("password").value;
            let confirmPassword = document.getElementById("confirm-password").value;

            if (password !== confirmPassword) {
                alert("Passwords do not match! Please try again.");
                return;
            }

            let formData = new FormData();
            formData.append("email", email);
            formData.append("password", password);

            try {
                let response = await fetch("/signup", {
                    method: "POST",
                    body: formData
                });

                let result = await response.json();

                if (result.success) {
                    alert("Signup successful!! ");
                    window.location.href = result.redirect; // Redirect
                } else {
                    alert(result.message || "Signup failed. Please try again.");
                }
            } catch (error) {
                console.error("Signup error:", error);
                alert("An error occurred. Please try again.");
            }
        });
    }
});
