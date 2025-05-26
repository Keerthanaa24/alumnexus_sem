document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded!");

    let loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            console.log("Login form submitted!");

            let email = document.getElementById("email").value;
            let password = document.getElementById("password").value;

            console.log("Email:", email, "Password:", password);

            try {
                let response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: email, password: password }),
                });

                console.log("Response received!");

                let result = await response.json();
                console.log("Result:", result);

                if (result.success) {
                    window.location.href = result.redirect;
                } else {
                    // Display the specific error message from the server
                    alert(result.message || "Login failed. Please try again.");
                }
            } catch (error) {
                console.error("Error:", error);
                alert("Login failed. Please try again later.");
            }
        });
    }
});