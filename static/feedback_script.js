function submitFeedback() {
    let feedbackText = document.getElementById("feedbackText").value;
    
    if (feedbackText.trim() === "") {
        alert("Please enter your feedback.");
        return;
    }

    // ✅ Show the pop-up
    document.getElementById("popup").style.display = "block";
}

function closePopup() {
    // ✅ Hide the pop-up when clicking "OK"
    document.getElementById("popup").style.display = "none";

    // ✅ Clear feedback text
    document.getElementById("feedbackText").value = "";

    // ✅ Reset star rating
    let stars = document.querySelectorAll(".star");
    stars.forEach(star => star.classList.remove("active"));

    // ✅ Redirect to mentorship.html after a slight delay
    setTimeout(() => {
        window.location.replace("/mentorship");
    }, 500);
}

function rate(starCount) {
    let stars = document.querySelectorAll(".star");

    stars.forEach((star, index) => {
        if (index < starCount) {
            star.classList.add("active"); // Highlight selected stars
        } else {
            star.classList.remove("active");
        }
    });
}