// script.js
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("feedbackForm");
    const responseMessage = document.getElementById("responseMessage");
    const stars = document.querySelectorAll(".star");
    let selectedRating = 0;

    // Function to highlight stars up to the selected rating
    function updateStars(rating) {
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add("active");
            } else {
                star.classList.remove("active");
            }
        });
    }

    // Event listener for each star
    stars.forEach((star, index) => {
        star.addEventListener("click", function () {
            selectedRating = index + 1;
            document.getElementById("rating").value = selectedRating;
            updateStars(selectedRating);
        });

        star.addEventListener("mouseover", function () {
            updateStars(index + 1);
        });

        star.addEventListener("mouseout", function () {
            updateStars(selectedRating);
        });
    });

    // Form submission
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        if (selectedRating === 0) {
            responseMessage.style.color = "red";
            responseMessage.innerText = "Please select a rating before submitting!";
            return;
        }

        responseMessage.style.color = "green";
        responseMessage.innerText = "Feedback submitted successfully!";
        form.reset();
        updateStars(0);
        selectedRating = 0;
    });
});
