document.addEventListener('DOMContentLoaded', function () {

    // De-duplicate mentors (optional if using dynamic rendering)
    const mentorContainer = document.getElementById('mentorContainer');
    if (mentorContainer) {
        const seenNames = new Set();
        const mentors = mentorContainer.querySelectorAll('.mentor');
        mentors.forEach(mentor => {
            const name = mentor.querySelector('h3')?.textContent.trim();
            if (seenNames.has(name)) {
                mentor.remove();
            } else {
                seenNames.add(name);
            }
        });
    }

    // Add click-to-filter only if using a button (optional)
    const findBtn = document.getElementById('findMentorBtn');
    if (findBtn) {
        findBtn.addEventListener('click', filterMentors);
    }

    // Add click handler for Book Session
    document.querySelectorAll('.book-btn').forEach(button => {
        button.addEventListener('click', function () {
            let mentorName = this.parentElement.querySelector('h3').textContent;
            window.location.replace(`/session-details?mentor=${encodeURIComponent(mentorName)}`);
        });
    });
});

function filterMentors() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    const mentorCards = document.querySelectorAll(".mentor");

    mentorCards.forEach(card => {
        const text = card.innerText.toLowerCase();
        if (text.includes(input)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }
    });
}