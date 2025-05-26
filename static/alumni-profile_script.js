const selectedAlumni = JSON.parse(localStorage.getItem("selectedAlumni"));

if (selectedAlumni) {
    document.getElementById("alumni-image").src = selectedAlumni.image;
    document.getElementById("alumni-name").textContent = selectedAlumni.name;
    document.getElementById("grad-year").textContent = `Class of ${selectedAlumni.gradYear}`;
    document.getElementById("achievements").textContent = selectedAlumni.achievements;
    document.getElementById("industry-impact").textContent = selectedAlumni.industryImpact;
    document.getElementById("testimonial").textContent = `"${selectedAlumni.testimonial}"`;

    const milestonesList = document.getElementById("milestones");
    selectedAlumni.milestones.forEach(milestone => {
        const listItem = document.createElement("li");
        listItem.textContent = milestone;
        milestonesList.appendChild(listItem);
    });
} else {
    window.location.replace("/static/success-stories.html") ;
}